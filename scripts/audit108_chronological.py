#!/usr/bin/env python3
"""Complete media decoding, ordered reading windows and component provenance.

Document body, footer and title are matched separately. A same-rule compilation
is compared pixel-for-pixel against its verified source recordings. These checks
support targeted visual review; they are not continuous human viewing or a model
rule-learning evaluation.
"""
import argparse,concurrent.futures,hashlib,json,sys
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));import workflows as w
cv2.setNumThreads(1)
REGIONS={'full':((40,660,130,1140),(320,198)),'body':((130,599,145,1133),(392,184)),'footer':((602,628,138,1133),(398,10)),'title':((48,74,150,730),(232,11))}

def vector(image,region):
 (y0,y1,x0,x1),size=REGIONS[region];gray=cv2.resize(cv2.cvtColor(image[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY),size).astype(np.float32);value=(gray-cv2.GaussianBlur(gray,(0,0),3)).reshape(-1);norm=np.linalg.norm(value)
 # Flat editor bodies acquire tiny codec edges. Do not amplify that noise
 # into unit vectors; real document glyphs remain well above this floor.
 if region=='body' and norm/np.sqrt(value.size)<.1:return np.zeros_like(value)
 return value/(norm if norm>1e-6 else 1)

def ordered_windows(costs,hold):
 count,n=costs.shape;slots=n-hold+1;assert slots>=count*hold,(count,n,hold)
 windows=np.stack([costs[:,i:i+hold].mean(axis=1) for i in range(slots)],axis=1)
 dp=np.full_like(windows,np.inf);parents=np.full((count,slots),-1,dtype=np.int32);dp[0]=windows[0]
 for k in range(1,count):
  best=np.inf;arg=-1
  for t in range(slots):
   old=t-hold
   if old>=0 and dp[k-1,old]<best:best=float(dp[k-1,old]);arg=old
   if arg>=0:dp[k,t]=best+windows[k,t];parents[k,t]=arg
 selected=[int(np.argmin(dp[-1]))]
 for k in range(count-1,0,-1):selected.append(int(parents[k,selected[-1]]))
 selected.reverse();assert all(i>=0 for i in selected)
 return selected,windows

def region_cost(features,reference):
 if np.linalg.norm(reference)<1e-6:
  return np.where(np.linalg.norm(features,axis=1)<1e-6,0.0,1.0)
 return 1-features@reference

def audit_component(component,destination):
 sid=component['session_id'];session=json.loads((ROOT/'data/episodes'/f'{sid}.json').read_text());ep=session['episode'];assert ep['implementation']['fingerprint']==w.IMPLEMENTATION['fingerprint'];provenance=session['video_provenance']
 assert w.evaluate(ep)['success'] and session['result']['success'] and provenance['replay_verified']
 assert provenance['trace_sha256']==w.digest(session['ui_events']) and provenance['final_state_sha256']==w.digest(ep['state'])
 video=Path(component['video']);assert hashlib.sha256(video.read_bytes()).hexdigest()==component['sha256']
 folder=Path(component['reference_directory']);markers=json.loads((folder/'review-frames.json').read_text());cap=cv2.VideoCapture(str(video));fps=cap.get(cv2.CAP_PROP_FPS);width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));expected=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));assert(width,height,fps)==(1280,720,25.0)
 step=max(1,round(fps/2));features={k:[] for k in REGIONS};times=[];n=0;black=0;longest_black=0
 while True:
  ok,image=cap.read()
  if not ok:break
  black=black+1 if float(image.mean())<3 else 0;longest_black=max(longest_black,black)
  if n%step==0:
   for key in features:features[key].append(vector(image,key))
   times.append(n/fps)
  n+=1
 cap.release();assert abs(n-expected)<=1 and longest_black/fps<2
 features={key:np.stack(value) for key,value in features.items()};costs=[];document=False;modes=[]
 for marker in markers:
  label=marker['label']
  if label.startswith(('document-','page-break-')):document=True
  elif label not in {'job-result','final-saved-result'}:document=False
  image=cv2.imread(str(folder/marker['image']));assert image is not None
  if document:
   cost=sum(weight*region_cost(features[region],vector(image,region)) for region,weight in [('body',.65),('footer',.25),('title',.10)])
  else:cost=region_cost(features['full'],vector(image,'full'))
  costs.append(np.clip(cost,0,2));modes.append(document)
 costs=np.stack(costs);hold=int(np.ceil(1.5/(step/fps)));selected,windows=ordered_windows(costs,hold)
 frames=destination/sid;frames.mkdir(parents=True,exist_ok=True);cap=cv2.VideoCapture(str(video));witnesses=[]
 for i,(marker,start,doc) in enumerate(zip(markers,selected,modes)):
  second=times[start+hold//2];cap.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,image=cap.read();assert ok
  path=frames/f'{i:03}.png';cv2.imwrite(str(path),image);mean=float(windows[i,start]);maximum=float(costs[i,start:start+hold].max());limit=.08 if doc else .16
  witnesses.append({**marker,'video_second':round(second,3),'window_start_seconds':round(times[start],3),'window_seconds':hold*step/fps,'mean_region_cost':round(mean,6),'maximum_region_cost':round(maximum,6),'document_regions':doc,'automatic_match':maximum<=limit,'frame':str(path)})
 cap.release();result={'session_id':sid,'seed':ep['seed'],'case_id':ep['case']['id'],'condition':chr(65+ep['convention']),'sha256':component['sha256'],'decoded_frames':n,'seconds':n/fps,'width':width,'height':height,'fps':fps,'longest_black_seconds':longest_black/fps,'judge_success':True,'replay_verified':True,'source_fingerprint':ep['implementation']['fingerprint'],'reading_views':len(witnesses),'automatic_matches':sum(x['automatic_match'] for x in witnesses),'witnesses':witnesses}
 (destination/(sid+'.json')).write_text(json.dumps(result,indent=2));return result

def verify_compilation(video,components):
 target=cv2.VideoCapture(str(video));count=0
 for component in components:
  source=cv2.VideoCapture(component['video'])
  while True:
   ok,image=source.read()
   if not ok:break
   actual_ok,actual=target.read();assert actual_ok and np.array_equal(image,actual),(video,count)
   count+=1
  source.release()
 assert not target.read()[0];target.release();return count

def audit_plan(plan,output,workers=2):
 output.mkdir(exist_ok=True);frame_root=output/'frames';frame_root.mkdir(exist_ok=True)
 reports=[]
 def audit(row):
  parts=[audit_component(c,frame_root) for c in row['components']]
  joined_frames=verify_compilation(row['video'],row['components']) if len(parts)>1 else parts[0]['decoded_frames']
  assert joined_frames==sum(p['decoded_frames'] for p in parts)
  result={'clip':row['clip'],'sha256':hashlib.sha256(Path(row['video']).read_bytes()).hexdigest(),'source_examples':len(parts),'decoded_frames':joined_frames,'seconds':joined_frames/25,'reading_views':sum(p['reading_views'] for p in parts),'automatic_matches':sum(p['automatic_matches'] for p in parts),'source_components':parts,'all_source_judges_pass':True,'lossless_composition_verified':len(parts)>1,'needs_visual_review':[{'session_id':p['session_id'],'index':i,'label':view['label'],'cost':view['maximum_region_cost']} for p in parts for i,view in enumerate(p['witnesses']) if not view['automatic_match']]}
  (output/(row['clip']+'.json')).write_text(json.dumps(result,indent=2));print(row['clip'],result['reading_views'],len(result['needs_visual_review']),flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  for result in pool.map(audit,plan):
   reports.append(result);(output/'progress.json').write_text(json.dumps({'audited':len(reports),'clips':len(plan),'pending_review_views':sum(len(r['needs_visual_review']) for r in reports)},indent=2))
 return reports

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--workers',type=int,default=2);a=p.parse_args();audit_plan(json.loads(a.plan.read_text()),a.output,a.workers)

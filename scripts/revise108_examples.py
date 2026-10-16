#!/usr/bin/env python3
"""Build one same-rule video from verified existing OS example recordings."""
import argparse,copy,hashlib,json,shutil,subprocess,sys,time
from decimal import Decimal,ROUND_HALF_EVEN
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import workflows as w

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def media(path):
 import cv2
 cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS);frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cap.release()
 assert fps==25 and frames>0
 return frames,fps

def example_coverage(episode):
 source=json.loads(next(f['content'] for f in episode['initial']['files'] if f['name']=='Example input.json'))
 output=next(a['content'] for a in episode['reference'] if a['op']=='write');c=episode['convention'];cid=episode['case']['id']
 if cid=='OS-M-11':
  expected=[]
  for record in source:
   n=record['quantity']
   if c==0:expected.append(f'{n} pcs')
   else:
    divisor=record['box' if c==1 else 'pack'];q,rem=divmod(n,divisor);expected.append(f'{q} '+('box' if c==1 else 'pack')+f' + {rem} pcs')
  expected='\n'.join(expected)
 else:
  n=source['released_bytes']
  if c==0:expected=f'{n} B'
  else:
   value=Decimal(n)/(Decimal(1024)**c);digits=3 if c==1 else 6;rounded=value.quantize(Decimal(10)**-digits,rounding=ROUND_HALF_EVEN)
   expected=f'{rounded:.{digits}f} '+('KiB' if c==1 else 'MiB')
 assert output==expected,(cid,c,source,output,expected)
 return {'case_id':cid,'condition':chr(65+c),'seed':episode['seed'],'input':source,'expected_result':expected,'independent_arithmetic_verified':True}

def validate_example_set(examples):
 assert examples and len({(x['case_id'],x['condition']) for x in examples})==1
 c=ord(examples[0]['condition'])-65
 if examples[0]['case_id']=='OS-M-11':
  records=[row for x in examples for row in x['input']]
  assert len({x['quantity'] for x in records})>=2
  if c:
   remainders={x['quantity']%x['box' if c==1 else 'pack'] for x in records}
   assert 0 in remainders and len(remainders)>=2
   assert len({x['quantity']//x['box' if c==1 else 'pack'] for x in records})>=2
 else:
  assert len({x['input']['released_bytes'] for x in examples})>=3
  if c:
   digits=3 if c==1 else 6;directions=set()
   for x in examples:
    exact=Decimal(x['input']['released_bytes'])/(Decimal(1024)**c);rounded=exact.quantize(Decimal(10)**-digits,rounding=ROUND_HALF_EVEN)
    directions.add((rounded>exact)-(rounded<exact))
   assert {-1,1}.issubset(directions)
 return True

def prepare(root,base_manifest,retained_videos,only=None):
 root.mkdir(exist_ok=True);package=root/'package';(package/'videos').mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/'candidate-manifest.json' if only else base_manifest).read_text());assert manifest['source_fingerprint']==w.IMPLEMENTATION['fingerprint'];manifest=copy.deepcopy(manifest)
 plan=[x for x in json.loads((root/'component-plan.json').read_text()) if x['clip'].rsplit('-',1)[0] not in only] if only else []
 coverage=[x for x in json.loads((root/'example-coverage.json').read_text()) if x['case_id'] not in only] if only else []
 for row in manifest['videos']:
  cid=row['case_id'];c=ord(row['condition'])-65
  if only and cid not in only:continue
  if cid not in {'OS-M-11','OS-H-11'}:
   source=retained_videos/Path(row['video']).name;assert source.is_file() and sha(source)==row['sha256']
   shutil.copy2(source,package/row['video']);row['example_seeds']=[row['seed']]
   folder=ROOT/'data/task36-standard108-recordings'/f'{cid}-{c}-{row["seed"]}'
   plan.append({'clip':cid+'-'+row['condition'],'video':str(package/row['video']),'components':[{'session_id':row['session_id'],'seed':row['seed'],'reference_directory':str(folder),'video':str(source),'sha256':row['sha256']} ]})
   continue
  seeds=[1016] if cid=='OS-M-11' else [1001,33,509];segments=[];components=[];cursor=0
  local_coverage=[]
  for seed in seeds:
   folder=root/'recordings'/f'{cid}-{c}-{seed}';result=json.loads((folder/'result.json').read_text());session=json.loads((ROOT/'data/episodes'/f'{result["session_id"]}.json').read_text());ep=session['episode'];assert session['video_status']=='ready',result['key']
   assert w.evaluate(ep)['success'] and session['result']['success'] and ep['implementation']['fingerprint']==manifest['source_fingerprint']
   provenance=session['video_provenance'];assert provenance['trace_sha256']==w.digest(session['ui_events']) and provenance['final_state_sha256']==w.digest(ep['state']) and provenance['replay_verified']
   source=ROOT/'data/videos'/session['video'];frames,fps=media(source);seconds=frames/fps
   component={'case_id':cid,'condition':row['condition'],'session_id':session['id'],'seed':seed,'sha256':sha(source),'seconds':seconds,'frames':frames,'start_seconds':cursor,'end_seconds':cursor+seconds,'provenance':provenance}
   segments.append(component);components.append({**component,'reference_directory':str(folder),'video':str(source)});cursor+=seconds
   local_coverage.append(example_coverage(ep))
  validate_example_set(local_coverage);coverage.extend(local_coverage)
  temp=package/'videos'/f'{cid}-{c}.webm'
  if len(components)==1:shutil.copy2(components[0]['video'],temp)
  else:
   listing=root/f'concat-{cid}-{c}.txt';listing.write_text(''.join("file '"+x['video'].replace("'","'\\''")+"'\n" for x in components))
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(temp)],check=True)
  digest=sha(temp);name='demo-'+digest[:24]+'.webm';target=temp.with_name(name);temp.replace(target)
  provenance=segments[0]['provenance'] if len(segments)==1 else {'schema_version':2,'source':'browser-interaction-replay-composite','actor':'oracle-assisted-coordinate-ui','implementation_fingerprint':manifest['source_fingerprint'],'composition':'lossless-concat-independent-same-rule-examples','component_count':len(segments),'replay_verified':True,'trace_sha256':w.digest([x['provenance']['trace_sha256'] for x in segments]),'trace_digest_scheme':'ordered-component-trace-hashes','final_state_sha256':w.digest([x['provenance']['final_state_sha256'] for x in segments]),'final_state_digest_scheme':'ordered-component-final-state-hashes'}
  row.update(seed=seeds[0],example_seeds=seeds,session_id=segments[0]['session_id'],video='videos/'+name,download_url=row['download_url'].rsplit('/',1)[0]+'/'+name,sha256=digest,bytes=target.stat().st_size,seconds=cursor,provenance=provenance,audit_passed=False,reading_witnesses=sum(len(json.loads((Path(x['reference_directory'])/'review-frames.json').read_text())) for x in components))
  if len(segments)>1:row['segments']=segments
  plan.append({'clip':cid+'-'+row['condition'],'video':str(target),'components':components})
 manifest['schema_version']=2;manifest.pop('demo_seed',None);manifest['query_seed_constraint']='Exclude every seed in the selected clip example_seeds from query examples.';manifest['examples_per_video']='One or more independent examples of the same rule; one video file per query.'
 (root/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2));(root/'component-plan.json').write_text(json.dumps(plan,indent=2));(root/'example-coverage.json').write_text(json.dumps(coverage,indent=2))
 print('Prepared 108 videos; source examples:',sum(len(x['components']) for x in plan),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT/'data/task36-revision108');p.add_argument('--manifest',type=Path,default=ROOT/'docs/STANDARD108_MANIFEST.json');p.add_argument('--retained-videos',type=Path,default=ROOT/'data/task36-recheck108/videos');p.add_argument('--cases',nargs='+');a=p.parse_args();prepare(a.root,a.manifest,a.retained_videos,a.cases)

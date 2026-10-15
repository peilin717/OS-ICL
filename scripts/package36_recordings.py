#!/usr/bin/env python3
"""Package only current-source successful, replay-verified coordinate demos."""
import argparse,hashlib,html,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import workflows as w
import tasks36


def package(source,destination,seeds):
    destination=destination.resolve()
    if str(destination).lower().startswith('/mnt/c/'):
        raise ValueError('Demo videos must remain in native WSL storage; use '+str(ROOT/'data/demo36'))
    results=[];pending=[]
    for case in tasks36.CASES:
        for convention in range(3):
            for seed in seeds:
                key=f'{case["id"]}-{convention}-{seed}';result_path=source/key/'result.json'
                if not result_path.exists():pending.append({'key':key,'status':'recording-missing'});continue
                result=json.loads(result_path.read_text());session=json.loads((ROOT/'data/episodes'/f'{result["session_id"]}.json').read_text());ep=session['episode']
                if session.get('video_status')!='ready':pending.append({'key':key,'status':session.get('video_status'),'error':session.get('video_error')});continue
                assert ep['implementation']['fingerprint']==w.IMPLEMENTATION['fingerprint'],(key,'stale source')
                assert ep['task36_scope']=='demo' and session['result']['success'] and w.evaluate(ep)['success'],key
                provenance=session['video_provenance'];assert provenance['replay_verified'] and provenance['actor']=='oracle-assisted-coordinate-ui',key
                assert provenance['trace_sha256']==w.digest(session['ui_events']) and provenance['final_state_sha256']==w.digest(ep['state']),key
                original=ROOT/'data/videos'/session['video'];meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height','-show_entries','format=duration,size','-of','json',str(original)],text=True))
                stream=meta['streams'][0];assert (stream['width'],stream['height'])==(1280,720)
                filename=f'{case["id"]}-{chr(65+convention)}-{seed}.webm';target=destination/'videos'/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
                results.append({'case_id':case['id'],'title':case['title'],'difficulty':case['difficulty'],'condition':chr(65+convention),'seed':seed,'video':'videos/'+filename,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'seconds':float(meta['format']['duration']),'bytes':target.stat().st_size,'session_id':session['id'],'provenance':provenance,'visual_review':'pending-whole-timeline-review'})
    destination.mkdir(parents=True,exist_ok=True)
    manifest={'catalogue_version':'36.1-dev','source_fingerprint':w.IMPLEMENTATION['fingerprint'],'scope':'local-method-demos','actor':'oracle-assisted-coordinate-ui','input_method':'screenshots-and-coordinate-mouse-keyboard; no DOM solver; trusted state reads verify inputs','expected':36*3*len(seeds),'ready':len(results),'pending':pending,'videos':results}
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    cards=[]
    for case in tasks36.CASES:
        rows=[r for r in results if r['case_id']==case['id']]
        clips=''.join(f'<figure><video controls preload="none" src="{html.escape(r["video"])}"></video><figcaption>{r["condition"]} · seed {r["seed"]} · {r["seconds"]:.1f}s</figcaption></figure>' for r in rows)
        cards.append(f'<section><h2>{case["id"]} {html.escape(case["title"])}</h2><div class="clips">{clips or "Pending"}</div></section>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>OS ICL 36 task demonstrations</title><style>body{font:16px system-ui;max-width:1500px;margin:32px auto;padding:0 24px;background:#f5f7f8;color:#243744}h1{font-size:30px}h2{font-size:20px}section{background:white;border:1px solid #dce2e7;border-radius:8px;padding:20px;margin:20px 0}.clips{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}figure{margin:0}video{width:100%;background:#dde5e9}figcaption{padding:8px;font-size:14px}</style>'''+f'<h1>OS ICL 36 task demonstrations</h1><p>{len(results)} / {manifest["expected"]} clips. Local methods, not full query solutions. Oracle-assisted coordinate mouse/keyboard interactions, rendered by verified browser replay; not human recordings or independent model evaluation. Whole-timeline visual review remains pending.</p>'+''.join(cards)+'</html>'
    (destination/'index.html').write_text(page)
    print(json.dumps({'ready':len(results),'expected':manifest['expected'],'pending':pending[:10]}))
    return not pending


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--output',type=Path,default=ROOT/'data/demo36',help='Native WSL destination (default: data/demo36)');p.add_argument('--seeds',nargs='+',type=int,default=[1001,1002,1003]);a=p.parse_args();sys.exit(0 if package(a.source,a.output,a.seeds) else 2)

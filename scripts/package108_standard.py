#!/usr/bin/env python3
"""Fail-closed standard108 package: one clip per task/rule, all evidence required."""
import hashlib,html,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'tasks36.py').exists():ROOT=Path('/root/VideoICL-bench/OS-ICL')
sys.path.insert(0,str(ROOT))
import tasks36,workflows as w
TAG='task36-standard108-2026-10-16'
URL='https://github.com/peilin717/OS-ICL/releases/download/'+TAG+'/'


def validate_manifest(manifest):
    expected={(c['id'],r) for c in tasks36.CASES for r in ['A','B','C']}
    actual=[(v['case_id'],v['condition']) for v in manifest['videos']]
    assert manifest['standard']=='one-demo-per-task-condition' and manifest['ready']==manifest['expected']==108
    assert len(actual)==len(set(actual))==108 and set(actual)==expected
    assert len({v['seed'] for v in manifest['videos']})==1
    assert len({v['sha256'] for v in manifest['videos']})==108
    for row in manifest['videos']:
        assert row['audit_passed'] and row['provenance']['replay_verified']
        assert row['download_url'].endswith(Path(row['video']).name)
        assert row['case_id'] not in row['download_url'] and not any('-'+c+'-' in row['download_url'] for c in ['A','B','C'])
    return True


def package():
    source=ROOT/'data/task36-standard108-recordings';auditroot=ROOT/'data/task36-audit108';out=ROOT/'data/task36-standard108';out.mkdir(exist_ok=True)
    author=hashlib.sha256((ROOT/'scripts/record108_coordinates.py').read_bytes()).hexdigest()
    reviewed=json.loads((auditroot/'visual-review.json').read_text());preservation=json.loads((auditroot/'query-preservation.json').read_text())
    assert len(reviewed)==36 and preservation['query_task_conditions_unchanged']==108 and not preservation['query_changes']
    rows=[];audits=[]
    for case in tasks36.CASES:
        review=reviewed[case['id']];assert review['status']=='passed' and review['conditions']==['A','B','C']
        sessions=[]
        for c in range(3):
            path=source/f'{case["id"]}-{c}-1001';r=json.loads((path/'result.json').read_text());s=json.loads((ROOT/'data/episodes'/f'{r["session_id"]}.json').read_text());a=json.loads((path/'video-audit.json').read_text());ep=s['episode'];sessions.append(s['id'])
            assert r['authoring_sha256']==author and ep['implementation']['fingerprint']==w.IMPLEMENTATION['fingerprint']
            assert s['video_status']=='ready' and s['result']['success'] and w.evaluate(ep)['success'] and ep['task36_scope']=='demo'
            assert a['passed'] and a['session_id']==s['id'] and a['reading_witnesses']==a['witnesses_passed']
            provenance=s['video_provenance'];assert provenance['replay_verified'] and provenance['trace_sha256']==w.digest(s['ui_events']) and provenance['final_state_sha256']==w.digest(ep['state'])
            video=ROOT/'data/videos'/s['video'];digest=hashlib.sha256(video.read_bytes()).hexdigest();assert digest==a['video_sha256']
            name='demo-'+digest[:24]+'.webm';target=out/'videos'/name;target.parent.mkdir(exist_ok=True);shutil.copy2(video,target)
            rows.append({'case_id':case['id'],'title':case['title'],'difficulty':case['difficulty'],'condition':chr(65+c),'seed':1001,'session_id':s['id'],'video':'videos/'+name,'download_url':URL+name,'sha256':digest,'bytes':video.stat().st_size,'seconds':a['seconds'],'audit_passed':True,'reading_witnesses':a['reading_witnesses'],'minimum_verified_view_seconds':min(x['continuous_match_seconds'] for x in a['witnesses']),'provenance':provenance,'authoring_sha256':author})
            audits.append(a)
        assert sessions==review['session_ids'],case['id']
    manifest={'schema_version':1,'standard':'one-demo-per-task-condition','catalogue_version':'36.1-dev','source_fingerprint':w.IMPLEMENTATION['fingerprint'],'expected':108,'ready':108,'demo_seed':1001,'query_seed_constraint':'Use independent query examples; exclude demo seed 1001.','scope':'local-method demonstration inputs','actor':'oracle-assisted-coordinate-ui','visual_review_scope':'assistant review of input and A/B/C rule-specific checkpoint frames for all tasks, with automatic coverage checks on every authored reading view; not continuous human viewing','videos':rows}
    validate_manifest(manifest)
    findings=[
        {'id':'D01','scope':'all task families','problem':'Replay compressed real reading pauses; blank result setup could dominate short text clips.','fix':'Preserve bounded recorded reading pauses; explicitly re-open saved results and hold observable input/action/result views.','status':'fixed'},
        {'id':'D02','scope':'long JSON, logs and proof reports','problem':'Only a partial page was shown, leaving some input fields and output parameters unread.','fix':'Compact example input formatting, overlapping document paging, and parameter-focused proof views.','status':'fixed'},
        {'id':'D03','scope':'OS-E-08','problem':'The business anchor time was absent from the visible demonstration.','fix':'Show a rule-independent work order with channel anchors before the interval controls and exported results.','status':'fixed'},
        {'id':'D04','scope':'OS-M-12','problem':'Timestamp ties were not demonstrated.','fix':'Show main-newer, review-newer and equal-time conflicts plus both unique fields in one clip.','status':'fixed'},
        {'id':'D05','scope':'OS-M-09','problem':'The recovery destination layout was not demonstrated.','fix':'Include inventory, backup and restore as the local organization example; keep full query comparison/verification separate.','status':'fixed'},
        {'id':'D06','scope':'OS-E-05, OS-E-07, OS-E-11','problem':'High-value out-of-scope objects were missing from the local examples.','fix':'Add protected process/device/print-packet controls and show before/after scope views.','status':'fixed'},
        {'id':'D07','scope':'OS-M-04, OS-H-12','problem':'Within-category ordering and revision/title transfer lacked varied witnesses.','fix':'Use multiple resources in the same category and two revision/title examples in the same video.','status':'fixed'},
        {'id':'D08','scope':'OS-E-12','problem':'A bulk text replacement hid the page-break operation.','fix':'Use the existing Go-to-line and Insert-page-break controls, save and show the footer boundary.','status':'fixed'},
        {'id':'D09','scope':'runner integration','problem':'The exporter required three seed videos; labeled asset URLs could expose rule conditions.','fix':'One matching video per current query; opaque video asset names and trusted manifest selection.','status':'fixed'}]
    report={'standard':manifest['standard'],'clips':108,'tasks':36,'conditions_per_task':3,'videos_per_condition':1,'source_fingerprint':manifest['source_fingerprint'],'baseline':json.loads((auditroot/'baseline-media-audit.json').read_text()),'findings':findings,'query_and_engine_preservation':preservation,'reviewed_task_families':reviewed,'full_frame_decoding':{'clips':108,'decoded_frames':sum(a['decoded_frames'] for a in audits)},'reading_view_coverage':{'authored_views':sum(a['reading_witnesses'] for a in audits),'matched_views':sum(a['witnesses_passed'] for a in audits),'criteria':'codec-normalized application-region visual matching at about 2 samples/sec; continuous matching >=1.5 seconds, independently backed by state judges and replay hashes'},'limits':['No independent model evaluation is claimed.','Assistant keyframe review and automatic timeline checks are not continuous human viewing.','Finite demonstrations cannot prove a unique rule among arbitrary unbounded hypotheses.'],'videos':audits}
    (out/'standard108-manifest.json').write_text(json.dumps(manifest,indent=2));(out/'demo108-audit.json').write_text(json.dumps(report,indent=2))
    shutil.copytree(auditroot/'sheets',out/'review-sheets',dirs_exist_ok=True)
    cards=[]
    for case in tasks36.CASES:
        videos=[r for r in rows if r['case_id']==case['id']]
        clips=''.join(f'<figure><video controls preload="none" src="{html.escape(r["video"])}"></video><figcaption>{r["condition"]} · {r["seconds"]:.1f}s</figcaption><a href="{html.escape(r["download_url"])}">Download</a></figure>' for r in videos)
        cards.append(f'<section><h2>{case["id"]} {html.escape(case["title"])}</h2><div class="clips">{clips}</div><details><summary>Input and rule checkpoint evidence</summary><img loading="lazy" src="review-sheets/{case["id"]}.png" style="max-width:100%"></details></section>')
    page='<!doctype html><meta charset="utf-8"><title>OS-ICL standard 108 demos</title><style>body{font:16px system-ui;max-width:1400px;margin:30px auto;padding:20px;background:#f5f7f8}section{background:white;padding:20px;margin:20px 0}.clips{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}figure{margin:0}video{width:100%}</style><h1>Standard 108 method demonstrations</h1><p>36 tasks × 3 rule conditions × one video. For each query supply one matching video, not all three conditions. The seed is fixture provenance, not an extra input-video count. These are oracle-assisted coordinate UI recordings, with state/replay/decoding/reading-view checks and assistant keyframe review.</p>'+''.join(cards)
    (out/'index.html').write_text(page)
    shutil.copy2(out/'standard108-manifest.json',ROOT/'docs/STANDARD108_MANIFEST.json')
    compact={k:v for k,v in report.items() if k!='videos'};(ROOT/'docs/DEMO108_AUDIT.json').write_text(json.dumps(compact,indent=2))
    print(json.dumps({'ready':108,'reading_views':report['reading_view_coverage'],'directory':str(out)},indent=2))
if __name__=='__main__':package()

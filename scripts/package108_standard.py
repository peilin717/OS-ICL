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
    for case in tasks36.CASES:
        group=[v for v in manifest['videos'] if v['case_id']==case['id']]
        assert len({tuple(v.get('example_seeds',[v['seed']])) for v in group})==1
    for row in manifest['videos']:
        seeds=row.get('example_seeds',[row['seed']])
        assert seeds and len(set(seeds))==len(seeds) and row['seed']==seeds[0]
        if row.get('segments'):
            assert [s['seed'] for s in row['segments']]==seeds
            assert all(s['case_id']==row['case_id'] and s['condition']==row['condition'] and s['provenance']['replay_verified'] for s in row['segments'])
    assert len({v['sha256'] for v in manifest['videos']})==108
    for row in manifest['videos']:
        assert row['audit_passed'] and row['provenance']['replay_verified']
        assert row['download_url'].endswith(Path(row['video']).name)
        assert row['case_id'] not in row['download_url'] and not any('-'+c+'-' in row['download_url'] for c in ['A','B','C'])
    return True



def package(root=None):
    root=Path(root) if root else ROOT/'data/task36-revision108'
    out=root/'package';manifest=json.loads((root/'candidate-manifest.json').read_text())
    plan=json.loads((root/'component-plan.json').read_text());reviewed=json.loads((root/'visual-review.json').read_text())
    resolutions=json.loads((root/'manual-resolution.json').read_text())
    timestamps=json.loads((root/'media-timestamps.json').read_text());assert timestamps['clips']==108 and timestamps['all_passed']
    assert len(reviewed)==36
    author=hashlib.sha256((ROOT/'scripts/record108_coordinates.py').read_bytes()).hexdigest()
    audits=[]
    by_clip={item['clip']:item for item in plan};assert len(by_clip)==len(plan)==108
    for row in manifest['videos']:
        clip=row['case_id']+'-'+row['condition'];item=by_clip[clip]
        timing=next(x for x in timestamps['videos'] if x['clip']==clip);assert timing['passed'] and timing['sha256']==row['sha256']
        a=json.loads((root/'audit'/f'{clip}.json').read_text());assert a['sha256']==row['sha256']
        assert hashlib.sha256((out/row['video']).read_bytes()).hexdigest()==row['sha256']
        review=reviewed[row['case_id']];assert review['status']=='passed'
        assert hashlib.sha256((root/'review-sheets'/f'{row["case_id"]}.png').read_bytes()).hexdigest()==review['sheet_sha256']
        approved=next(x for x in review['videos'] if x['condition']==row['condition'])
        assert approved['sha256']==row['sha256'] and approved['session_ids']==[c['session_id'] for c in item['components']]
        for f in a['needs_visual_review']:
            resolution=resolutions[f['session_id']+':'+str(f['index'])]
            assert resolution['status']=='passed' and resolution['clip_sha256']==row['sha256']
            witness=next(c for c in a['source_components'] if c['session_id']==f['session_id'])['witnesses'][f['index']]
            assert hashlib.sha256((ROOT/witness['frame']).read_bytes()).hexdigest()==resolution['frame_sha256']
        for c in a['source_components']:
            assert c['judge_success'] and c['replay_verified'] and c['source_fingerprint']==manifest['source_fingerprint']
            assert c['case_id']==row['case_id'] and c['condition']==row['condition'] and c['seed'] in row['example_seeds']
            views=c['witnesses'];assert all(x['window_seconds']>=1.5 for x in views)
            assert all(x['window_start_seconds']+x['window_seconds']<=y['window_start_seconds']+.001 for x,y in zip(views,views[1:]))
        for component in item['components']:
            result=json.loads((Path(component['reference_directory'])/'result.json').read_text())
            assert result['session_id']==component['session_id'] and result['authoring_sha256']==author
        assert a['source_examples']==len(item['components']) and a['all_source_judges_pass']
        if len(item['components'])>1:assert a['lossless_composition_verified']
        row.update(audit_passed=True,reading_witnesses=a['reading_views'],minimum_verified_view_seconds=min(v['window_seconds'] for c in a['source_components'] for v in c['witnesses']),seconds=a['seconds'])
        audits.append(a)
    assert manifest['source_fingerprint']==w.IMPLEMENTATION['fingerprint'];validate_manifest(manifest)
    # Remove only orphan candidate files, confined to this package's video directory.
    names={Path(x['video']).name for x in manifest['videos']};directory=(out/'videos').resolve()
    for path in directory.glob('*.webm'):
        assert path.resolve().parent==directory
        if path.name not in names:path.unlink()
    assert len(list(directory.glob('*.webm')))==108
    report={'standard':manifest['standard'],'clips':108,'tasks':36,'conditions_per_task':3,'videos_per_condition':1,'source_examples':sum(a['source_examples'] for a in audits),'source_fingerprint':manifest['source_fingerprint'],'reviewed_task_families':reviewed,'full_frame_decoding':{'clips':108,'decoded_frames':sum(a['decoded_frames'] for a in audits),'seconds':sum(a['seconds'] for a in audits)},'reading_view_coverage':{'authored_views':sum(a['reading_views'] for a in audits),'automatic_matches':sum(a['automatic_matches'] for a in audits),'manually_resolved_views':sum(len(a['needs_visual_review']) for a in audits),'criteria':'Chronological, nonoverlapping >=1.5-second sampled application-region windows; document body, title and footer checked separately; flagged views manually compared with reference screenshots.'},'manual_resolutions':resolutions,'example_coverage':json.loads((root/'example-coverage.json').read_text()),'limits':['No independent model evaluation or full-query browser acceptance is claimed.','Assistant keyframe review and automatic timeline checks are not continuous human viewing.','E05/E11 use finite shared numeric domains; these demos do not establish numeric extrapolation.','Finite demonstrations cannot prove a unique rule among arbitrary unbounded hypotheses.'],'videos':audits}
    report['media_timestamps']=timestamps
    report['audit_tool_sha256']={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in ['audit108_chronological.py','audit108_timestamps.py','package108_standard.py','record108_coordinates.py']}
    (out/'standard108-manifest.json').write_text(json.dumps(manifest,indent=2));(out/'demo108-audit.json').write_text(json.dumps(report,indent=2))
    shutil.copytree(root/'review-sheets',out/'review-sheets',dirs_exist_ok=True)
    cards=[]
    for case in tasks36.CASES:
        clips=''.join(f'<figure><video controls preload="none" src="{html.escape(v["video"])}"></video><figcaption>{v["condition"]}: {v["seconds"]:.1f}s / {len(v["example_seeds"])} same-rule example(s)</figcaption></figure>' for v in manifest['videos'] if v['case_id']==case['id'])
        cards.append(f'<section><h2>{case["id"]} {html.escape(case["title"])}</h2><div class="clips">{clips}</div><details><summary>Input and rule checkpoints</summary><img src="review-sheets/{case["id"]}.png" loading="lazy" style="max-width:100%"></details></section>')
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>OS-ICL 108 demonstrations</title><style>body{font:16px system-ui;margin:30px}.clips{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}video{width:100%}section{margin:30px 0}figure{margin:0}</style><h1>36 tasks / 108 demonstration videos</h1><p>Each inference receives one matching video. A/B/C are alternative rules. H11 videos contain three independently recorded examples of the same rule, joined losslessly. Authors use oracle-assisted coordinate UI interaction. Visual review covers keyframes, with automatic full decoding and chronological reading-view checks.</p>'+''.join(cards))
    shutil.copy2(out/'standard108-manifest.json',ROOT/'docs/STANDARD108_MANIFEST.json')
    (ROOT/'docs/DEMO108_AUDIT.json').write_text(json.dumps({k:v for k,v in report.items() if k!='videos'},indent=2))
    print(json.dumps({'ready':108,'frames':report['full_frame_decoding'],'views':report['reading_view_coverage']},indent=2))

if __name__=='__main__':package(sys.argv[1] if len(sys.argv)>1 else None)

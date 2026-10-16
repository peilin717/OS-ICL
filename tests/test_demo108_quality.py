import copy,importlib.util,json
from pathlib import Path
import pytest
import workflows as w
import tasks36

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('export108',ROOT/'scripts/export_v2_episode.py');export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)


def solve(ep):
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success'];return ep


@pytest.mark.parametrize('c',[0,1,2])
def test_demo_scope_controls_and_threshold_boundaries(c):
    ep=solve(w.generate('OS-E-05',c,1001,'module-demo'))
    assert next(p for p in ep['state']['processes'] if p['id']=='scope-control')['status']=='Running'
    workers=[p for p in ep['state']['processes'] if p['name'].startswith('Background worker ')]
    assert all((p['status']=='Paused')==(p['memory']>=[128,256,384][c]) for p in workers)
    ep=solve(w.generate('OS-E-11',c,1001,'module-demo'))
    assert next(q for q in ep['state']['print_queue'] if q['id']=='scope-control-queue')['status']=='Queued'
    for q in ep['state']['print_queue']:
        if q['name'].startswith('Packet '):assert (q['status']=='Paused')==(len(q['pages'])>[4,6,8][c])


def test_merge_demo_covers_two_directions_ties_and_unique_fields():
    ep=solve(w.generate('OS-M-12',2,1001,'module-demo'))
    inp=json.loads(next(f['content'] for f in ep['initial']['files'] if f['name']=='Example input.json'))
    out=json.loads(next(f['content'] for f in ep['state']['files'] if f['name']=='Example result.txt'))
    assert inp['times']['main']['x']>inp['times']['review']['x'] and out['x']==10
    assert inp['times']['main']['y']<inp['times']['review']['y'] and out['y']==21
    assert inp['times']['main']['z']==inp['times']['review']['z'] and out['z']==30
    assert out['main_only']==out['review_only']=='retain'


@pytest.mark.parametrize('c',[0,1,2])
def test_rollback_demo_includes_restore_layout(c):
    ep=solve(w.generate('OS-M-09',c,1001,'module-demo'))
    assert [j['kind'] for j in ep['state']['jobs']]==['inventory','backup','restore']
    restored=next(j for j in ep['state']['jobs'] if j['kind']=='restore')
    assert w.path(ep['state'],restored['output']).endswith('/Restore' if c==0 else '/Recovery')


def test_public_demo_context_is_rule_independent_and_contains_log_anchors():
    for case in tasks36.CASES:
        episodes=[w.generate(case['id'],c,1001,'module-demo') for c in range(3)]
        notes=[next(f['content'] for f in e['initial']['files'] if f['id']=='demo-context') for e in episodes]
        assert notes[0]==notes[1]==notes[2],case['id']
    ep=w.generate('OS-E-08',0,1001,'module-demo')
    note=next(f['content'] for f in ep['initial']['files'] if f['id']=='demo-context')
    assert 'Channel 0:' in note and 'Channel 1:' in note and '2026-10-15T' in note


def test_current_query_uses_one_remote_demo_and_hides_condition():
    ep=w.generate('OS-E-01',1,4201);session={'id':'osl_query','mode':'evaluation','episode':ep}
    demo={'seed':1001,'case_id':'OS-E-01','convention':1,'video':'opaque.webm','video_url':'https://github.com/peilin717/OS-ICL/releases/download/standard108/demo-opaque.webm','sha256':'a'*64}
    launch,trusted=export.build_export(session,[demo],'http://localhost:8790')
    assert len(launch['demonstrations'])==1 and launch['demonstrations'][0]['video_url']==demo['video_url']
    assert not any(k in json.dumps(launch) for k in ['convention','recorder_brief','_judge36','reference'])
    with pytest.raises(ValueError):export.build_export(session,[],'http://localhost:8790')
    with pytest.raises(ValueError):export.build_export(session,[{**demo,'seed':4201}],'http://localhost:8790')
    with pytest.raises(ValueError):export.build_export(session,[{**demo,'convention':0}],'http://localhost:8790')

import copy,importlib.util,json
from pathlib import Path
import pytest
import tasks36,workflows as w
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pack=module('package108_standard');export=module('export_v2_episode')


def manifest():
    rows=[]
    for case in tasks36.CASES:
        for c in ['A','B','C']:
            token=f'{len(rows)+1:064x}';rows.append({'case_id':case['id'],'condition':c,'seed':1001,'sha256':token,'video':'videos/demo-'+token[:24]+str(len(rows))+'.webm','download_url':'https://github.com/peilin717/OS-ICL/releases/download/standard/demo-'+token[:24]+str(len(rows))+'.webm','audit_passed':True,'provenance':{'replay_verified':True,'actor':'oracle-assisted-coordinate-ui'},'session_id':'osl_'+token})
    return {'standard':'one-demo-per-task-condition','ready':108,'expected':108,'source_fingerprint':w.IMPLEMENTATION['fingerprint'],'videos':rows}


def test_standard_manifest_requires_exact_quota_and_opaque_agent_urls(tmp_path):
    m=manifest();assert pack.validate_manifest(m)
    for transform in [lambda x:x['videos'].pop(),lambda x:x['videos'].append(copy.deepcopy(x['videos'][0])),lambda x:x['videos'][0].update(seed=1002),lambda x:x['videos'][0].update(download_url='https://example.test/OS-E-01-A-demo.webm')]:
        broken=copy.deepcopy(m);transform(broken)
        with pytest.raises(AssertionError):pack.validate_manifest(broken)
    p=tmp_path/'manifest.json';p.write_text(json.dumps(m));ep=w.generate('OS-M-12',1,4201)
    demos=export.manifest_demos(ep,p);assert len(demos)==1 and demos[0]['convention']==1
    launch,_=export.build_export({'id':'osl_query','mode':'evaluation','episode':ep},demos,'http://localhost:8790')
    assert len(launch['demonstrations'])==1 and 'OS-M-12' not in launch['demonstrations'][0]['video_url']
    m['videos'].pop();p.write_text(json.dumps(m))
    with pytest.raises(ValueError):export.manifest_demos(ep,p)


@pytest.mark.parametrize('c',[0,1,2])
def test_approved_selection_demo_uses_independently_derived_metadata(c):
    ep=w.generate('OS-E-03',c,1001,'module-demo')
    for a in ep['reference']:w.transition(ep,a)
    originals=[f for f in ep['initial']['files'] if f.get('approved') is True]
    for parent in {f['parent'] for f in originals}:
        candidates=[f for f in originals if f['parent']==parent]
        chosen=max(candidates,key=lambda f:f['revision']) if c==0 else min(candidates,key=lambda f:len(f['content'].encode())) if c==1 else max(candidates,key=lambda f:len(f['content'].encode()))
        selected=next(f for f in ep['state']['files'] if f['kind']=='folder' and f['parent']==parent and f['name']=='Selected')
        copies=[f for f in ep['state']['files'] if f['parent']==selected['id'] and not f.get('deleted')]
        assert len(copies)==1 and copies[0]['name']==chosen['name'] and copies[0]['content']==chosen['content']

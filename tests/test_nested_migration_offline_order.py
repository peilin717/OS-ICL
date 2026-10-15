import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_nested_input_manifest_resolves_real_sources_and_migration_rewrites_them():
    paths=set()
    for seed in [1001,1002,1003,1004]:
        ep=w._generate_fixture('OS-LH-07',1,seed)
        original=json.loads(w.get_file(ep['initial'],'source-0')['content'])
        available={w.path(ep['initial'],f['id']) for f in ep['initial']['files']}
        assert all(link in available for link in [original['entry'],*original['references']])
        assert '/Profiles/' in w.path(ep['initial'],'source-2')
        paths.add(original['entry'])
        for action in ep['reference']:w.transition(ep,action)
        assert w.evaluate(ep)['success'],w.evaluate(ep)
        assert w.evaluate(ep)['checks']['workspace_probe_passed']
    assert len(paths)>1


def test_offline_reference_builds_cache_before_disconnection_and_tests_after_it():
    for seed in [1001,1002,1003]:
        ep=w._generate_fixture('OS-LH-06',1,seed)
        cache_built=False;disconnected=False
        for action in ep['reference']:
            if action['op']=='setting' and action['key']=='network.offline' and action['value']:
                assert cache_built
                disconnected=True
            if action['op']=='probe' and action['kind']=='offline':assert disconnected
            event=w.transition(ep,action)
            if action['op']=='run-job' and isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Completed':
                job=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
                if job['kind']=='cache':cache_built=True
        assert cache_built and disconnected and w.evaluate(ep)['success']

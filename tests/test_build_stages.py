import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_build_has_passing_independent_test_artifact():
    ep=w._generate_fixture('OS-LH-08',0,1002)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success'],[(j['kind'],j['status'],j['error']) for j in ep['state']['jobs']]
    test=next(j for j in ep['state']['jobs'] if j['kind']=='test')
    details=w.get_file(ep['state'],test['artifact'])['provenance']['processing']
    result=json.loads(w.get_file(ep['state'],details['test_file'])['content'])
    assert result['passed'] and all(a['passed'] for a in result['assertions'])
    assert result['build_sha256']==w.digest(w.get_file(ep['state'],result['build_artifact'])['content'])
    w.transition(ep,{'op':'write','target':details['test_file'],'content':'{}'})
    assert not w.evaluate(ep)['checks']['build_tests_passed']
    package=next(j for j in ep['state']['jobs'] if j['kind']=='package')
    assert 'Build release gate failed' in w.job_error(ep['state'],package,ep['case'])


def test_build_recovery_varies_lock_owner_file_and_failed_test_assertion():
    observed=set()
    for seed in [1000,1001,1003,1004]:
        ep=w._generate_fixture('OS-LH-08',1,seed)
        owner=next(p for p in ep['initial']['processes'] if p['id']=='build-owner')
        observed.add((owner['name'],owner['locks'][0]))
        failures=[]
        for action in ep['reference']:
            event=w.transition(ep,action)
            if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed':failures.append(event['outcome']['error'])
        assert any('Build configuration error' in error for error in failures)
        assert any('Test assertion failed' in error for error in failures)
        assert w.evaluate(ep)['success'],w.evaluate(ep)
        w.transition(ep,{'op':'process','target':owner['id'],'status':'Paused'})
        assert not w.evaluate(ep)['checks']['owner_restored']
    assert len(observed)>=2

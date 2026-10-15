import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_release_missing_components_fail_at_their_own_stage_and_are_repaired():
    for seed,stage,message,key in [(1003,'build','Compiler component','tools.compiler'),(1001,'sign','Signing provider','tools.signer')]:
        ep=w._generate_fixture('OS-LH-02',1,seed)
        assert not ep['initial']['settings'][key]
        observed=[]
        for action in ep['reference']:
            before=len(ep['state']['files'])
            event=w.transition(ep,action)
            if isinstance(event['outcome'],dict) and message in event['outcome'].get('error',''):
                job=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
                assert job['kind']==stage and len(ep['state']['files'])==before
                observed.append(event)
        assert len(observed)==1 and ep['state']['settings'][key]
        assert w.evaluate(ep)['success'],w.evaluate(ep)


def test_enabling_wrong_component_does_not_fix_missing_signing_provider():
    ep=w._generate_fixture('OS-LH-02',0,1001)
    for action in ep['reference']:
        if action['op']=='setting' and action['key']=='tools.signer':break
        w.transition(ep,action)
    failed=next(j for j in ep['state']['jobs'] if j['kind']=='sign')
    w.transition(ep,{'op':'setting','key':'tools.compiler','value':True})
    result=w.transition(ep,{'op':'run-job','target':failed['id']})
    assert result['outcome']['status']=='Failed' and 'Signing provider' in result['outcome']['error']

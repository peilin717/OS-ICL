import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_distribution_repairs_access_checks_payload_and_schedules_without_dispatch():
    ep=w._generate_fixture('OS-LH-10',1,1001)
    failures=[]
    for action in ep['reference']:
        before=len(ep['state']['files'])
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed':
            assert event['outcome']['error'].startswith('Destination access denied:')
            assert len(ep['state']['files'])==before
            failures.append(event)
    assert len(failures)==1 and w.evaluate(ep)['success']
    assert w.evaluate(ep)['checks']['distribution_dry_run_valid']
    delivery=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    assert delivery['status']=='Scheduled'
    details=w.get_file(ep['state'],delivery['artifact'])['provenance']['processing']
    assert details['recipient']==ep['initial']['distribution_request']['recipient']
    assert details['dispatched'] is False
    w.transition(ep,{'op':'device-access','target':'destination','access':'read-only'})
    assert not w.evaluate(ep)['success']


def test_switching_destination_or_editing_payload_invalidates_dry_run_for_staging():
    ep=w._generate_fixture('OS-LH-10',0,1002)
    for action in ep['reference']:
        if action['op']=='run-job':
            task=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
            if task['kind']=='replicate':
                w.transition(ep,{'op':'setting','key':'distribution.destination','value':'other-share'})
                assert 'differs from the dry-run receipt' in w.job_error(ep['state'],task,ep['case'])
                w.transition(ep,{'op':'setting','key':'distribution.destination','value':'destination'})
                document=next(f for f in ep['state']['files'] if f['parent']==task['input'] and f.get('source')=='source-1')
                w.transition(ep,{'op':'write','target':document['id'],'content':document['content']+'Changed after dry run\n'})
                assert 'differs from the dry-run receipt' in w.job_error(ep['state'],task,ep['case'])
                return
        w.transition(ep,action)
    assert False,'Staging operation was not reached'


def test_recipient_and_destination_names_vary_without_changing_context_rules():
    targets=set()
    for seed in range(1000,1008):
        ep=w._generate_fixture('OS-LH-10',0,seed)
        targets.add((ep['initial']['distribution_request']['recipient'],ep['initial']['distribution_request']['destination']))
    assert len(targets)==3

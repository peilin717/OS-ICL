import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_privacy_scope_failure_is_repaired_and_real_redacted_copies_are_delivered():
    ep=w._generate_fixture('OS-LH-09',1,1001)
    diagnosed=False
    for action in ep['reference']:
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('error','').startswith('Personal fields remain:'):
            diagnosed=True
            assert any(field in event['outcome']['error'] for field in ep['initial']['sensitive_fields'] if field!='contact')
    assert diagnosed and w.evaluate(ep)['success']
    assert w.evaluate(ep)['checks']['evidence_fields_preserved']
    assert w.evaluate(ep)['checks']['redacted_copies_intact']
    redaction=next(j for j in ep['state']['jobs'] if j['kind']=='redact')
    details=w.get_file(ep['state'],redaction['artifact'])['provenance']['processing']
    copies=[w.get_file(ep['state'],identifier) for identifier in details['redacted_files']]
    assert len(copies)==2
    for copy in copies:
        for record in map(json.loads,copy['content'].splitlines()):
            assert all(field not in record for field in ep['initial']['sensitive_fields'])
            assert record['event_id'].startswith('EV-') and record['time'] and record['message']
    assert w.get_file(ep['state'],'source-0')['content']==w.get_file(ep['initial'],'source-0')['content']
    w.transition(ep,{'op':'write','target':copies[0]['id'],'content':'{}'})
    assert not w.evaluate(ep)['checks']['redacted_copies_intact']
    package=next(j for j in ep['state']['jobs'] if j['kind']=='package')
    assert 'changed' in w.job_error(ep['state'],package,ep['case'])


def test_recovery_seeds_vary_sensitive_fields_and_healthy_contact_only_is_valid():
    fields=set()
    for seed in range(1000,1012):
        ep=w._generate_fixture('OS-LH-09',0,seed)
        fields.update(ep['initial']['sensitive_fields'])
        for action in ep['reference']:w.transition(ep,action)
        assert w.evaluate(ep)['success']
        if ep['scenario']==0:assert ep['state']['settings']['privacy.scope']=='contact'
    assert fields=={'contact','phone','account_id','ip_address'}

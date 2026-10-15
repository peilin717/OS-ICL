import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_omission_is_detected_and_setting_alone_does_not_repair_recovery_bytes():
    ep=w.generate('OS-LH-03',1,1001)
    diagnosed=False
    for action in ep['reference']:
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('error','').startswith('Recovery scope incomplete:'):
            assert 'notes.txt' in event['outcome']['error']
            diagnosed=True
            restore=next(j for j in ep['state']['jobs'] if j['kind']=='restore')
            assert not any(f['parent']==restore['output'] and f.get('source')=='source-2' and not f['deleted'] for f in ep['state']['files'])
            w.transition(ep,{'op':'setting','key':'backup.include-text','value':True})
            assert w.transition(ep,action)['outcome']['status']=='Failed'
    assert diagnosed and w.evaluate(ep)['success'],w.evaluate(ep)
    snapshots=[json.loads(w.get_file(ep['state'],h['file'])['content']) for h in ep['state']['backup_history']]
    assert len(snapshots)==2 and [len(s['resources']) for s in snapshots]==[3,4]
    assert not any(r['source']=='source-2' for r in snapshots[0]['resources'])
    assert any(r['source']=='source-2' for r in snapshots[1]['resources'])


def test_all_input_and_copied_source_scopes_have_different_real_membership():
    for convention,expected_count in [(0,5),(1,4),(2,5)]:
        ep=w.generate('OS-LH-03',convention,1002)
        for action in ep['reference']:w.transition(ep,action)
        assert w.evaluate(ep)['success']
        backup=next(j for j in ep['state']['jobs'] if j['kind']=='backup')
        report=w.get_file(ep['state'],backup['artifact'])['provenance']
        assert len(report['resources'])==expected_count
        assert len(json.loads(w.get_file(ep['state'],report['processing']['snapshot_file'])['content'])['resources'])==expected_count
        assert len(ep['state']['backup_history'])==1

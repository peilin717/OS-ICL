import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_interval_export_creates_traceable_working_log_and_preserves_original():
    ep=w._generate_fixture('OS-LH-09',0,1001)
    original=w.get_file(ep['initial'],'source-0')['content']
    action={'op':'export-log','target':'source-0','parent':'documents','name':'incident.log',**ep['initial']['incident']}
    result=w.transition(ep,action)
    assert result['accepted']
    exported=w.get_file(ep['state'],result['outcome'])
    records=[json.loads(line) for line in exported['content'].splitlines()]
    assert len(records)==2 and all(action['start']<=r['time']<=action['end'] for r in records)
    assert exported['source_hash']==w.digest(original)
    assert w.get_file(ep['state'],'source-0')['content']==original
    assert ep['state']['log_exports'][0]['event_ids']==[r['event_id'] for r in records]


def test_invalid_or_empty_export_does_not_create_partial_file_or_receipt():
    for start,end in [('bad','also bad'),('2026-01-01T00:00:00','2026-01-01T00:01:00'),('2026-10-15T00:00:00','2026-10-14T00:00:00')]:
        ep=w._generate_fixture('OS-LH-09',0,1001)
        before=copy.deepcopy(ep['state']['files'])
        result=w.transition(ep,{'op':'export-log','target':'source-0','parent':'documents','name':'invalid.log','start':start,'end':end})
        assert not result['accepted']
        assert ep['state']['files']==before and ep['state']['log_exports']==[]


def test_final_evidence_requires_both_log_export_receipts():
    ep=w._generate_fixture('OS-LH-09',1,1001)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success']
    assert w.evaluate(ep)['checks']['incident_logs_exported']
    ep['state']['log_exports'].pop()
    assert not w.evaluate(ep)['checks']['incident_logs_exported']

import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def create_backup(retention):
    ep=w._generate_fixture('OS-LH-03',1,1002)
    w.transition(ep,{'op':'setting','key':'backup.retention','value':retention})
    w.transition(ep,{'op':'create-job','name':'Inventory','kind':'inventory','input':'inputs','output':'documents','dependency':'','trigger':'manual'})
    w.transition(ep,{'op':'run-job','target':'job-1'})
    w.transition(ep,{'op':'create-job','name':'Backup','kind':'backup','input':'inputs','output':'documents','dependency':'Inventory','trigger':'manual'})
    assert w.transition(ep,{'op':'run-job','target':'job-2'})['outcome']['status']=='Completed'
    return ep


def test_versioned_retention_preserves_real_previous_snapshot_bytes_on_rerun():
    ep=create_backup('versioned')
    first=ep['state']['backup_history'][0]
    original=w.get_file(ep['state'],first['file'])['content']
    assert w.transition(ep,{'op':'update-job','target':'job-2'})['accepted']
    assert w.get_file(ep['state'],first['file'])['content']==original
    assert w.transition(ep,{'op':'run-job','target':'job-2'})['outcome']['status']=='Completed'
    second=ep['state']['backup_history'][1]
    assert second['file']!=first['file'] and second['version']==2
    assert json.loads(w.get_file(ep['state'],second['file'])['content'])['resources']==json.loads(original)['resources']
    assert w.get_file(ep['state'],first['file'])['content']==original


def test_keep_originals_replaces_only_generated_snapshot_not_source_documents():
    ep=create_backup('keep')
    first=ep['state']['backup_history'][0]
    source=w.get_file(ep['state'],'source-0')['content']
    assert w.transition(ep,{'op':'update-job','target':'job-2'})['accepted']
    assert next(f for f in ep['state']['files'] if f['id']==first['file'])['deleted']
    assert w.transition(ep,{'op':'run-job','target':'job-2'})['outcome']['status']=='Completed'
    assert w.get_file(ep['state'],'source-0')['content']==source


def test_recovery_rejects_tampered_actual_backup_snapshot():
    ep=create_backup('versioned')
    snapshot=ep['state']['backup_history'][0]['file']
    w.transition(ep,{'op':'write','target':snapshot,'content':'{}'})
    result=w.transition(ep,{'op':'create-job','name':'Restore','kind':'restore','input':'inputs','output':'recovery','dependency':'Backup','trigger':'manual'})
    job=result['outcome']
    failed=w.transition(ep,{'op':'run-job','target':job})
    assert failed['outcome']['status']=='Failed'
    assert 'snapshot' in failed['outcome']['error'].lower()
    assert not any(f['parent']=='recovery' for f in ep['state']['files'])

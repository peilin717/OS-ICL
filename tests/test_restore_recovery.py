import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def complete(case,seed=1001):
    episode=w.generate(case,1,seed)
    for action in episode['reference']:
        w.transition(episode,action)
    assert w.evaluate(episode)['success'],w.evaluate(episode)
    return episode


def test_restore_conflict_is_atomic_and_preserves_existing_user_edits():
    for case in ['OS-LH-03','OS-LH-12']:
        episode=w.generate(case,1,1001)
        failed=False
        for action in episode['reference']:
            before=copy.deepcopy(episode['state']['files'])
            event=w.transition(episode,action)
            if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed' and 'name conflict' in event['outcome'].get('error','').lower():
                assert 'name conflict' in event['outcome']['error'].lower()
                assert episode['state']['files']==before
                failed=True
        assert failed
        assert w.evaluate(episode)['success']
        original=w.get_file(episode['initial'],'user-recovery-edit')
        current=w.get_file(episode['state'],'user-recovery-edit')
        assert current['content']==original['content'] and current['parent']==original['parent']
        restore=next(j for j in episode['state']['jobs'] if j['kind']=='restore')
        assert restore['output']!='recovery' and restore['status']=='Completed'
        healthy=complete(case,1002)
        assert next(j for j in healthy['state']['jobs'] if j['kind']=='restore')['output']=='recovery'


def test_snapshot_selection_uses_latest_complete_not_latest_filename():
    episode=complete('OS-LH-12')
    snapshots=[f for f in episode['initial']['files'] if f.get('snapshot_version')]
    latest=max(snapshots,key=lambda f:f['snapshot_version'])
    chosen=w.get_file(episode['initial'],'source-0')
    assert latest['snapshot_status']=='Incomplete'
    assert chosen['snapshot_status']=='Complete' and chosen['snapshot_version']<latest['snapshot_version']
    assert w.evaluate(episode)['checks']['latest_complete_snapshot']
    assert sum(a['op']=='properties' for a in episode['reference'])==3


def test_compare_reads_restored_bytes_instead_of_echoing_the_snapshot():
    episode=w.generate('OS-LH-03',0,1002)
    for action in episode['reference']:
        if action['op']=='run-job' and next(j for j in episode['state']['jobs'] if j['id']==action['target'])['kind']=='compare':
            restore=next(j for j in episode['state']['jobs'] if j['kind']=='restore')
            folder=w.get_file(episode['state'],restore['artifact'])['provenance']['processing']['materialized_folder']
            target=next(f for f in episode['state']['files'] if f['parent']==folder and f.get('source')=='source-1')
            w.transition(episode,{'op':'write','target':target['id'],'content':'damaged recovery copy'})
            event=w.transition(episode,action)
            assert event['outcome']['status']=='Failed' and 'differs' in event['outcome']['error']
            return
        w.transition(episode,action)
    assert False,'comparison task was not reached'

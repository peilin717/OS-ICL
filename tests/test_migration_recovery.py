import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def solve(seed=1001):
    ep=w._generate_fixture('OS-LH-07',1,seed)
    failures=[]
    for action in ep['reference']:
        before=copy.deepcopy(ep['state']['files'])
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed':
            assert event['outcome']['error'].startswith('Migrate name conflict:')
            assert ep['state']['files']==before
            failures.append(event)
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    return ep,failures


def test_migration_collision_preserves_user_edits_and_uses_clean_destination():
    ep,failures=solve()
    assert len(failures)==1
    initial=w.get_file(ep['initial'],'existing-workspace-edit')
    current=w.get_file(ep['state'],'existing-workspace-edit')
    assert all(initial[key]==current[key] for key in ['name','parent','content','revision'])
    migration=next(j for j in ep['state']['jobs'] if j['kind']=='migrate')
    assert migration['output']!='migration-target'
    healthy,failures=solve(1002)
    assert not failures
    assert next(j for j in healthy['state']['jobs'] if j['kind']=='migrate')['output']=='migration-target'


def test_migrated_app_settings_preserve_preferences_and_resolve_new_paths():
    ep,_=solve()
    action=next(a for a in ep['reference'] if a['op']=='probe')
    folder=action['target']
    settings=next(f for f in ep['state']['files'] if f['parent']==folder and f.get('source')=='source-2')
    config=json.loads(settings['content'])
    original=json.loads(w.get_file(ep['initial'],'source-2')['content'])
    assert config['preferences']==original['preferences']
    assert config['workspace_root']==w.path(ep['state'],folder)+'/'
    assert config['startup_path']==config['workspace_root']+'source.js'
    damaged={**config,'preferences':{**config['preferences'],'tab_width':99}}
    w.transition(ep,{'op':'write','target':settings['id'],'content':json.dumps(damaged)})
    assert not w.transition(ep,action)['accepted']
    assert not w.evaluate(ep)['success']
    damaged={**config,'workspace_root':original['workspace_root']}
    w.transition(ep,{'op':'write','target':settings['id'],'content':json.dumps(damaged)})
    assert not w.transition(ep,action)['accepted']
    w.transition(ep,{'op':'write','target':settings['id'],'content':json.dumps(config,indent=2)})
    assert w.transition(ep,action)['accepted']
    assert w.evaluate(ep)['success']

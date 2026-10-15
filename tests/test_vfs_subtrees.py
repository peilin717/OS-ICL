import copy
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def create_tree(ep):
    def act(**action):
        event=w.transition(ep,action)
        assert event['accepted'],event
        return event['outcome']
    root=act(op='mkdir',parent='documents',name='Temporary workspace')
    child=act(op='mkdir',parent=root,name='Nested')
    document=act(op='create-document',parent=child,name='notes.txt',content='Disposable test data')
    return root,child,document


def test_folder_delete_removes_complete_nested_subtree_and_rejects_stale_targets():
    ep=w.generate('OS-LH-01',0,1002)
    root,child,document=create_tree(ep)
    assert w.transition(ep,{'op':'delete','target':root})['accepted']
    assert all(next(f for f in ep['state']['files'] if f['id']==identifier)['deleted'] for identifier in [root,child,document])
    assert not w.transition(ep,{'op':'write','target':document,'content':'Resurrect through stale ID'})['accepted']
    assert not w.transition(ep,{'op':'create-document','parent':child,'name':'new.txt'})['accepted']


def test_locked_descendant_blocks_entire_folder_delete_atomically():
    ep=w.generate('OS-LH-01',0,1002)
    root,child,document=create_tree(ep)
    ep['state']['processes'][0]['locks']=[document]
    before=copy.deepcopy(ep['state']['files'])
    rejected=w.transition(ep,{'op':'delete','target':root})
    assert not rejected['accepted'] and 'in use' in rejected['error']
    assert ep['state']['files']==before
    w.transition(ep,{'op':'process','target':'indexer','status':'Paused'})
    assert w.transition(ep,{'op':'delete','target':root})['accepted']


def test_deleting_cache_parent_cannot_bypass_backup_verification():
    ep=w.generate('OS-LH-11',0,1002)
    for owner in ep['state']['processes']:
        if owner['locks']:w.transition(ep,{'op':'process','target':owner['id'],'status':'Paused'})
    before=copy.deepcopy(ep['state']['files'])
    rejected=w.transition(ep,{'op':'delete','target':'cache-folder'})
    assert not rejected['accepted'] and 'backup' in rejected['error'].lower()
    assert ep['state']['files']==before

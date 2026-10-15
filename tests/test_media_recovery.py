import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_missing_sidecar_fails_without_preview_and_recovers_by_download_import():
    ep=w._generate_fixture('OS-LH-04',1,1001)
    failed=False
    for action in ep['reference']:
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed':
            assert event['outcome']['error'].startswith('Caption sidecar is missing.')
            assert not any(f.get('generated_by') and f['name'].endswith('-preview.txt') for f in ep['state']['files'])
            failed=True
    assert failed and w.evaluate(ep)['success']
    assert not w.get_file(ep['initial'],'source-2')['downloaded']
    assert w.get_file(ep['state'],'source-2')['downloaded']
    transfer=next(t for t in ep['state']['transfers'] if t['id']=='download-captions')
    assert transfer['status']=='Completed'
    assert w.evaluate(ep)['checks']['media_session_organized']
    previews=[f for f in ep['state']['files'] if f['name'].endswith('-preview.txt')]
    session=json.loads(w.get_file(ep['initial'],'source-0')['content'])['session']
    assert len(previews)==2 and all(json.loads(f['content'])['session']==session for f in previews)
    assert w.get_file(ep['state'],'previous-session-clip')['content']==w.get_file(ep['initial'],'previous-session-clip')['content']


def test_healthy_media_does_not_force_a_missing_sidecar_failure():
    ep=w._generate_fixture('OS-LH-04',2,1002)
    for action in ep['reference']:
        event=w.transition(ep,action)
        assert event['accepted']
        assert not isinstance(event['outcome'],dict) or event['outcome'].get('status')!='Failed'
    assert w.evaluate(ep)['success']


def test_media_catalogue_materializes_mapping_and_delivers_actual_derived_bytes():
    ep=w._generate_fixture('OS-LH-04',0,1002)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['checks']['media_catalogue_delivered']
    catalogue=next(j for j in ep['state']['jobs'] if j['kind']=='catalogue')
    info=w.get_file(ep['state'],catalogue['artifact'])['provenance']['processing']
    manifest=w.get_file(ep['state'],info['catalogue_file'])
    document=json.loads(manifest['content'])
    assert len(document['entries'])==2
    for entry in document['entries']:
        preview=w.get_file(ep['state'],entry['preview_id'])
        assert entry['preview_sha256']==w.digest(preview['content'])
        assert entry['caption']==json.loads(preview['content'])['caption']
        assert entry['preview_path']==w.path(ep['state'],preview['id'])
    delivery=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    derived=w.get_file(ep['state'],delivery['artifact'])['provenance']['derived_artifacts']
    assert len(derived)==3 and manifest['content'] in [a['content'] for a in derived]
    w.transition(ep,{'op':'delete','target':document['entries'][0]['preview_id']})
    assert not w.evaluate(ep)['checks']['media_catalogue_delivered']
    assert not w.evaluate(ep)['success']


def test_catalogue_refuses_corrupt_preview_before_writing_any_index():
    ep=w._generate_fixture('OS-LH-04',0,1002)
    for action in ep['reference']:
        if action['op']=='run-job':
            task=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
            if task['kind']=='catalogue':
                preview=next(f for f in ep['state']['files'] if f['name'].endswith('-preview.txt'))
                w.transition(ep,{'op':'write','target':preview['id'],'content':'{}'})
                before=len(ep['state']['files'])
                failed=w.transition(ep,action)
                assert failed['outcome']['status']=='Failed'
                assert 'Media catalogue cannot be generated' in failed['outcome']['error']
                assert len(ep['state']['files'])==before
                return
        w.transition(ep,action)
    assert False,'Catalogue stage was not reached'


def test_media_verification_detects_preview_changed_after_catalogue_generation():
    ep=w._generate_fixture('OS-LH-04',0,1002)
    for action in ep['reference']:
        if action['op']=='run-job':
            task=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
            if task['kind']=='verify':
                preview=next(f for f in ep['state']['files'] if f['name'].endswith('-preview.txt'))
                original=preview['content']
                w.transition(ep,{'op':'write','target':preview['id'],'content':'{}'})
                failed=w.transition(ep,action)
                assert failed['outcome']['status']=='Failed'
                assert 'Media verification failed' in failed['outcome']['error']
                w.transition(ep,{'op':'write','target':preview['id'],'content':original})
                assert w.transition(ep,action)['outcome']['status']=='Completed'
                continue
        w.transition(ep,action)
    assert w.evaluate(ep)['success']

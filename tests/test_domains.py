import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def solve(case):
    ep=w._generate_fixture(case,1,173)
    for action in ep['reference']:
        w.transition(ep,action)
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    return ep


def test_offline_requires_actual_disconnected_access_receipt():
    ep=solve('OS-LH-06')
    ep['state']['receipts']=[]
    assert not w.evaluate(ep)['success']
    action=next(a for a in reversed(ep['reference']) if a['op']=='probe')
    w.transition(ep,{'op':'setting','key':'network.offline','value':False})
    assert not w.transition(ep,action)['accepted']
    w.transition(ep,{'op':'setting','key':'network.offline','value':True})
    assert w.transition(ep,action)['accepted']
    target=w.get_file(ep['state'],action['target'])
    contact=next(f for f in ep['state']['files'] if f['parent']==target['id'] and f.get('source')=='source-1')
    w.transition(ep,{'op':'delete','target':contact['id']})
    assert not w.transition(ep,action)['accepted']
    assert not w.evaluate(ep)['success']


def test_transfer_failure_is_persistent_and_retry_requires_reconnected_adapter():
    ep=w._generate_fixture('OS-LH-06',0,1001)
    target=ep['state']['transfers'][0]['id']
    failed=w.transition(ep,{'op':'download','target':target})
    assert failed['accepted'] and failed['outcome']['status']=='Failed'
    transfer=ep['state']['transfers'][0]
    assert transfer['status']=='Failed' and transfer['attempts']==1
    assert not w.get_file(ep['state'],transfer['file'])['downloaded']
    assert ep['state']['events'][-1]['source']=='Transfer Manager'
    again=w.transition(ep,{'op':'download','target':target})
    assert again['outcome']['status']=='Failed' and ep['state']['transfers'][0]['attempts']==2
    w.transition(ep,{'op':'device','target':'field-relay','connected':True})
    assert w.transition(ep,{'op':'download','target':target})['accepted']
    completed=ep['state']['transfers'][0]
    assert completed['status']=='Completed' and completed['error']=='' and completed['attempts']==3
    assert w.get_file(ep['state'],completed['file'])['downloaded']


def test_offline_omitted_cache_requires_scope_repair_and_actual_rebuild():
    ep=w._generate_fixture('OS-LH-06',1,1001)
    failed_probe=None
    for action in ep['reference']:
        event=w.transition(ep,action)
        if action['op']=='probe' and not event['accepted']:
            failed_probe=action
            assert 'missing Contacts' in event['error']
            cached=[f for f in ep['state']['files'] if f['parent']==action['target'] and not f['deleted']]
            assert not any(f.get('source')=='source-1' for f in cached)
            assert not w.evaluate(ep)['success']
            # A setting change is not a retroactive rebuild of cached bytes.
            w.transition(ep,{'op':'setting','key':'cache.contacts','value':True})
            assert not w.transition(ep,action)['accepted']
    assert failed_probe is not None
    assert w.evaluate(ep)['success']
    cache=next(j for j in ep['state']['jobs'] if j['kind']=='cache')
    processing=w.get_file(ep['state'],cache['artifact'])['provenance']['processing']
    assert processing['omitted_sources']==[]
    assert any(f.get('source')=='source-1' and f['parent']==processing['materialized_folder'] and not f['deleted'] for f in ep['state']['files'])
    healthy=w._generate_fixture('OS-LH-06',1,1002)
    assert healthy['initial']['settings']['cache.contacts']
    assert len([a for a in healthy['reference'] if a['op']=='probe'])==1


def test_migration_rewrites_paths_and_launches_materialized_workspace():
    ep=solve('OS-LH-07')
    action=next(a for a in ep['reference'] if a['op']=='probe')
    manifest=next(f for f in ep['state']['files'] if f['parent']==action['target'] and f.get('source')=='source-0')
    assert '/Inputs/' not in manifest['content']
    migrated=next(j for j in ep['state']['jobs'] if j['kind']=='migrate')
    assert w.path(ep['state'],migrated['output'])+'/' in manifest['content']
    ep['state']['receipts']=[]
    assert not w.evaluate(ep)['success']
    w.transition(ep,{'op':'write','target':manifest['id'],'content':w.get_file(ep['initial'],'source-0')['content']})
    assert not w.transition(ep,action)['accepted']


def test_evidence_delivers_exact_window_and_redacts_actual_log_bytes():
    ep=solve('OS-LH-09')
    job=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    resources=w.get_file(ep['state'],job['artifact'])['provenance']['resources']
    logs=[r['content'] for r in resources if r['source'] in {'source-0','source-1'}]
    assert logs
    import json
    records=[json.loads(line) for content in logs for line in content.splitlines()]
    window=ep['initial']['incident']
    assert len(records)==4 and all(window['start']<=r['time']<=window['end'] for r in records)
    # This fixture uses context B, which now removes personal fields rather
    # than replacing their values with the context A mask marker.
    assert all(not any(field in r for field in ep['initial']['sensitive_fields']) for r in records)
    assert '@example.test' in w.get_file(ep['initial'],'source-0')['content']


def test_storage_cleanup_requires_verified_backup_and_releases_exact_cache_bytes():
    initial=w._generate_fixture('OS-LH-11',0,42)
    for owner in initial['state']['processes']:
        if owner['locks']:w.transition(initial,{'op':'process','target':owner['id'],'status':'Paused'})
    denied=w.transition(initial,{'op':'delete','target':'cache-0'})
    assert not denied['accepted'] and 'backup' in denied['error'].lower()
    ep=solve('OS-LH-11')
    receipt=next(r for r in ep['state']['receipts'] if r['kind']=='storage')
    caches=[f for f in ep['initial']['files'] if f.get('regenerable')]
    assert receipt['result']['freed_cache_bytes']==sum(len(f['content'].encode()) for f in caches)
    assert all(f['deleted'] for f in ep['state']['files'] if f.get('regenerable'))
    w.transition(ep,{'op':'process','target':'cache-owner-0','status':'Paused'})
    assert not w.evaluate(ep)['success']


def test_distribution_persists_schedule_instead_of_dispatching_immediately():
    ep=solve('OS-LH-10')
    delivery=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    assert delivery['status']=='Scheduled'
    p=w.get_file(ep['state'],delivery['artifact'])['provenance']['processing']
    assert p['dispatch_status']=='Scheduled' and p['trigger']=='idle'
    w.transition(ep,{'op':'device','target':'destination','connected':False})
    assert not w.evaluate(ep)['success']


def test_storage_compaction_decodes_actual_payload_and_rejects_corruption():
    import json
    import zlib
    ep=solve('OS-LH-11')
    compact=next(j for j in ep['state']['jobs'] if j['kind']=='compact')
    report=w.get_file(ep['state'],compact['artifact'])['provenance']
    processing=report['processing']
    artifact=w.get_file(ep['state'],processing['compressed_artifact'])
    packed=bytes.fromhex(artifact['content'])
    decoded=zlib.decompress(packed)
    assert json.loads(decoded)==report['resources']
    assert len(decoded)==processing['bytes_before']
    assert len(packed)==processing['bytes_after']==artifact['storage_bytes']
    assert len(packed)<len(decoded)
    assert w.evaluate(ep)['checks']['lossless_compaction_effective']
    # Mutate bytes, not the success flag on the report.
    w.transition(ep,{'op':'write','target':artifact['id'],'content':'00010203'})
    assert not w.evaluate(ep)['checks']['lossless_compaction_effective']
    assert not w.evaluate(ep)['success']


def test_media_caption_repair_and_preview_integrity():
    ep=solve('OS-LH-04')
    transcode=next(j for j in ep['state']['jobs'] if j['kind']=='transcode')
    folder=w.get_file(ep['state'],transcode['artifact'])['provenance']['processing']['preview_folder']
    preview=next(f for f in ep['state']['files'] if f['parent']==folder)
    import json
    record=json.loads(preview['content'])
    record['caption']='Incorrect caption'
    w.transition(ep,{'op':'write','target':preview['id'],'content':json.dumps(record,indent=2)})
    assert not w.evaluate(ep)['checks']['captioned_previews']


def test_print_repaired_layout_has_explicit_page_breaks():
    ep=solve('OS-LH-05')
    layout=next(j for j in ep['state']['jobs'] if j['kind']=='layout')
    processing=w.get_file(ep['state'],layout['artifact'])['provenance']['processing']
    report_pages=[p for p in processing['pages'] if p['name'].endswith('report.txt')]
    lines=len(w.get_file(ep['initial'],'source-1')['content'].splitlines())
    assert [p['lines'] for p in sorted(report_pages,key=lambda p:p['page'])]==[35,lines-35]


def test_restoration_recreates_persisted_schedule_and_local_paths():
    ep=solve('OS-LH-12')
    import json
    expected=json.loads(w.get_file(ep['initial'],'source-0')['content'])['scheduled_tasks'][0]
    restored=next(j for j in ep['state']['jobs'] if j['name']==expected['name'])
    assert restored['status']=='Ready' and restored['trigger']==expected['trigger']
    action=next(a for a in ep['reference'] if a['op']=='probe' and a['kind']=='restoration')
    w.transition(ep,{'op':'update-job','target':restored['id'],'trigger':'manual' if expected['trigger']!='manual' else 'idle'})
    assert not w.transition(ep,action)['accepted']
    assert not w.evaluate(ep)['success']

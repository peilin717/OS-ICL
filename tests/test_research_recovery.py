import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w
import domain_checks as domains


def test_research_selects_latest_approved_revisions_not_fixed_source_ids():
    ep=w._generate_fixture('OS-LH-01',1,1001)
    chosen=[domains.required_source(ep['initial'],ep['case'],i) for i in range(4)]
    assert any(f['id'].startswith('approved-update-') for f in chosen)
    draft=w.get_file(ep['initial'],'draft-source')
    assert draft['revision']>chosen[0]['revision'] and not draft['approved']
    properties=[]
    denied=[]
    for action in ep['reference']:
        event=w.transition(ep,action)
        if action['op']=='properties':properties.append(event['outcome'])
        if not event['accepted']:denied.append(event['error'])
    assert any('Research Sync' in error for error in denied)
    assert any(p.get('resource_key') and p['approved'] is False for p in properties)
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    assert w.evaluate(ep)['checks']['research_index_revisions']
    assert w.evaluate(ep)['checks']['research_owner_restored']
    delivery=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    members=w.get_file(ep['state'],delivery['artifact'])['provenance']['resources']
    assert {r['source'] for r in members if r['source'] in {f['id'] for f in ep['initial']['files']}}=={f['id'] for f in chosen}
    source=next(f for f in chosen if f['id'].startswith('approved-update-'))
    working=next(f for f in ep['state']['files'] if f.get('source')==source['id'])
    older=next(f for f in ep['initial']['files'] if f.get('resource_key')==source['resource_key'] and f['id'].startswith('source-'))
    w.transition(ep,{'op':'write','target':working['id'],'content':older['content']})
    assert not w.evaluate(ep)['success']


def test_research_service_must_be_restored_after_delivery():
    ep=w._generate_fixture('OS-LH-01',0,1001)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success']
    w.transition(ep,{'op':'process','target':'research-sync','status':'Paused'})
    assert not w.evaluate(ep)['checks']['research_owner_restored']

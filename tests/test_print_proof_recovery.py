import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_proof_diagnoses_original_overflow_then_document_is_repaired_and_revalidated():
    ep=w.generate('OS-LH-05',1,1001)
    overflow=None
    failed_index=None
    for index,action in enumerate(ep['reference']):
        before=len(ep['state']['files'])
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('error','').startswith('Proof page overflow:'):
            overflow=event
            failed_index=index
            assert 'page 1' in event['outcome']['error'] and 'capacity is 40' in event['outcome']['error']
            assert len(ep['state']['files'])==before
            layout=next(j for j in ep['state']['jobs'] if j['kind']=='layout')
            pages=w.get_file(ep['state'],layout['artifact'])['provenance']['processing']['pages']
            assert any(p['lines']>40 for p in pages)
            working_report=next(f for f in ep['state']['files'] if f['parent']==layout['input'] and f.get('source')=='source-1')
            assert working_report['content']==w.get_file(ep['initial'],'source-1')['content']
    assert overflow is not None
    assert ep['reference'][failed_index+1]['op']=='write'
    assert '\f' in ep['reference'][failed_index+1]['content']
    assert any(a['op']=='update-job' for a in ep['reference'][failed_index+2:])
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    assert w.get_file(ep['state'],'source-1')['content']==w.get_file(ep['initial'],'source-1')['content']


def test_healthy_document_does_not_force_a_page_break_or_failed_proof():
    ep=w.generate('OS-LH-05',2,1002)
    for action in ep['reference']:
        event=w.transition(ep,action)
        assert event['accepted']
        assert not isinstance(event['outcome'],dict) or event['outcome'].get('status')!='Failed'
    assert not any(a['op']=='write' and '\f' in a.get('content','') for a in ep['reference'])
    assert w.evaluate(ep)['success']

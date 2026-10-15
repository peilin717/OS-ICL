import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_incompatible_printer_fails_without_output_and_fallback_profile_is_proved():
    ep=w._generate_fixture('OS-LH-05',1,1001)
    failures=[]
    for action in ep['reference']:
        before=len(ep['state']['files'])
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed':
            assert 'does not support' in event['outcome']['error'] or event['outcome']['error'].startswith('Proof page overflow:')
            assert len(ep['state']['files'])==before
            failures.append(event)
    assert len(failures)==2
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    assert ep['state']['settings']['printer.selected']=='production-printer'
    layout=next(j for j in ep['state']['jobs'] if j['kind']=='layout')
    proof=next(j for j in ep['state']['jobs'] if j['kind']=='proof')
    p=w.get_file(ep['state'],layout['artifact'])['provenance']['processing']
    confirmation=w.get_file(ep['state'],proof['artifact'])['provenance']['processing']
    assert p['paper']==ep['initial']['print_request']['paper']==confirmation['paper']
    assert p['printer']==confirmation['printer']=='production-printer'


def test_changed_print_profile_requires_new_layout_before_proof():
    ep=w._generate_fixture('OS-LH-05',0,1002)
    for action in ep['reference']:
        if action['op']=='run-job':
            task=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
            if task['kind']=='proof':
                original=ep['state']['settings']['printer.paper']
                other='Letter' if original=='A4' else 'A4'
                w.transition(ep,{'op':'setting','key':'printer.paper','value':other})
                result=w.transition(ep,action)
                assert result['outcome']['status']=='Failed'
                assert 'settings changed after layout' in result['outcome']['error']
                w.transition(ep,{'op':'setting','key':'printer.paper','value':original})
                assert w.transition(ep,action)['outcome']['status']=='Completed'
                continue
        w.transition(ep,action)
    assert w.evaluate(ep)['success']


def test_non_printer_cannot_be_selected_as_print_destination():
    ep=w._generate_fixture('OS-LH-05',0,1002)
    result=w.transition(ep,{'op':'setting','key':'printer.selected','value':'camera'})
    assert not result['accepted']
    assert ep['state']['settings']['printer.selected']=='printer'

import copy
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def solve(convention,wrong=False):
    ep=w.generate('OS-LH-05',convention,1002)
    for original in ep['reference']:
        action=copy.deepcopy(original)
        if wrong and action['op']=='setting' and action['key']=='printer.order':action['value']='forward'
        event=w.transition(ep,action)
        assert event['accepted'],event
        assert not isinstance(event['outcome'],dict) or event['outcome'].get('status')!='Failed'
    return ep


def test_reverse_output_changes_actual_queue_sequence_and_matches_proof():
    forward=solve(0);reverse=solve(1)
    for ep in [forward,reverse]:
        assert w.evaluate(ep)['success']
        layout=next(j for j in ep['state']['jobs'] if j['kind']=='layout')
        pages=w.get_file(ep['state'],layout['artifact'])['provenance']['processing']['pages']
        assert ep['state']['print_queue'][0]['pages']==pages
    roles=lambda ep:[p['name'].split('-',1)[-1] for p in ep['state']['print_queue'][0]['pages']]
    assert roles(reverse)==list(reversed(roles(forward)))
    assert reverse['state']['print_queue'][0]['order']=='reverse'


def test_legal_wrong_output_order_fails_only_the_demonstrated_order_spec():
    ep=solve(1,True)
    result=w.evaluate(ep)
    assert result['checks']['print_proof_valid'] and result['checks']['print_submission_queued']
    assert not result['checks']['printer.order'] and not result['rule_compliance'] and not result['success']


def test_order_change_after_layout_requires_reproof():
    ep=solve(0)
    proof=next(j for j in ep['state']['jobs'] if j['kind']=='proof')
    w.transition(ep,{'op':'setting','key':'printer.order','value':'reverse'})
    assert 'settings changed after layout' in w.job_error(ep['state'],proof,ep['case'])
    delivery=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    assert 'settings changed after proof' in w.job_error(ep['state'],delivery,ep['case'])

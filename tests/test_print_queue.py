import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def solve():
    ep=w.generate('OS-LH-05',1,1001)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    return ep


def test_queue_controls_and_cancel_before_producer_reset():
    ep=solve()
    queue=ep['state']['print_queue'][0]
    assert len(queue['documents'])==4 and len(queue['pages'])==5
    assert w.transition(ep,{'op':'print-control','target':queue['id'],'status':'Paused'})['accepted']
    assert not w.evaluate(ep)['checks']['print_submission_queued']
    printer=queue['printer']
    w.transition(ep,{'op':'device','target':printer,'connected':False})
    assert not w.transition(ep,{'op':'print-control','target':queue['id'],'status':'Queued'})['accepted']
    w.transition(ep,{'op':'device','target':printer,'connected':True})
    assert w.transition(ep,{'op':'print-control','target':queue['id'],'status':'Queued'})['accepted']
    assert w.evaluate(ep)['success']
    assert not w.transition(ep,{'op':'update-job','target':queue['task']})['accepted']
    assert w.transition(ep,{'op':'print-control','target':queue['id'],'status':'Cancelled'})['accepted']
    assert not w.evaluate(ep)['success']
    assert not w.transition(ep,{'op':'print-control','target':queue['id'],'status':'Queued'})['accepted']
    assert w.transition(ep,{'op':'update-job','target':queue['task']})['accepted']
    assert w.transition(ep,{'op':'run-job','target':queue['task']})['outcome']['status']=='Completed'
    assert w.evaluate(ep)['success']
    assert len(ep['state']['print_queue'])==2


def test_submission_rejects_document_changes_after_proof():
    ep=w.generate('OS-LH-05',0,1002)
    for action in ep['reference']:
        if action['op']=='run-job':
            task=next(j for j in ep['state']['jobs'] if j['id']==action['target'])
            if task['kind']=='deliver':
                document=next(f for f in ep['state']['files'] if f['parent']==task['input'] and f.get('source')=='source-0')
                w.transition(ep,{'op':'write','target':document['id'],'content':document['content']+'Unproved edit\n'})
                result=w.transition(ep,action)
                assert result['outcome']['status']=='Failed'
                assert 'Documents changed after proof' in result['outcome']['error']
                assert ep['state']['print_queue']==[]
                return
        w.transition(ep,action)
    assert False,'Submission stage was not reached'

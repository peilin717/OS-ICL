import copy
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
import workflows as w
import tasks36


def solve(ep):
    for action in ep['reference']:w.transition(ep,action)
    return ep


@pytest.mark.parametrize('cid',[x['id'] for x in tasks36.CASES])
@pytest.mark.parametrize('scope',['standard','module-demo'])
def test_all_conditions_initial_privacy_correct_and_wrong_rules(cid,scope):
    for seed in [1001,1002,1003]:
        episodes=[w.generate(cid,c,seed,scope) for c in range(3)]
        payloads=[w.public(ep,'evaluation') for ep in episodes]
        assert payloads[0]==payloads[1]==payloads[2],(cid,seed)
        def private_keys(value):
            if isinstance(value,dict):
                return any(k in {'_judge36','_brief36','recorder_brief','reference','convention'} or private_keys(v) for k,v in value.items())
            if isinstance(value,list):return any(private_keys(v) for v in value)
            return False
        assert not private_keys(payloads)
        for c,ep in enumerate(episodes):
            assert not w.evaluate(ep)['success']
            solved=solve(copy.deepcopy(ep))
            result=w.evaluate(solved)
            assert result['success'],(cid,c,seed,result['failed_checks'])
            wrong=copy.deepcopy(ep)
            for action in episodes[(c+1)%3]['reference']:w.transition(wrong,action)
            assert not w.evaluate(wrong)['success'],('wrong demo accepted',cid,c,seed)
            protected=copy.deepcopy(solved)
            target=next(f for f in protected['initial']['files'] if f['kind']!='folder' and not set(protected['_judge36']['writable'].get('files',{}).get(f['id'],[])).intersection({'content','deleted'}))
            w.get_file(protected['state'],target['id'])['content']='Tampered original'
            assert not w.evaluate(protected)['success'],('protected source tamper accepted',cid,c,seed)


@pytest.mark.parametrize('cid',[x['id'] for x in tasks36.CASES])
def test_omitting_final_required_mutation_and_injected_result_cannot_pass(cid):
    ep=w.generate(cid,0,4201,'standard')
    probe=copy.deepcopy(ep);meaningful=[]
    for i,action in enumerate(probe['reference']):
        before=w.digest(probe['state']);event=w.transition(probe,action)
        if event['accepted'] and before!=w.digest(probe['state']) and action['op']!='properties':meaningful.append(i)
    last=meaningful[-1]
    for i,action in enumerate(ep['reference']):
        if i!=last:w.transition(ep,action)
    ep['state']['result']={'success':True};ep['state']['success']=True
    assert not w.evaluate(ep)['success'],cid


def test_manual_expected_values_not_reference_replay():
    ep=w.generate('OS-E-05',0,41)
    assert sorted(p['memory'] for p in ep['initial']['processes'])==[127,128,255,256,383,384]
    for p in ep['state']['processes']:
        if p['memory']>=128:p['status']='Paused'
    assert w.evaluate(ep)['success']
    ep=w.generate('OS-M-11',0,41)
    stock=next(f for f in ep['state']['files'] if f['name']=='stock-working.json')
    assert any(g.get('id')==stock['id'] and json.loads(g['value'])==[{'lot_id':'L1','quantity':'29 pcs'},{'lot_id':'L2','quantity':'13 pcs'}] for g in ep['_judge36']['goals'])


def test_36_catalogue_quota_and_local_demo_scope():
    assert {level:sum(c['difficulty']==level for c in tasks36.CASES) for level in ['easy','medium','hard']}=={'easy':12,'medium':12,'hard':12}
    for cid in ['OS-H-04','OS-H-05','OS-H-09','OS-H-10']:
        ep=w.generate(cid,0,1001,'module-demo')
        assert len(ep['reference'])<=8,(cid,ep['reference'])


def test_unused_correct_proof_cannot_authorize_a_wrong_profile_submission():
    ep=solve(w.generate('OS-H-05',0,1001))
    state=ep['state'];old=next(j for j in state['jobs'] if j['kind']=='deliver');queue=state['print_queue'][0]
    w.transition(ep,{'op':'print-control','target':queue['id'],'status':'Cancelled'})
    w.transition(ep,{'op':'update-job','target':old['id']})
    w.transition(ep,{'op':'setting','key':'printer.paper','value':'Letter'})
    previous=next(j['name'] for j in state['jobs'] if j['kind']=='validate')
    # transition replaces state atomically: use fresh state after each call.
    input_id=old['input'];output_id=old['output']
    for kind in ['layout','proof','verify','deliver']:
        name='replacement-'+kind
        event=w.transition(ep,{'op':'create-job','name':name,'kind':kind,'input':input_id,'output':output_id,'dependency':previous,'trigger':'manual'})
        assert event['accepted']
        result=w.transition(ep,{'op':'run-job','target':event['outcome']})
        assert result['outcome']['status']=='Completed',result
        previous=name
    assert any(j['kind']=='proof' and j['status']=='Completed' for j in ep['state']['jobs'])
    assert not w.evaluate(ep)['success']


def test_extra_completed_delivery_is_not_harmless_navigation():
    ep=solve(w.generate('OS-M-08',0,4201))
    last=next(j for j in ep['state']['jobs'] if j['kind']=='deliver')
    event=w.transition(ep,{'op':'create-job','name':'unrequested-delivery','kind':'deliver','input':last['input'],'output':last['output'],'dependency':last['dependency'],'trigger':'manual'})
    result=w.transition(ep,{'op':'run-job','target':event['outcome']})
    assert result['outcome']['status']=='Completed'
    assert not w.evaluate(ep)['success']

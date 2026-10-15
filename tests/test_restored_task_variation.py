import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_missing_and_outdated_tasks_are_recreated_or_repaired_without_duplicates():
    triggers=set();existing_names=set()
    for seed in range(1000,1006):
        ep=w._generate_fixture('OS-LH-12',1,seed)
        definitions=json.loads(w.get_file(ep['initial'],'source-0')['content'])['scheduled_tasks']
        original_saved=next((j for j in ep['initial']['jobs'] if j['id']=='saved-task-1'),None)
        for action in ep['reference']:w.transition(ep,action)
        assert w.evaluate(ep)['success'],w.evaluate(ep)
        restore=next(j for j in ep['state']['jobs'] if j['kind']=='restore')
        folder=w.get_file(ep['state'],restore['artifact'])['provenance']['processing']['materialized_folder']
        for expected in definitions:
            matching=[j for j in ep['state']['jobs'] if j['name']==expected['name']]
            assert len(matching)==1
            actual=matching[0]
            assert actual['input']==folder and actual['trigger']==expected['trigger'] and actual['status']=='Ready'
            output=w.get_file(ep['state'],actual['output'])
            assert output['parent']==folder and output['name']==expected['output']
            triggers.add(actual['trigger'])
        if original_saved:
            repaired=next(j for j in ep['state']['jobs'] if j['name']==original_saved['name'])
            assert repaired['id']==original_saved['id']
            assert repaired['input']!=original_saved['input'] and repaired['trigger']!=original_saved['trigger']
            existing_names.add(original_saved['name'])
    assert triggers=={'manual','idle','plugged-in'} and len(existing_names)>1


def test_restored_task_output_location_is_part_of_recovery_validation():
    ep=w._generate_fixture('OS-LH-12',0,1001)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success']
    definition=json.loads(w.get_file(ep['initial'],'source-0')['content'])['scheduled_tasks'][0]
    saved=next(j for j in ep['state']['jobs'] if j['name']==definition['name'])
    w.transition(ep,{'op':'update-job','target':saved['id'],'output':'documents'})
    check=next(a for a in ep['reference'] if a['op']=='probe' and a['kind']=='restoration')
    assert not w.transition(ep,check)['accepted']
    assert not w.evaluate(ep)['checks']['restored_schedule_configuration']

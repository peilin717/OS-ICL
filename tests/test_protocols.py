import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_conventions_have_distinct_procedures_but_identical_query_state():
    for case in w._FIXTURE_CASES:
        episodes=[w._generate_fixture(case['id'],context,1002) for context in range(3)]
        assert len({tuple(e['case']['pipeline']) for e in episodes})==3
        assert all(w.public(e)==w.public(episodes[0]) for e in episodes)


def test_application_does_not_enforce_or_expose_hidden_procedure():
    # Healthy seed isolates procedure privacy from unrelated physical locks.
    target=w._generate_fixture('OS-LH-01',1,1002)
    # Use the correct convention's directory/configuration values but an
    # interactive procedure. Tools accept this legitimate workflow; the
    # convention-specific evaluation rejects its missing checkpoint.
    actions=w.reference(copy.deepcopy(w._FIXTURE_BY_ID['OS-LH-01']),target['initial'],w.CONVENTIONS[1])
    for action in actions:
        event=w.transition(target,action)
        assert event['accepted'],event
        assert not isinstance(event['outcome'],dict) or event['outcome'].get('status')!='Failed',event
    result=w.evaluate(target)
    assert not result['success'] and not result['checks']['job_backup']
    assert all(result['checks'][f'resource_{i}'] for i in range(4))
    assert result['checks']['archive.format'] and result['checks']['scheduler.trigger']


def test_document_formatting_is_not_an_oracle_constraint():
    for case in ['OS-LH-07','OS-LH-08','OS-LH-12']:
        episode=w._generate_fixture(case,1,1001)
        for action in episode['reference']:
            action=copy.deepcopy(action)
            if action['op']=='write' and action['content'].lstrip().startswith('{'):
                action['content']=json.dumps(json.loads(action['content']),sort_keys=True,separators=(',',':'))
            w.transition(episode,action)
        assert w.evaluate(episode)['success'],w.evaluate(episode)


def test_scenarios_cover_ready_and_recovery_branches():
    ready=w._generate_fixture('OS-LH-08',0,1002)
    recover=w._generate_fixture('OS-LH-08',0,1001)
    assert ready['scenario']==0 and recover['scenario']!=0
    assert not ready['state']['processes'][0]['locks']
    assert any(p['locks'] for p in recover['state']['processes'])
    assert len(ready['reference'])<len(recover['reference'])
    for case in ['OS-LH-02','OS-LH-04','OS-LH-05','OS-LH-06','OS-LH-08','OS-LH-10','OS-LH-12']:
        assert w._generate_fixture(case,0,1002)['initial']!=w._generate_fixture(case,0,1001)['initial']

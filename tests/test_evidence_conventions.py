"""Privacy procedure ICL: same query, all safe tools, different real output."""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import domain_checks as d
import workflows as w


@pytest.mark.parametrize('context', range(3))
@pytest.mark.parametrize('seed', [1001, 1002, 1003])
def test_evidence_methods_materialize_expected_records(context, seed):
    ep = w._generate_fixture('OS-LH-09', context, seed)
    assert all(w.public(w._generate_fixture('OS-LH-09', other, seed)) == w.public(ep)
               for other in range(3))
    for action in ep['reference']:
        event = w.transition(ep, action)
        assert event['accepted'], event
    result = w.evaluate(ep)
    assert result['success'], result
    redaction = next(j for j in ep['state']['jobs'] if j['kind'] == 'redact')
    report = w.get_file(ep['state'], redaction['artifact'])['provenance']
    method = w.CONVENTIONS[context]['redaction']
    assert report['processing']['method'] == method
    originals = {r['event_id']: r for i in [0, 1]
                 for r in map(json.loads, w.get_file(ep['initial'], f'source-{i}')['content'].splitlines())}
    records = []
    for identifier in report['processing']['redacted_files']:
        records.extend(map(json.loads, w.get_file(ep['state'], identifier)['content'].splitlines()))
    assert len(records) == 4
    for record in records:
        assert record == d.redact_record(originals[record['event_id']], ep['initial']['sensitive_fields'], method)
    if method == 'pseudonym':
        # Same operator in the two channels remains linkable, unlike masking.
        assert records[0]['contact'] == records[2]['contact']
        assert records[0]['contact'] != records[1]['contact']


@pytest.mark.parametrize('context', range(3))
@pytest.mark.parametrize('method', ['mask', 'remove', 'pseudonym'])
def test_safe_wrong_method_is_not_revealed_by_runtime_but_fails_final_output(context, method):
    ep = w._generate_fixture('OS-LH-09', context, 1002)  # ready resources, no scope failure
    for original in ep['reference']:
        action = copy.deepcopy(original)
        if action['op'] == 'setting' and action['key'] == 'privacy.method':
            action['value'] = method
        event = w.transition(ep, action)
        assert event['accepted'], event
        assert not isinstance(event['outcome'], dict) or event['outcome'].get('status') != 'Failed', event
    result = w.evaluate(ep)
    matched = method == w.CONVENTIONS[context]['redaction']
    assert result['success'] == matched, result
    assert result['checks']['redaction_method_learned'] == matched
    assert result['checks']['delivery_redacted'] == matched
    if not matched:
        assert result['checks']['delivery']
        assert result['checks']['preserved_originals']


def test_pseudonym_is_deterministic_field_specific_and_not_anonymization_claim():
    record = {'contact': 'operator@example.test', 'account_id': 'operator@example.test', 'message': 'Connection lost'}
    first = d.redact_record(record, ['contact', 'account_id'], 'pseudonym')
    assert first == d.redact_record(record, ['contact', 'account_id'], 'pseudonym')
    assert first['contact'] != first['account_id']
    assert first['message'] == record['message']
    assert 'operator@example.test' not in json.dumps(first)
    assert record['contact'] == 'operator@example.test'

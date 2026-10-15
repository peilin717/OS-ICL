"""Controller payloads contain visible resources but no authoring answer plan.

This does not authorize HTTP/DOM access for a visual agent; its inputs remain
pixels, task text and videos, as documented in the external runner protocol.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workflows as w

PRIVATE_KEYS = {'convention', 'reference', 'recorder_brief', 'pipeline', 'recovery',
                'required_pipeline', 'expected', 'expected_hash', 'policy',
                'rule_text', 'plan_variant', 'source_hashes', 'implementation'}


def assert_no_authoring_keys(value):
    if isinstance(value, dict):
        assert not PRIVATE_KEYS.intersection(value)
        for child in value.values():
            assert_no_authoring_keys(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_authoring_keys(child)


@pytest.mark.parametrize('case', w.CASES, ids=lambda case: case['id'])
def test_public_queries_hide_answers_across_demo_and_query_scenarios(case):
    for seed in (1001, 1002, 1003, 42, 173, 4201):
        payloads = [w.public(w.generate(case['id'], context, seed), 'evaluation')
                    for context in range(3)]
        for payload in payloads:
            assert_no_authoring_keys(payload)
        assert payloads[0] == payloads[1] == payloads[2]


def test_demo_authoring_still_has_private_plan_for_trusted_recorder():
    payload = w.public(w.generate('OS-LH-01', 2, 1003), 'demo')
    assert payload['recorder_brief']['convention'] == w.CONVENTIONS[2]
    assert payload['recorder_brief']['reference']
    assert payload['case']['pipeline']

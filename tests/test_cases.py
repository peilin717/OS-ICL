import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cases import CASES, CASE_BY_ID, available_actions, generate_episode
from server import evaluate, public_session


def session_for(case_id, rule, seed=41):
    return {
        "id": "test", "mode": "evaluation", "status": "active", "created_at": 0,
        "episode": generate_episode(case_id, rule, seed), "actions": [], "recording": False,
        "video": None, "result": None,
    }


def test_catalogue_has_36_unique_cases():
    assert len(CASES) == 36
    assert len(CASE_BY_ID) == 36
    assert {c.family for c in CASES} == {"selection", "selection_set", "mapping", "ordering", "state_machine", "recovery", "cross_app"}


def test_all_rules_and_seeds_are_deterministic_and_executable():
    for case in CASES:
        assert available_actions(case.id)
        for rule in range(3):
            for seed in (1, 19, 991):
                left = generate_episode(case.id, rule, seed)
                right = generate_episode(case.id, rule, seed)
                assert left == right
                assert left["expected"]
                assert all(x["verb"] and x["target"] for x in left["expected"])


def test_public_evaluation_session_does_not_leak_rule():
    payload = public_session(session_for("OS-SEL-01", 2))
    encoded = str(payload)
    assert "rule_text" not in payload
    assert "rule" not in payload
    assert "shortest name" not in encoded.lower()


def test_expected_trajectory_passes_and_empty_trajectory_fails():
    for case in CASES:
        session = session_for(case.id, 1)
        assert not evaluate(session)["success"]
        session["actions"] = [dict(action, at=1) for action in session["episode"]["expected"]]
        result = evaluate(session)
        assert result["success"], (case.id, session["episode"]["expected"], result)
        assert result["side_effect_free"]


def test_different_rules_change_the_expected_policy():
    for case in CASES:
        signatures = []
        query_states = []
        for rule in range(3):
            ep = generate_episode(case.id, rule, 77)
            signatures.append(tuple((x["verb"], x["target"]) for x in ep["expected"]))
            query_states.append(ep["items"])
        assert len(set(signatures)) == 3, (case.id, signatures)
        assert query_states[0] == query_states[1] == query_states[2], case.id

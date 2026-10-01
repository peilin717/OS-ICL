import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cases import CASES, CASE_BY_ID, available_actions, generate_episode
import server as server_module
from server import EPISODES, RENDER_TEMP, SESSIONS, VIDEOS, evaluate, find_demos, public_session, schedule_video_render


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


def test_incomplete_demo_is_ignored_by_demo_library():
    path = EPISODES / "test_incomplete_demo.json"
    path.write_text('{"mode":"demo","result":null,"episode":{"case":{"id":"OS-SEL-01"},"rule":0}}', encoding="utf-8")
    try:
        assert all(x["episode_id"] != "test_incomplete_demo" for x in find_demos("OS-SEL-01", 0))
    finally:
        path.unlink(missing_ok=True)


def test_successful_demo_without_ready_video_is_ignored():
    path = EPISODES / "test_unrendered_demo.json"
    path.write_text(
        '{"id":"test_unrendered_demo","mode":"demo","video":null,"video_status":"rendering",'
        '"result":{"success":true},"episode":{"seed":1,"case":{"id":"OS-SEL-01"},"rule":0}}',
        encoding="utf-8",
    )
    try:
        assert all(x["episode_id"] != "test_unrendered_demo" for x in find_demos("OS-SEL-01", 0))
    finally:
        path.unlink(missing_ok=True)


def test_reset_generation_discards_in_flight_render(monkeypatch):
    sid = "test_cancelled_render"
    session = session_for("OS-SEL-01", 0)
    session.update({"id": sid, "mode": "demo", "status": "finished", "render_generation": 1, "video_status": "queued"})
    started = threading.Event()
    release = threading.Event()

    def fake_run(command, **_kwargs):
        output = Path(command[command.index("--output") + 1])
        started.set()
        assert release.wait(2)
        output.write_bytes(b"stale-render")
        return type("Completed", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(server_module.subprocess, "run", fake_run)
    SESSIONS[sid] = session
    schedule_video_render(sid, 1)
    assert started.wait(2)
    session.update({"status": "active", "render_generation": 2, "video_status": None, "video": None})
    release.set()
    deadline = time.time() + 2
    temp = RENDER_TEMP / f"{sid}-1.webm"
    while any(thread.name == f"video-{sid}" for thread in threading.enumerate()) and time.time() < deadline:
        time.sleep(0.01)
    assert not any(thread.name == f"video-{sid}" for thread in threading.enumerate())
    assert session["video"] is None
    assert session["video_status"] is None
    assert not temp.exists()
    assert not (VIDEOS / f"{sid}.webm").exists()
    SESSIONS.pop(sid, None)
    (EPISODES / f"{sid}.json").unlink(missing_ok=True)


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

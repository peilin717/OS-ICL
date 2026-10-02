import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cases import BENCHMARK_VERSION, CASES, CASE_BY_ID, available_actions, generate_episode
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


def test_different_seeds_create_novel_query_content():
    for case in CASES:
        left = generate_episode(case.id, 0, 101)["items"]
        right = generate_episode(case.id, 0, 202)["items"]
        left_content = [(x["name"], x["value"], x["cpu"], x["memory"], x["runtime"]) for x in left]
        right_content = [(x["name"], x["value"], x["cpu"], x["memory"], x["runtime"]) for x in right]
        assert left_content != right_content, case.id


def test_mapping_rules_match_the_published_policy_text():
    expected = {
        ("OS-MAP-01", 0): {"Blue": "copy", "Amber": "move", "Violet": "star"},
        ("OS-MAP-01", 1): {"Blue": "star", "Amber": "copy", "Violet": "move"},
        ("OS-MAP-01", 2): {"Blue": "move", "Amber": "star", "Violet": "copy"},
        ("OS-MAP-02", 0): {"Circle": "pin", "Triangle": "mute", "Square": "clear"},
        ("OS-MAP-02", 1): {"Circle": "clear", "Triangle": "pin", "Square": "mute"},
        ("OS-MAP-02", 2): {"Circle": "mute", "Triangle": "clear", "Square": "pin"},
    }
    for (case_id, rule), table in expected.items():
        episode = generate_episode(case_id, rule, 700 + rule)
        field = "color" if case_id == "OS-MAP-01" else "symbol"
        items = {item["id"]: item for item in episode["items"]}
        assert all(action["verb"] == table[items[action["target"]][field]] for action in episode["expected"])


def test_recovery_cases_are_observable_two_step_workflows():
    for case in CASES:
        if case.family != "recovery":
            continue
        for rule in range(3):
            episode = generate_episode(case.id, rule, 821)
            assert len(episode["expected"]) == 6
            grouped = {}
            for action in episode["expected"]:
                grouped.setdefault(action["target"], []).append(action["verb"])
            assert len(grouped) == 3
            assert all(len(steps) == 2 and steps[0] != steps[1] for steps in grouped.values())


def test_cross_app_workflows_have_real_navigation_and_consistent_sources():
    for case in CASES:
        if case.family != "cross_app":
            continue
        for rule in range(3):
            episode = generate_episode(case.id, rule, 902)
            workflow = episode["workflow"]
            assert workflow and workflow["source_apps"] and workflow["target_app"]
            actions = episode["expected"]
            assert [a["target"] for a in actions[:len(workflow["source_apps"])]] == workflow["source_apps"]
            assert all(a["verb"] == "open-app" for a in actions[:len(workflow["source_apps"])])
            inspect = actions[len(workflow["source_apps"])]
            assert inspect["verb"] == "inspect" and inspect["target"] in {f"source:{x['key']}" for x in workflow["records"]}
            assert actions[-2] == {"verb": "open-app", "target": workflow["target_app"]}
            assert episode["benchmark_version"] == BENCHMARK_VERSION


def test_ordering_oracles_use_visible_index_or_layer_tiebreaks():
    for case in CASES:
        if case.family != "ordering":
            continue
        assert all("Index" in rule or "Layer" in rule for rule in case.rules)
        episode = generate_episode(case.id, 0, 331)
        assert all("index" in item and "layer" in item for item in episode["items"])

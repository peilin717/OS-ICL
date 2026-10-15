import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workflows as w


def complete(case, convention=0, seed=42):
    episode = w._generate_fixture(case, convention, seed)
    for a in episode["reference"]:
        event = w.transition(episode, a)
        if not event["accepted"]:
            expected_cache_failure=(episode['case']['domain']=='offline' and a['op']=='probe' and 'Offline cache is missing Contacts' in event.get('error',''))
            assert expected_cache_failure or (a["op"] == "copy" and episode["case"]["recovery"] in {"lock", "device", "download"}), event
        if isinstance(event["outcome"], dict) and event["outcome"].get("status") == "Failed":
            expected_download_failure=(episode['case']['domain']=='offline' and a['op']=='download' and 'Field relay' in event['outcome'].get('error',''))
            expected_migration_conflict=(episode['case']['domain']=='migration' and a['op']=='run-job' and event['outcome'].get('error','').startswith('Migrate name conflict:'))
            expected_missing_sidecar=(episode['case']['domain']=='media' and a['op']=='run-job' and event['outcome'].get('error','').startswith('Caption sidecar is missing.'))
            expected_printer_failure=(episode['case']['domain']=='print' and a['op']=='run-job' and ('does not support' in event['outcome'].get('error','') or event['outcome'].get('error','').startswith('Proof page overflow:')))
            expected_access_failure=(episode['case']['domain']=='distribution' and a['op']=='run-job' and event['outcome'].get('error','').startswith('Destination access denied:'))
            expected_privacy_failure=(episode['case']['domain']=='evidence' and a['op']=='run-job' and event['outcome'].get('error','').startswith('Personal fields remain:'))
            assert expected_download_failure or expected_migration_conflict or expected_missing_sidecar or expected_printer_failure or expected_access_failure or expected_privacy_failure or episode["case"]["recovery"] in {"dependency", "lock"} or episode['case']['domain'] in {'backup','restoration'}, event
    return episode


def test_entire_catalogue_reachable_and_deterministic():
    assert len(w._FIXTURE_CASES) == 12
    for case in w._FIXTURE_CASES:
        for convention in range(3):
            for seed in [42, 173, 1001, 4201]:
                first = w._generate_fixture(case["id"], convention, seed)
                assert first == w._generate_fixture(case["id"], convention, seed)
                episode = complete(case["id"], convention, seed)
                assert w.evaluate(episode)["success"], w.evaluate(episode)
                meaningful = [e for e in episode["events"] if e["accepted"] and e["before"] != e["after"] and e["action"]["op"] != "properties"]
                assert len(meaningful) >= 25


def test_same_query_requires_demonstrated_convention():
    for case in w._FIXTURE_CASES:
        original = w._generate_fixture(case["id"], 0, 42)
        for convention in [1, 2]:
            counterfactual = w._generate_fixture(case["id"], convention, 42)
            assert w.public(original) == w.public(counterfactual)
            solved = complete(case["id"], convention)
            solved["convention"] = 0
            assert not w.evaluate(solved)["success"]


def test_no_answer_material_in_evaluation_payload():
    for case in w._FIXTURE_CASES:
        payload = w.public(w._generate_fixture(case["id"]))
        assert not {"reference", "initial", "convention", "recorder_brief", "pipeline", "recovery"}.intersection(payload)
        assert not {"pipeline", "recovery"}.intersection(payload["case"])
        assert "reference" in w.public(w._generate_fixture(case["id"]), "demo")["recorder_brief"]


def test_recovery_and_atomic_failures():
    for case_id, action in [
        ("OS-LH-04", {"op":"copy", "target":"source-0", "parent":"documents"}),
        ("OS-LH-08", {"op":"copy", "target":"source-0", "parent":"documents"}),
        ("OS-LH-06", {"op":"copy", "target":"source-0", "parent":"documents"}),
    ]:
        episode = w._generate_fixture(case_id,0,173)
        if case_id=='OS-LH-08':
            action={**action,'target':next(p['locks'][0] for p in episode['state']['processes'] if p['locks'])}
        files = copy.deepcopy(episode["state"]["files"])
        assert not w.transition(episode, action)["accepted"]
        assert episode["state"]["files"] == files
        assert episode["state"]["events"][-1]["level"] == "Error"


def test_dependencies_and_tampering_are_detected():
    episode = complete("OS-LH-01")
    artifact = w.get_file(episode["state"], episode["state"]["jobs"][0]["artifact"])
    w.transition(episode, {"op":"write", "target":artifact["id"], "content":"forged"})
    assert not w.evaluate(episode)["success"]
    episode = complete("OS-LH-03")
    restored = next(f for f in episode["state"]["files"] if f.get("source") == "source-0" and f["parent"] != w.resolve_folder(episode["state"], "Working"))
    w.transition(episode, {"op":"write", "target":restored["id"], "content":"corrupt"})
    assert not w.evaluate(episode)["success"]


def test_equivalent_navigation_and_independent_copy_order():
    episode = w._generate_fixture("OS-LH-01")
    actions = copy.deepcopy(episode["reference"])
    # Reorder settings without changing their values. ID-generating operations
    # are left in order; navigation is frontend-only and cannot change score.
    setting_indices = [i for i,a in enumerate(actions) if a["op"] == "setting"]
    values = [actions[i] for i in setting_indices][::-1]
    for i,a in zip(setting_indices,values):
        actions[i] = a
    for a in actions:
        w.transition(episode, a)
    w.transition(episode, {"op":"properties", "target":"source-0"})
    assert w.evaluate(episode)["success"]


def test_originals_cannot_be_destroyed_and_still_pass():
    episode = complete("OS-LH-01")
    w.transition(episode, {"op":"delete", "target":"old-output"})
    result = w.evaluate(episode)
    assert not result["success"] and not result["side_effect_free"]


def test_failed_build_requires_repair_revalidation_and_owner_restoration():
    episode=complete("OS-LH-08",0,173)
    assert any(e["outcome"] and isinstance(e["outcome"],dict) and e["outcome"].get("status")=="Failed" for e in episode["events"])
    working=w.resolve_folder(episode["state"],"Working")
    repaired=next(f for f in episode["state"]["files"] if f.get("source")=="source-1" and f["parent"]==working)
    assert json.loads(repaired["content"])["build_ready"] is True
    assert json.loads(w.get_file(episode["state"],"source-1")["content"])["build_ready"] is False
    w.transition(episode,{"op":"process","target":"indexer","status":"Paused"})
    assert not w.evaluate(episode)["success"]

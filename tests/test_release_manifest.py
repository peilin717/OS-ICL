import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_release_manifest_is_complete_and_oracle_free():
    path = ROOT / "data" / "manifests" / "os-icl-1.0.0.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    assert manifest["benchmark_version"] == "1.0.0"
    assert manifest["episode_schema_version"] == 2
    assert len(entries) == 108
    assert len({(entry["case_id"], entry["rule"]) for entry in entries}) == 108
    assert Counter(entry["rule"] for entry in entries) == Counter({0: 36, 1: 36, 2: 36})
    assert len({entry["episode_id"] for entry in entries}) == 108
    assert all(len(entry["sha256"]) == 64 and entry["bytes"] > 1000 for entry in entries)
    encoded = json.dumps(manifest).lower()
    assert "rule_text" not in encoded
    assert '"expected"' not in encoded

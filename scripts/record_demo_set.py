#!/usr/bin/env python3
"""Record one deterministic, rendered demonstration for every OS-ICL case."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cases import CASES, generate_episode  # noqa: E402


def request(base: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8790")
    parser.add_argument("--name", default="icl-36-rule0-v2")
    parser.add_argument("--rule", type=int, choices=range(3), default=0)
    parser.add_argument("--seed-base", type=int, default=360_000)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    target_dir = ROOT / "data" / "manifests"
    target_dir.mkdir(parents=True, exist_ok=True)
    entries = []

    for index, case in enumerate(CASES):
        seed = args.seed_base + index
        created = request(args.base_url, "/api/v1/sessions", {
            "case_id": case.id, "mode": "demo", "rule": args.rule, "seed": seed,
        })
        sid = created["id"]
        expected = generate_episode(case.id, args.rule, seed)["expected"]
        request(args.base_url, f"/api/v1/sessions/{sid}/recording", {"active": True})
        for action in expected:
            request(args.base_url, f"/api/v1/sessions/{sid}/action", action)
        finished = request(args.base_url, f"/api/v1/sessions/{sid}/finish", {})
        if not finished.get("result", {}).get("success"):
            raise RuntimeError(f"{case.id} demonstration failed validation")

        deadline = time.monotonic() + args.timeout
        while finished.get("video_status") not in {"ready", "error"}:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{case.id} video render timed out")
            time.sleep(1)
            finished = request(args.base_url, f"/api/v1/sessions/{sid}")
        if finished["video_status"] == "error":
            raise RuntimeError(f"{case.id} render failed: {finished.get('video_error')}")

        video_name = Path(finished["video_url"]).name
        video_path = ROOT / "data" / "videos" / video_name
        digest = hashlib.sha256(video_path.read_bytes()).hexdigest()
        entries.append({
            "case_id": case.id,
            "rule": args.rule,
            "seed": seed,
            "episode_id": sid,
            "video": f"data/videos/{video_name}",
            "sha256": digest,
            "bytes": video_path.stat().st_size,
            "actions": len(expected),
        })
        print(f"[{index + 1:02d}/{len(CASES)}] {case.id}: {video_name}", flush=True)

    manifest = {
        "name": args.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "One clean 1280x720 rendered ICL demonstration per OS case.",
        "rule": args.rule,
        "case_count": len(entries),
        "video_format": "WebM",
        "resolution": [1280, 720],
        "entries": entries,
    }
    output = target_dir / f"{args.name}.json"
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest: {output}", flush=True)


if __name__ == "__main__":
    main()

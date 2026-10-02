#!/usr/bin/env python3
"""Audit a computer-use recording queue and emit its immutable manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height:format=duration",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(completed.stdout)
    stream = data["streams"][0]
    return {
        "codec": stream["codec_name"],
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "duration_seconds": round(float(data["format"]["duration"]), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    queue_path = args.queue if args.queue.is_absolute() else repo / args.queue
    manifest_path = args.manifest if args.manifest.is_absolute() else repo / args.manifest
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    manifest_entries = []
    errors = []

    for entry in queue["entries"]:
        episode_path = repo / "data" / "episodes" / f"{entry['episode_id']}.json"
        session = json.loads(episode_path.read_text(encoding="utf-8"))
        result = session.get("result") or {}
        if session.get("episode", {}).get("benchmark_version") != "1.0.0":
            errors.append(f"{entry['episode_id']}: wrong benchmark version")
            continue
        video_name = session.get("video")
        video_path = repo / "data" / "videos" / (video_name or "missing")
        if session.get("status") != "finished" or not result.get("success"):
            errors.append(f"{entry['episode_id']}: unsuccessful trajectory")
            continue
        if session.get("video_status") != "ready" or not video_name or not video_path.is_file():
            errors.append(f"{entry['episode_id']}: video {session.get('video_status')}")
            continue
        media = probe(video_path)
        if (media["width"], media["height"]) != (1280, 720) or media["duration_seconds"] <= 0:
            errors.append(f"{entry['episode_id']}: invalid media {media}")
            continue
        digest = hashlib.sha256(video_path.read_bytes()).hexdigest()
        entry["status"] = "complete"
        entry["video"] = f"data/videos/{video_name}"
        manifest_entries.append(
            {
                "case_id": entry["case_id"],
                "rule": entry["rule"],
                "seed": entry["seed"],
                "episode_id": entry["episode_id"],
                "video": f"data/videos/{video_name}",
                "sha256": digest,
                "bytes": video_path.stat().st_size,
                "actions": len(session["actions"]),
                **media,
            }
        )

    if errors:
        raise SystemExit("audit failed:\n" + "\n".join(errors[:20]) + (f"\n... {len(errors)} errors" if len(errors) > 20 else ""))

    pairs = {(item["case_id"], item["rule"]) for item in manifest_entries}
    rules = Counter(item["rule"] for item in manifest_entries)
    if len(manifest_entries) != 108 or len(pairs) != 108 or rules != Counter({0: 36, 1: 36, 2: 36}):
        raise SystemExit(f"coverage audit failed: entries={len(manifest_entries)}, pairs={len(pairs)}, rules={rules}")

    queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "name": manifest_path.stem,
        "benchmark_version": "1.0.0",
        "episode_schema_version": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Computer-use recorded demonstrations for every OS-ICL case and hidden rule.",
        "case_count": 36,
        "rule_count": 3,
        "entry_count": 108,
        "rule_distribution": {str(rule): count for rule, count in sorted(rules.items())},
        "video_format": "WebM",
        "resolution": [1280, 720],
        "entries": manifest_entries,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"audited {len(manifest_entries)} videos; wrote {manifest_path}")


if __name__ == "__main__":
    main()

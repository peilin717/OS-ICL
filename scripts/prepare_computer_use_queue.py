#!/usr/bin/env python3
"""Create a deterministic, resumable queue for computer-use demo recording."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cases import CASES


def post_json(url: str, body: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8790")
    parser.add_argument("--seed-base", type=int, default=480_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    entries = []
    for case_index, case in enumerate(CASES):
        for rule in range(3):
            seed = args.seed_base + case_index * 3 + rule
            payload = post_json(
                f"{args.base_url}/api/v1/sessions",
                {"case_id": case.id, "mode": "demo", "rule": rule, "seed": seed},
            )
            entries.append(
                {
                    "case_id": case.id,
                    "rule": rule,
                    "seed": seed,
                    "episode_id": payload["id"],
                    "launch_url": f"{args.base_url}{payload['launch_url']}",
                    "expected": payload["case"].get("expected", []),
                    "status": "pending",
                }
            )

    # Expected actions are intentionally read from the persisted private episode,
    # not exposed by the public API used by evaluation agents.
    repo = Path(__file__).resolve().parents[1]
    for entry in entries:
        episode = json.loads((repo / "data" / "episodes" / f"{entry['episode_id']}.json").read_text())
        entry["expected"] = episode["episode"]["expected"]

    document = {
        "schema_version": 1,
        "benchmark_version": "1.0.0",
        "kind": "computer-use-recording-queue",
        "base_url": args.base_url,
        "seed_base": args.seed_base,
        "count": len(entries),
        "entries": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"created {len(entries)} queued demos at {args.output}")


if __name__ == "__main__":
    main()

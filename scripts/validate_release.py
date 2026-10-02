#!/usr/bin/env python3
"""Validate an OS-ICL release manifest and its local video artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"release validation failed: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--allow-missing-videos", action="store_true")
    args = parser.parse_args()
    path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])

    if manifest.get("benchmark_version") != "1.0.0":
        fail("benchmark_version must be 1.0.0")
    if len(entries) != 108:
        fail(f"expected 108 entries, found {len(entries)}")
    pairs = [(entry.get("case_id"), entry.get("rule")) for entry in entries]
    if len(set(pairs)) != 108:
        fail("case-rule pairs are not unique")
    if Counter(rule for _, rule in pairs) != Counter({0: 36, 1: 36, 2: 36}):
        fail("rule distribution is not 36/36/36")
    if len({entry.get("episode_id") for entry in entries}) != 108:
        fail("episode IDs are not unique")

    checked = 0
    for entry in entries:
        video = ROOT / entry["video"]
        if not video.is_file():
            if args.allow_missing_videos:
                continue
            fail(f"missing video: {video}")
        digest = hashlib.sha256(video.read_bytes()).hexdigest()
        if digest != entry.get("sha256"):
            fail(f"checksum mismatch: {video}")
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,width,height:format=duration", "-of", "json", str(video)],
            check=True, capture_output=True, text=True,
        )
        media = json.loads(probe.stdout)
        stream = media["streams"][0]
        if (int(stream["width"]), int(stream["height"])) != (1280, 720):
            fail(f"invalid resolution: {video}")
        if float(media["format"]["duration"]) <= 0:
            fail(f"invalid duration: {video}")
        checked += 1

    print(f"valid OS-ICL 1.0.0 release: entries=108 videos_checked={checked}")


if __name__ == "__main__":
    main()

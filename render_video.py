#!/usr/bin/env python3
"""Render a completed semantic trajectory to WebM without screen capture."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright


def render(session_id: str, base_url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    query = urlencode({"session": session_id, "replay": "1"})
    url = f"{base_url.rstrip('/')}/?{query}"
    with tempfile.TemporaryDirectory(prefix="vibe-replay-") as temp:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/usr/bin/google-chrome",
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                device_scale_factor=1,
                locale="en-US",
                record_video_dir=temp,
                record_video_size={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_function("window.__REPLAY_DONE__ === true", timeout=120_000)
            video = page.video
            context.close()
            if video is None:
                browser.close()
                raise RuntimeError("Playwright did not create a video artifact")
            source = Path(video.path())
            browser.close()
            shutil.move(str(source), str(output))
    if not output.exists() or output.stat().st_size < 1_000:
        raise RuntimeError("rendered video is missing or unexpectedly small")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    render(args.session, args.base_url, args.output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dependency-light API and static server for Vibe OS-ICL."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import secrets
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cases import CASES, CASE_BY_ID, available_actions, generate_episode

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
EPISODES = DATA / "episodes"
VIDEOS = DATA / "videos"
for directory in (EPISODES, VIDEOS):
    directory.mkdir(parents=True, exist_ok=True)

SESSIONS: dict[str, dict] = {}
LOCK = threading.RLock()


def now_ms() -> int:
    return int(time.time() * 1000)


def state_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


def persist(session: dict) -> None:
    path = EPISODES / f"{session['id']}.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def public_session(session: dict) -> dict:
    episode = session["episode"]
    payload = {
        "id": session["id"], "mode": session["mode"], "status": session["status"],
        "created_at": session["created_at"], "case": episode["case"],
        "external_task_id": session.get("external_task_id"), "external_user_id": session.get("external_user_id"),
        "seed": episode["seed"], "items": episode["items"], "clues": episode["clues"],
        "actions": session["actions"], "available_actions": available_actions(episode["case"]["id"]),
        "recording": session.get("recording", False), "result": session.get("result"),
        "video_url": f"/artifacts/{session['video']}" if session.get("video") else None,
        "state_hash": state_hash({"items": episode["items"], "seed": episode["seed"]}),
    }
    if session["mode"] == "demo":
        payload["recorder_brief"] = episode["rule_text"]
        payload["rule"] = episode["rule"]
    if session["mode"] == "evaluation":
        payload["demonstrations"] = find_demos(episode["case"]["id"], episode["rule"])
    return payload


def normalised(actions: list[dict]) -> list[dict]:
    return [{"verb": str(a.get("verb", "")), "target": str(a.get("target", ""))} for a in actions]


def evaluate(session: dict) -> dict:
    expected = normalised(session["episode"]["expected"])
    actual = normalised(session["actions"])
    family = session["episode"]["case"]["family"]
    invalid = sum(1 for a in actual if not a["verb"] or not a["target"])
    if family == "selection_set":
        expected_submit = expected[-1:]
        actual_submit = [a for a in actual if a["verb"] == "submit"][-1:]
        expected_body = {(a["verb"], a["target"]) for a in expected if a["verb"] != "submit"}
        # Repeated toggles cancel, mirroring the UI selection state.
        toggled: set[tuple[str, str]] = set()
        for a in actual:
            if a["verb"] == "toggle":
                key = (a["verb"], a["target"])
                toggled.symmetric_difference_update({key})
        success = toggled == expected_body and actual_submit == expected_submit
        trajectory = 1.0 if success else 0.0
    elif family in {"mapping", "recovery", "cross_app", "selection"}:
        success = len(actual) == len(expected) and {(a["verb"], a["target"]) for a in actual} == {(a["verb"], a["target"]) for a in expected}
        trajectory = 1.0 if actual == expected else (1.0 if success and family != "selection" else 0.0)
    else:
        success = actual == expected
        prefix = 0
        for left, right in zip(actual, expected):
            if left != right: break
            prefix += 1
        trajectory = prefix / max(1, len(expected))
    expected_pairs = {(a["verb"], a["target"]) for a in expected}
    side_effects = [a for a in actual if (a["verb"], a["target"]) not in expected_pairs and a["verb"] != "submit"]
    return {
        "success": bool(success), "goal_success": bool(success),
        "rule_compliance": bool(success), "trajectory_compliance": round(trajectory, 3),
        "side_effect_free": not side_effects, "invalid_actions": invalid,
        "agent_steps": len(actual), "optimal_steps": len(expected),
        "expected_count": len(expected), "side_effect_count": len(side_effects),
    }


def find_demos(case_id: str, rule: int) -> list[dict]:
    demos = []
    for path in sorted(EPISODES.glob("*.json"), reverse=True):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ep = item.get("episode", {})
        result = item.get("result") or {}
        if item.get("mode") == "demo" and result.get("success") and ep.get("case", {}).get("id") == case_id and ep.get("rule") == rule:
            video = item.get("video")
            demos.append({"episode_id": item["id"], "seed": ep["seed"], "video_url": f"/artifacts/{video}" if video else None})
        if len(demos) == 4:
            break
    return demos


class Handler(BaseHTTPRequestHandler):
    server_version = "VibeOS/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def send_json(self, value: object, status: int = 200) -> None:
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 5_000_000:
            raise ValueError("request too large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json({"ok": True, "service": "vibe-os-icl", "cases": len(CASES)})
        if parsed.path == "/api/v1/cases":
            return self.send_json({"cases": [c.public() for c in CASES]})
        if parsed.path.startswith("/api/v1/sessions/"):
            sid = parsed.path.rsplit("/", 1)[-1]
            with LOCK:
                session = SESSIONS.get(sid)
                if not session:
                    saved = EPISODES / f"{sid}.json"
                    if saved.exists():
                        session = json.loads(saved.read_text(encoding="utf-8")); SESSIONS[sid] = session
            return self.send_json(public_session(session), 200) if session else self.send_json({"error": "session not found"}, 404)
        if parsed.path == "/api/v1/demos":
            q = parse_qs(parsed.query)
            case_id = q.get("case_id", [""])[0]
            rule = int(q.get("rule", ["0"])[0])
            return self.send_json({"demos": find_demos(case_id, rule)})
        if parsed.path.startswith("/artifacts/"):
            name = Path(parsed.path[len("/artifacts/"):]).name
            return self.serve_file(VIDEOS / name)
        path = STATIC / ("index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/"))
        return self.serve_file(path)

    def serve_file(self, path: Path) -> None:
        try:
            resolved = path.resolve()
            if STATIC.resolve() not in resolved.parents and VIDEOS.resolve() not in resolved.parents:
                raise FileNotFoundError
            data = resolved.read_bytes()
        except OSError:
            return self.send_error(404)
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/v1/sessions":
                return self.create_session(self.read_json())
            if parsed.path.startswith("/api/v1/sessions/"):
                parts = parsed.path.strip("/").split("/")
                if len(parts) != 5:
                    return self.send_json({"error": "invalid endpoint"}, 404)
                sid, command = parts[3], parts[4]
                return self.session_command(sid, command)
            if parsed.path.startswith("/api/v1/videos/"):
                sid = Path(parsed.path).name
                return self.upload_video(sid)
            return self.send_json({"error": "not found"}, 404)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            return self.send_json({"error": str(exc)}, 400)
        except Exception as exc:  # keep standalone service diagnosable
            return self.send_json({"error": f"internal error: {exc}"}, 500)

    def create_session(self, body: dict) -> None:
        case_id = body.get("case_id", "OS-SEL-01")
        if case_id not in CASE_BY_ID:
            raise ValueError("unknown case_id")
        mode = body.get("mode", "evaluation")
        if mode not in {"demo", "evaluation", "practice"}:
            raise ValueError("mode must be demo, evaluation, or practice")
        seed = int(body.get("seed", secrets.randbelow(900_000) + 100_000))
        requested_rule = body.get("rule")
        rule = int(requested_rule) if requested_rule is not None else secrets.randbelow(3)
        if rule not in range(3):
            raise ValueError("rule must be 0, 1, or 2")
        sid = "vos_" + secrets.token_hex(8)
        session = {
            "id": sid, "mode": mode, "status": "active", "created_at": now_ms(),
            "external_task_id": body.get("external_task_id"), "external_user_id": body.get("external_user_id"),
            "episode": generate_episode(case_id, rule, seed), "actions": [], "recording": False,
            "video": None, "result": None,
        }
        with LOCK:
            SESSIONS[sid] = session; persist(session)
        payload = public_session(session)
        payload["launch_url"] = f"/?session={sid}"
        self.send_json(payload, 201)

    def session_command(self, sid: str, command: str) -> None:
        with LOCK:
            session = SESSIONS.get(sid)
            if not session:
                return self.send_json({"error": "session not found"}, 404)
            if command == "action":
                if session["status"] != "active":
                    return self.send_json({"error": "session is not active"}, 409)
                body = self.read_json()
                action = {"verb": str(body.get("verb", "")), "target": str(body.get("target", "")), "at": now_ms()}
                session["actions"].append(action)
            elif command == "recording":
                body = self.read_json(); session["recording"] = bool(body.get("active"))
            elif command == "reset":
                session["actions"] = []; session["status"] = "active"; session["result"] = None
            elif command == "finish":
                session["status"] = "finished"; session["recording"] = False
                session["result"] = evaluate(session); session["result"]["finished_at"] = now_ms()
            else:
                return self.send_json({"error": "unknown command"}, 404)
            persist(session)
            self.send_json(public_session(session))

    def upload_video(self, sid: str) -> None:
        with LOCK:
            session = SESSIONS.get(sid)
            if not session:
                return self.send_json({"error": "session not found"}, 404)
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 500_000_000:
            return self.send_json({"error": "invalid video size"}, 400)
        extension = ".webm" if "webm" in self.headers.get("Content-Type", "") else ".bin"
        name = sid + extension
        target = VIDEOS / name
        target.write_bytes(self.rfile.read(length))
        with LOCK:
            session["video"] = name; persist(session)
        self.send_json({"ok": True, "video_url": f"/artifacts/{name}"}, 201)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Vibe OS-ICL simulator")
    parser.add_argument("--host", default=os.environ.get("VIBE_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("VIBE_PORT", "8790")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Vibe OS-ICL running at http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

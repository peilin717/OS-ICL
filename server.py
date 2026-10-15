#!/usr/bin/env python3
"""Deterministic desktop service and versioned OS-ICL authoring API."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import secrets
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cases import BENCHMARK_VERSION, CASES, CASE_BY_ID, available_actions, generate_episode
import workflows

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
EPISODES = DATA / "episodes"
VIDEOS = DATA / "videos"
RENDER_TEMP = DATA / "render-temp"
for directory in (EPISODES, VIDEOS, RENDER_TEMP):
    directory.mkdir(parents=True, exist_ok=True)

SESSIONS: dict[str, dict] = {}
LOCK = threading.RLock()
RENDER_JOBS = {}
PUBLIC_BASE_URL = os.environ.get("OS_ICL_PUBLIC_URL", os.environ.get("VIBE_PUBLIC_URL", "http://127.0.0.1:8790"))
RENDER_CONCURRENCY = max(1, int(os.environ.get("OS_ICL_RENDER_CONCURRENCY", os.environ.get("VIBE_RENDER_CONCURRENCY", "3"))))
RENDER_SLOTS = threading.Semaphore(RENDER_CONCURRENCY)


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
        "workflow": episode.get("workflow"),
        "actions": session["actions"], "available_actions": available_actions(episode["case"]["id"]),
        "recording": session.get("recording", False), "result": session.get("result"),
        "video_url": f"/artifacts/{session['video']}" if session.get("video") else None,
        "video_status": session.get("video_status"), "video_error": session.get("video_error"),
        "state_hash": state_hash({"items": episode["items"], "seed": episode["seed"]}),
        "benchmark_version": episode.get("benchmark_version", BENCHMARK_VERSION),
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
    elif family in {"mapping", "selection"}:
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
        video = item.get("video")
        video_ready = bool(video) and (VIDEOS / Path(video).name).is_file() and item.get("video_status") in {None, "ready"}
        if item.get("mode") == "demo" and result.get("success") and video_ready and ep.get("benchmark_version") == BENCHMARK_VERSION and ep.get("case", {}).get("id") == case_id and ep.get("rule") == rule:
            demos.append({"episode_id": item["id"], "seed": ep["seed"], "video_url": f"/artifacts/{video}"})
        if len(demos) == 4:
            break
    return demos


def schedule_video_render(session_id: str, generation: int) -> None:
    """Render a successful semantic trajectory in an isolated browser.

    The worker visits the replay-only page, which contains neither the recorder
    brief nor evaluation controls. No display-capture permission is required.
    """
    def work() -> None:
        output = RENDER_TEMP / f"{session_id}-{generation}.webm"
        final_output = VIDEOS / f"{session_id}.webm"
        command = [
            sys.executable, str(ROOT / "render_video.py"),
            "--session", session_id, "--base-url", PUBLIC_BASE_URL,
            "--output", str(output),
        ]
        with RENDER_SLOTS:
            try:
                with LOCK:
                    session = SESSIONS.get(session_id)
                    if not session or session.get("render_generation") != generation:
                        return
                    session["video_status"] = "rendering"
                    persist(session)
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=600)
                if completed.returncode != 0:
                    raise RuntimeError((completed.stderr or completed.stdout or "video renderer failed")[-2000:])
                with LOCK:
                    session = SESSIONS.get(session_id)
                    if session and session.get("render_generation") == generation and session.get("status") == "finished":
                        output.replace(final_output)
                        session["video"] = final_output.name
                        session["video_status"] = "ready"
                        session["video_error"] = None
                        if session.get("engine")=="v2":
                            session["video_provenance"]=workflows.artifact_provenance.video_metadata(session)
                        persist(session)
                    else:
                        output.unlink(missing_ok=True)
            except Exception as exc:
                output.unlink(missing_ok=True)
                with LOCK:
                    session = SESSIONS.get(session_id)
                    if session and session.get("render_generation") == generation:
                        session["video_status"] = "error"
                        session["video_error"] = str(exc)
                        persist(session)

    worker=threading.Thread(target=work, name=f"video-{session_id}", daemon=True)
    with LOCK:
        RENDER_JOBS[session_id]=worker
        worker.start()


class Handler(BaseHTTPRequestHandler):
    server_version = "OSICL/2.0"

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
        if parsed.path == "/api/v2/cases":
            return self.send_json({"benchmark_version": workflows.VERSION,
                "cases": [{k: v for k, v in c.items() if k not in {"pipeline", "recovery"}} for c in workflows.CASES]})
        if parsed.path.startswith("/api/v2/sessions/"):
            sid = parsed.path.rsplit("/", 1)[-1]
            with LOCK:
                session = SESSIONS.get(sid)
                if session is None and (EPISODES / f"{sid}.json").is_file():
                    session = json.loads((EPISODES / f"{sid}.json").read_text())
                    if session.get('video_status') in {'queued','rendering'}:
                        session['video_status']='interrupted'
                        persist(session)
                    SESSIONS[sid] = session
                if session is None or session.get("engine") != "v2":
                    return self.send_json({"error": "session not found"}, 404)
                return self.send_json(self.v2_payload(session))
        if parsed.path == "/api/health":
            return self.send_json({"ok": True, "service": "os-icl-bench", "benchmark_version": workflows.VERSION,
                                   "cases": len(workflows.CASES), "legacy_version": BENCHMARK_VERSION, "legacy_cases": len(CASES)})
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
            return self.send_json(public_session(session), 200) if session and session.get("engine") != "v2" else self.send_json({"error": "session not found"}, 404)
        if parsed.path == "/api/v1/demos":
            q = parse_qs(parsed.query)
            case_id = q.get("case_id", [""])[0]
            rule = int(q.get("rule", ["0"])[0])
            return self.send_json({"demos": find_demos(case_id, rule)})
        if parsed.path.startswith("/artifacts/"):
            name = Path(parsed.path[len("/artifacts/"):]).name
            return self.serve_file(VIDEOS / name)
        path = STATIC / ("index.html" if parsed.path in {"", "/", "/studio", "/legacy"} else parsed.path.lstrip("/"))
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
            if parsed.path == "/api/v2/sessions":
                return self.v2_create(self.read_json())
            if parsed.path.startswith("/api/v2/sessions/"):
                parts = parsed.path.strip("/").split("/")
                if len(parts) != 5:
                    return self.send_json({"error": "invalid endpoint"}, 404)
                return self.v2_command(parts[3], parts[4], self.read_json())
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

    def v2_payload(self, session):
        result = workflows.public(session["episode"], session["mode"])
        result.update(id=session["id"], mode=session["mode"], status=session["status"],
                      launch_url=f"/?session={session['id']}", video_status=session.get("video_status"),
                      video_url=f"/artifacts/{session['video']}" if session.get("video") else None,
                      video_error=session.get("video_error"), result=session.get("result"),
                      external_task_id=session.get("external_task_id"))
        result['compatible']=self.v2_compatible(session)
        return result

    @staticmethod
    def v2_compatible(session):
        episode=session['episode']
        return (episode.get('benchmark_version')==workflows.VERSION and
                episode.get('schema_version')==workflows.SCHEMA_VERSION and
                episode.get('implementation',{}).get('fingerprint')==workflows.IMPLEMENTATION['fingerprint'])

    def v2_create(self, body):
        mode = body.get("mode", "evaluation")
        if mode not in {"evaluation", "demo", "practice"}:
            raise ValueError("invalid session mode")
        # Rule assignment belongs to the runner, not to the visual agent.
        episode = workflows.generate(body.get("case_id", "OS-LH-01"),
            int(body.get("convention", secrets.randbelow(3))), int(body.get("seed", secrets.randbelow(1_000_000))),body.get('plan_variant','standard'))
        session = {"id": "osl_" + secrets.token_hex(8), "engine": "v2", "mode": mode,
                   "status": "active", "created_at": now_ms(), "episode": episode,
                   "ui_events": [], "actions": [], "result": None, "video": None,
                   "external_task_id": body.get("external_task_id"),
                   "external_user_id": body.get("external_user_id")}
        with LOCK:
            SESSIONS[session["id"]] = session
            persist(session)
        self.send_json(self.v2_payload(session), 201)

    def v2_command(self, sid, command, body):
        should_render = False
        with LOCK:
            session = SESSIONS.get(sid)
            if session is None and (EPISODES / f"{sid}.json").is_file():
                session = json.loads((EPISODES / f"{sid}.json").read_text())
                if session.get('video_status') in {'queued','rendering'}:
                    session['video_status']='interrupted'
                    persist(session)
                SESSIONS[sid] = session
            if session is None or session.get("engine") != "v2":
                return self.send_json({"error": "session not found"}, 404)
            compatible=self.v2_compatible(session)
            if not compatible and command != "reset":
                return self.send_json({"error":"This episode belongs to an earlier development version. Create a new episode or reset it before continuing."},409)
            if command in {"action", "ui-event"} and session["status"] != "active":
                return self.send_json({"error": "session is not active"}, 409)
            if command == "action":
                event = workflows.transition(session["episode"], body)
                event["at"] = now_ms()
                session["actions"].append(event)
                payload = self.v2_payload(session)
                payload["last_event"] = event
            elif command == "ui-event":
                if len(session["ui_events"]) >= 20000:
                    raise ValueError("interaction trace is too large")
                if body.get("type") not in {"click", "dblclick", "contextmenu", "change", "input", "submit", "keydown", "drag", "scroll"}:
                    raise ValueError("invalid interaction type")
                session["ui_events"].append({**body, "at": now_ms()})
                payload = {"ok": True}
            elif command == "reset":
                if not compatible:
                    old=session["episode"]
                    session["episode"]=workflows.generate(old["case"]["id"],old["convention"],old["seed"],old.get('plan_variant','standard'))
                session["episode"]["state"] = json.loads(json.dumps(session["episode"]["initial"]))
                session["episode"]["events"] = []
                session.update(status="active", actions=[], ui_events=[], result=None, video=None,
                               video_status=None, video_error=None)
                session["render_generation"] = int(session.get("render_generation", 0)) + 1
                payload = self.v2_payload(session)
            elif command == "finish":
                if session["status"] != "finished":
                    session.update(status="finished", result=workflows.evaluate(session["episode"]))
                if session["mode"] == "demo" and session["result"]["success"] and session["ui_events"] and not session.get("video") and session.get("video_status") not in {"queued", "rendering"}:
                    session["render_generation"] = int(session.get("render_generation", 0)) + 1
                    session["video_status"] = "queued"
                    should_render = True
                payload = self.v2_payload(session)
            elif command == "replay":
                if session["mode"] != "demo" or not (session.get("result") or {}).get("success"):
                    return self.send_json({"error": "only successful demonstrations can be replayed"}, 403)
                workflows.artifact_provenance.assert_unchanged(session['episode']['implementation'])
                import copy
                clone = copy.deepcopy(session)
                clone.update(id="osl_" + secrets.token_hex(8), mode="practice", status="active", actions=[], ui_events=[], result=None, video=None)
                clone["episode"]["state"] = copy.deepcopy(clone["episode"]["initial"])
                clone["episode"]["events"] = []
                SESSIONS[clone["id"]] = clone
                payload = {"session": self.v2_payload(clone), "trace": session["ui_events"],
                           "expected_hash": workflows.digest(session["episode"]["state"])}
            else:
                return self.send_json({"error": "unknown command"}, 404)
            persist(session)
        if should_render:
            schedule_video_render(sid, session["render_generation"])
        self.send_json(payload)

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
        should_render = False
        render_generation = 0
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
                session["recording"] = False; session["video"] = None
                session["video_status"] = None; session["video_error"] = None
                session["render_generation"] = int(session.get("render_generation", 0)) + 1
            elif command == "finish":
                if session["status"] != "finished":
                    session["status"] = "finished"; session["recording"] = False
                    session["result"] = evaluate(session); session["result"]["finished_at"] = now_ms()
                # A repeated finish request retries a failed or interrupted render
                # without mutating the already-verified action trajectory.
                if session["mode"] == "demo" and session["result"]["success"] and not session.get("video") and session.get("video_status") not in {"queued", "rendering"}:
                    session["render_generation"] = int(session.get("render_generation", 0)) + 1
                    render_generation = session["render_generation"]
                    session["video_status"] = "queued"
                    session["video_error"] = None
                    should_render = True
            else:
                return self.send_json({"error": "unknown command"}, 404)
            persist(session)
            payload = public_session(session)
        if should_render:
            schedule_video_render(sid, render_generation)
        self.send_json(payload)

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
            session["render_generation"] = int(session.get("render_generation", 0)) + 1
            session["video"] = name
            session["video_status"] = "ready"
            session["video_error"] = None
            session["video_provenance"] = None
            persist(session)
        self.send_json({"ok": True, "video_url": f"/artifacts/{name}"}, 201)


def main() -> None:
    global PUBLIC_BASE_URL
    parser = argparse.ArgumentParser(description="Run the OS-ICL desktop simulator")
    parser.add_argument("--host", default=os.environ.get("OS_ICL_HOST", os.environ.get("VIBE_HOST", "0.0.0.0")))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OS_ICL_PORT", os.environ.get("VIBE_PORT", "8790"))))
    args = parser.parse_args()
    PUBLIC_BASE_URL = os.environ.get("OS_ICL_PUBLIC_URL", os.environ.get("VIBE_PUBLIC_URL", f"http://127.0.0.1:{args.port}"))
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"OS-ICL Desktop running at http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

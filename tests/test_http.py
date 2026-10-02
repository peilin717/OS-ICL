import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import Handler, SESSIONS, VIDEOS


def request(base, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return response.status, json.loads(response.read())


def test_http_lifecycle_and_hidden_rule_boundary():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, health = request(base, "/api/health")
        assert status == 200 and health["cases"] == 36
        status, created = request(base, "/api/v1/sessions", {"case_id": "OS-SEL-01", "mode": "evaluation", "seed": 123, "rule": 0})
        assert status == 201
        assert "rule" not in created and "recorder_brief" not in created
        assert created["benchmark_version"] == "1.0.0"
        sid = created["id"]
        expected = SESSIONS[sid]["episode"]["expected"]
        for action in expected:
            status, _ = request(base, f"/api/v1/sessions/{sid}/action", action)
            assert status == 200
        status, finished = request(base, f"/api/v1/sessions/{sid}/finish", {})
        assert status == 200 and finished["result"]["success"]
        video_bytes = b"webm-test-fixture"
        upload = urllib.request.Request(base + f"/api/v1/videos/{sid}", data=video_bytes, headers={"Content-Type": "video/webm"}, method="POST")
        with urllib.request.urlopen(upload) as response:
            uploaded = json.loads(response.read())
        assert uploaded["video_url"].endswith(".webm")
        with urllib.request.urlopen(base + uploaded["video_url"]) as response:
            assert response.read() == video_bytes
        status, reset = request(base, f"/api/v1/sessions/{sid}/reset", {})
        assert status == 200
        assert reset["status"] == "active"
        assert reset["video_url"] is None
        assert reset["video_status"] is None
        (VIDEOS / f"{sid}.webm").unlink(missing_ok=True)
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_desktop_and_studio_static_routes_are_served():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base + "/") as response:
            index = response.read().decode()
        assert "/os-shell.css" in index and "/app.js" in index
        with urllib.request.urlopen(base + "/studio") as response:
            assert response.status == 200
        with urllib.request.urlopen(base + "/os-shell.js") as response:
            shell = response.read().decode()
        assert "mountOs" in shell
        assert "data-drag-window" in shell
        assert "data-files-location" in shell
        assert "data-settings-section" in shell
        with urllib.request.urlopen(base + "/app.js") as response:
            app = response.read().decode()
        assert "source-cards" in app
        assert "outcome" in app
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)

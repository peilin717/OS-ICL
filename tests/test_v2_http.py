import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import workflows


def request(base, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base+path, data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def test_v2_external_lifecycle_and_privacy():
    http = ThreadingHTTPServer(("127.0.0.1",0), server.Handler)
    thread = threading.Thread(target=http.serve_forever,daemon=True)
    thread.start()
    base=f"http://127.0.0.1:{http.server_port}"
    try:
        catalogue=request(base,"/api/v2/cases")
        assert len(catalogue["cases"])==12
        assert all("pipeline" not in c and "recovery" not in c for c in catalogue["cases"])
        created=request(base,"/api/v2/sessions",{"case_id":"OS-LH-08","seed":4201,"mode":"evaluation","convention":2,"external_task_id":"external-42"})
        assert created["external_task_id"]=="external-42"
        assert not {"convention","recorder_brief","reference","pipeline"}.intersection(created)
        assert "pipeline" not in created["case"]
        sid=created["id"]
        rejected=request(base,f"/api/v2/sessions/{sid}/action",{"op":"copy","target":"source-0","parent":"documents"})
        assert not rejected["last_event"]["accepted"]
        reset=request(base,f"/api/v2/sessions/{sid}/reset",{})
        assert reset["state_hash"]==created["state_hash"]
        for action in server.SESSIONS[sid]["episode"]["reference"]:
            request(base,f"/api/v2/sessions/{sid}/action",action)
        completed=request(base,f"/api/v2/sessions/{sid}/finish",{})
        assert completed["result"]["success"]
        try:
            request(base,f"/api/v2/sessions/{sid}/action",{"op":"delete","target":"source-0"})
            assert False,"finished sessions must reject mutations"
        except urllib.error.HTTPError as exc:
            assert exc.code==409
        server.SESSIONS.pop(sid)
        restored=request(base,f"/api/v2/sessions/{sid}")
        assert restored["state_hash"]==completed["state_hash"]
        again=request(base,f"/api/v2/sessions/{sid}/reset",{})
        assert again["state_hash"]==created["state_hash"]
        server.SESSIONS[sid]['episode']['benchmark_version']='2.0.0-dev'
        server.persist(server.SESSIONS[sid])
        try:
            request(base,f"/api/v2/sessions/{sid}/action",{"op":"properties","target":"source-0"})
            assert False,'old development episodes must not execute against new reducers'
        except urllib.error.HTTPError as exc:
            assert exc.code==409
        upgraded=request(base,f"/api/v2/sessions/{sid}/reset",{})
        assert upgraded['benchmark_version']==workflows.VERSION and upgraded['state_hash']==created['state_hash']
    finally:
        http.shutdown();http.server_close();thread.join(timeout=2)

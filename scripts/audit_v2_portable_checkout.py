#!/usr/bin/env python3
"""Smoke-test a source-only checkout with spaces using the active interpreter.

No package installation, model calls, or modification of the working checkout.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import artifact_provenance


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    implementation=artifact_provenance.capture()
    with tempfile.TemporaryDirectory(prefix='os-icl-portable-') as task_temp:
        task_root=Path(task_temp)
        checkout=task_root/'checkout with spaces'
        checkout.mkdir()
        for path in ROOT.glob('*.py'):shutil.copy2(path,checkout/path.name)
        for name in ['run.sh','test.sh','CITATION.cff']:shutil.copy2(ROOT/name,checkout/name)
        for name in ['static','scripts','tests']:
            shutil.copytree(ROOT/name,checkout/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        legacy_manifest=Path('data/manifests/os-icl-1.0.0.json')
        (checkout/legacy_manifest).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/legacy_manifest,checkout/legacy_manifest)
        # Explicit interpreter takes precedence even if the caller has a
        # historical Conda configuration. No personal path is in the wrappers.
        env=dict(os.environ,OS_ICL_PYTHON=sys.executable)
        help_text=subprocess.check_output([str(checkout/'run.sh'),'--help'],
                                          cwd=task_root,env=env,timeout=15).decode()
        if 'OS-ICL desktop simulator' not in help_text or 'Vibe' in help_text:
            raise RuntimeError('Portable launch help does not describe the current desktop.')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        service=subprocess.Popen([str(checkout/'run.sh'),'--host','127.0.0.1','--port',str(port)],
                                 cwd=task_root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        def request(path,body=None):
            raw=json.dumps(body).encode() if body is not None else None
            req=urllib.request.Request(base+path,data=raw,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=5) as response:return json.load(response)
        try:
            deadline=time.monotonic()+10
            while True:
                try:
                    health=request('/api/health');break
                except urllib.error.URLError:
                    if service.poll() is not None or time.monotonic()>deadline:
                        detail=service.stdout.read().decode() if service.poll() is not None else 'Health endpoint startup timeout'
                        raise RuntimeError('Portable service did not start: '+detail)
                    time.sleep(.1)
            if not health['ok'] or health['cases']!=12:raise RuntimeError('Wrong portable service catalogue.')
            catalogue=request('/api/v2/cases')
            if len(catalogue['cases'])!=12:raise RuntimeError('Incomplete portable task catalogue.')
            created=request('/api/v2/sessions',{'case_id':'OS-LH-09','convention':2,'seed':173,'mode':'evaluation'})
            if not created['compatible'] or {'reference','recorder_brief','convention'}.intersection(created):
                raise RuntimeError('Portable query compatibility/privacy failure.')
            reset=request(f"/api/v2/sessions/{created['id']}/reset",{})
            if reset['state_hash']!=created['state_hash']:raise RuntimeError('Portable reset mismatch.')
            saved=json.loads((checkout/'data/episodes'/f"{created['id']}.json").read_text())
            if saved['episode']['implementation']!=implementation:raise RuntimeError('Copied sources differ from the original implementation.')
        finally:
            service.terminate()
            try:service.wait(timeout=5)
            except subprocess.TimeoutExpired:service.kill();service.wait(timeout=5)
        tests=subprocess.check_output([str(checkout/'test.sh'),'-k','session_compatibility or export_audit_privacy'],
                                      cwd=task_root,env=env,timeout=45).decode()
        if '14 passed' not in tests:raise RuntimeError('Portable wrapper regression failed: '+tests)
    artifact_provenance.assert_unchanged(implementation)
    report={'schema_version':1,'status':'passed','implementation_fingerprint':implementation['fingerprint'],
            'checkout_path_with_spaces':True,'launched_outside_checkout':True,
            'http_catalogue_query_reset':True,'wrapper_tests_passed':14,
            'dependency_scope':'existing active interpreter; not a fresh dependency installation',
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'wrapper_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['run.sh','test.sh']}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({key:value for key,value in report.items() if key not in {'wrapper_sha256','script_sha256'}}))


if __name__=='__main__':
    main()

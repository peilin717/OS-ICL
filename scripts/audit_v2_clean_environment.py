#!/usr/bin/env python3
"""Verify source checkout with newly installed, isolated Python dependencies.

Uses a task-owned temporary virtual environment; does not install into the
working interpreter. System Chrome/FFmpeg remain supplied by this host, and
this is not a second-machine or external-model evaluation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import artifact_provenance


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    implementation=artifact_provenance.capture()
    env=dict(os.environ,PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH',None)
    logs={}
    with tempfile.TemporaryDirectory(prefix='os-icl-clean-env-') as task_temp:
        task_root=Path(task_temp)
        venv=task_root/'fresh interpreter'
        subprocess.run([sys.executable,'-m','venv',str(venv)],check=True,env=env,timeout=60)
        python=venv/'bin/python'
        installed=subprocess.run([str(python),'-m','pip','--isolated','install',
                                  '--index-url','https://pypi.org/simple','--no-cache-dir',
                                  '--disable-pip-version-check','--no-input',
                                  'pytest==9.0.2','playwright==1.63.0'],env=env,
                                 text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        if installed.returncode:
            raise RuntimeError('Fresh dependency installation failed:\n'+installed.stdout[-6000:])
        print('Fresh isolated dependency installation completed.',flush=True)
        freeze=subprocess.check_output([str(python),'-m','pip','freeze'],env=env,text=True,timeout=30).splitlines()
        checkout=task_root/'source checkout with spaces'
        checkout.mkdir()
        for path in ROOT.glob('*.py'):shutil.copy2(path,checkout/path.name)
        for name in ['run.sh','test.sh','CITATION.cff']:shutil.copy2(ROOT/name,checkout/name)
        for name in ['static','scripts','tests']:
            shutil.copytree(ROOT/name,checkout/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        # This tracked historical public manifest is required by the preserved
        # v1 compatibility tests. Do not copy private runtime episodes/videos.
        legacy_manifest=Path('data/manifests/os-icl-1.0.0.json')
        (checkout/legacy_manifest).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/legacy_manifest,checkout/legacy_manifest)
        env['OS_ICL_PYTHON']=str(python)
        def run(name,command,timeout):
            result=subprocess.run(command,cwd=checkout,env=env,text=True,
                                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
            logs[name]=result.stdout
            if result.returncode:
                raise RuntimeError(name+' failed:\n'+result.stdout[-6000:])
            print(name+' passed.',flush=True)
        run('full_tests',[str(checkout/'test.sh')],180)
        portable=task_root/'portable-report.json'
        run('portable_startup',[str(python),'scripts/audit_v2_portable_checkout.py','--output',str(portable)],60)
        run('native_input_replay',[str(python),'scripts/audit_v2_input_capture_ui.py'],60)
        portable_report=json.loads(portable.read_text())
        if portable_report['implementation_fingerprint']!=implementation['fingerprint']:
            raise RuntimeError('Fresh checkout fingerprint mismatch.')
    artifact_provenance.assert_unchanged(implementation)
    report={'schema_version':1,'status':'passed','implementation_fingerprint':implementation['fingerprint'],
            'fresh_python_dependencies':True,'dependencies':freeze,
            'python_version':sys.version,'checkout_path_with_spaces':True,
            'system_dependencies':'Existing host Google Chrome/FFmpeg; not a fresh OS installation',
            'independent_machine':False,'model_evaluation':False,'logs':logs,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print('Fresh dependency/source-checkout audit passed: '+str(args.output),flush=True)


if __name__=='__main__':main()

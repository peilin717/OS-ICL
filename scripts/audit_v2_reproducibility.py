#!/usr/bin/env python3
"""Cross-process deterministic engine checks on held-out query seeds.

Not a model evaluation, video approval or independent-machine reproduction.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import artifact_provenance
import workflows as w

SEEDS=(42,173,4201)


def worker():
    rows=[]
    for case in w._FIXTURE_CASES:
        for seed in SEEDS:
            visible=[]
            for context in range(3):
                ep=w._generate_fixture(case['id'],context,seed)
                visible.append(w.public(ep))
                for action in ep['reference']:
                    # Demonstrations intentionally include lock/permission and
                    # prerequisite failures before recovery. Compare their
                    # complete traces too; only the final successful state is
                    # required, not an artificially error-free trajectory.
                    w.transition(ep,action)
                result=w.evaluate(ep)
                if not result['success']:
                    raise RuntimeError('Held-out engine path failed: '+json.dumps(result))
                meaningful=[e for e in ep['events'] if e['accepted'] and e['before']!=e['after']
                            and e['action']['op']!='properties' and not
                            (isinstance(e['outcome'],dict) and e['outcome'].get('status')=='Failed')]
                if len(meaningful)<25:
                    raise RuntimeError('Held-out reference has fewer than 25 meaningful operations.')
                rows.append({'case_id':case['id'],'seed':seed,'convention':context,
                             'initial_sha256':w.digest(ep['initial']),
                             'reference_sha256':w.digest(ep['reference']),
                             'events_sha256':w.digest(ep['events']),
                             'final_state_sha256':result['state_hash'],
                             'meaningful_operations':len(meaningful),
                             'rejected_attempts':sum(not e['accepted'] for e in ep['events']),
                             'failed_job_attempts':sum(isinstance(e['outcome'],dict) and e['outcome'].get('status')=='Failed' for e in ep['events']),
                             'success':True})
            if not all(query==visible[0] for query in visible):
                raise RuntimeError('Initial public query differs across hidden contexts.')
    artifact_provenance.assert_unchanged(w.IMPLEMENTATION)
    return {'implementation_fingerprint':w.IMPLEMENTATION['fingerprint'],'rows':rows}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.worker:
        print(json.dumps(worker(),sort_keys=True))
        return
    if not args.output:
        parser.error('--output is required')
    def invoke(hash_seed):
        env=dict(os.environ,PYTHONHASHSEED=str(hash_seed))
        raw=subprocess.check_output([sys.executable,str(Path(__file__).resolve()),'--worker'],
                                    cwd=ROOT,env=env,timeout=180)
        return json.loads(raw)
    with ThreadPoolExecutor(max_workers=2) as pool:
        runs=list(pool.map(invoke,[11,97]))
    if runs[0]!=runs[1]:
        raise RuntimeError('Fresh processes produced different episode/reference/trace/state hashes.')
    artifact_provenance.assert_unchanged(w.IMPLEMENTATION)
    report={'schema_version':1,'benchmark_version':w.VERSION,
            'implementation_fingerprint':w.IMPLEMENTATION['fingerprint'],
            'status':'passed','scope':'cross-process held-out engine reproducibility',
            'model_evaluation':False,'video_review':False,'independent_machine':False,
            'python_hash_seeds':[11,97],'query_seeds':list(SEEDS),
            'paths_per_process':len(runs[0]['rows']),'processes':2,
            'audit_script_sha256':__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),
            'rows':runs[0]['rows']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print(f"Verified {report['paths_per_process']} held-out engine paths in two fresh processes; no model or video claims.")


if __name__=='__main__':
    main()

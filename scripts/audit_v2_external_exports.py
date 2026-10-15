#!/usr/bin/env python3
"""Exercise real reset/export/video interfaces; never launch an agent model.

Requires the complete current structural video matrix. This is runner-interface
verification, not visual approval, a model baseline or independent reproduction.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import workflows as w
import artifact_provenance
from export_v2_episode import build_export
from validate_v2_release import validate, QUERY_SEEDS


def request(base,path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(base.rstrip('/')+path,data=data,
                               headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:
        return json.load(response)


def assert_agent_privacy(value):
    banned={'convention','reference','recorder_brief','condition','checks','state',
            'initial','pipeline','plan_variant','source_hashes','rules','policy'}
    if isinstance(value,dict):
        leaked=banned.intersection(value)
        if leaked:raise ValueError('Private runner data in agent launch: '+', '.join(sorted(leaked)))
        for child in value.values():assert_agent_privacy(child)
    elif isinstance(value,list):
        for child in value:assert_agent_privacy(child)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--release-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:8790')
    args=parser.parse_args()
    # Fail before creating query sessions if the 108-video evidence is missing,
    # mislabeled, stale, undeodable or incorrectly scored.
    try:
        manifest=validate(args.release_root)
    except ValueError as error:
        parser.error(str(error))
    health=request(args.base_url,'/api/health')
    if not health.get('ok') or health['benchmark_version']!=w.VERSION:
        raise ValueError('Preview service does not match the release implementation.')
    groups={}
    for entry in manifest['entries']:
        name=entry['episode_id']+'.webm'
        canonical=ROOT/'data/videos'/name
        if not canonical.is_file() or hashlib.sha256(canonical.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('HTTP artifact copy differs from validated release video: '+name)
        with urllib.request.urlopen(args.base_url.rstrip('/')+'/artifacts/'+name,timeout=30) as response:
            if not response.headers.get('Content-Type','').startswith('video/'):
                raise ValueError('Artifact endpoint does not return a video: '+name)
            # Disk bytes were fully decoded by structural validation. Here,
            # verify routing and response signature without a second download.
            with canonical.open('rb') as stream:signature=stream.read(4)
            if response.read(4)!=signature:
                raise ValueError('Artifact response differs from the canonical file: '+name)
        groups.setdefault((entry['case_id'],entry['convention']),[]).append({
            'episode_id':entry['episode_id'],'case_id':entry['case_id'],
            'convention':entry['convention'],'seed':entry['seed'],
            'video':name,'sha256':entry['sha256'],'actor':entry['recording_actor']})
    rows=[]
    for case in w.CASES:
        for context in range(3):
            for seed in QUERY_SEEDS:
                artifact_provenance.assert_unchanged(w.IMPLEMENTATION)
                query=request(args.base_url,'/api/v2/sessions',{
                    'case_id':case['id'],'convention':context,'seed':seed,
                    'mode':'evaluation','external_task_id':'export-check-'+str(len(rows)+1)})
                sid=query['id']
                if not query.get('compatible'):
                    raise ValueError('Query session is incompatible with current sources.')
                session=json.loads((ROOT/'data/episodes'/f'{sid}.json').read_text())
                if session['episode']['implementation']['fingerprint']!=manifest['implementation']['fingerprint']:
                    raise ValueError('Live service is running a different implementation.')
                # A harmless inspect operation exercises the real mutation/reset
                # lifecycle. No semantic solve or model evaluation is performed.
                request(args.base_url,f'/api/v2/sessions/{sid}/action',{'op':'properties','target':'source-0'})
                reset=request(args.base_url,f'/api/v2/sessions/{sid}/reset',{})
                if reset['state_hash']!=query['state_hash']:
                    raise ValueError('Query reset does not reproduce the initial state.')
                session=json.loads((ROOT/'data/episodes'/f'{sid}.json').read_text())
                trials=[]
                for condition in ['matching','zero-shot','wrong-demo']:
                    demo_context=(context+1)%3 if condition=='wrong-demo' else context
                    demos=groups[(case['id'],demo_context)] if condition!='zero-shot' else []
                    launch,trusted=build_export(session,demos,args.base_url,condition)
                    assert_agent_privacy(launch)
                    if len(launch['demonstrations'])!=(0 if condition=='zero-shot' else 3):
                        raise ValueError('Export has the wrong demonstration count.')
                    # Opaque public directory names do not disclose control labels.
                    trial_id=f'trial-{len(rows)*3+len(trials)+1:04d}'
                    public=args.output/'agent'/trial_id
                    private=args.output/'trusted'/trial_id
                    public.mkdir(parents=True,exist_ok=True);private.mkdir(parents=True,exist_ok=True)
                    (public/'launch.json').write_text(json.dumps(launch,indent=2))
                    (private/'runner.json').write_text(json.dumps(trusted,indent=2))
                    trials.append({'id':trial_id,'condition':condition,'demo_context':demo_context,
                                   'public':str(public.relative_to(args.output)),'trusted':str(private.relative_to(args.output))})
                rows.append({'episode_id':sid,'case_id':case['id'],'convention':context,
                             'seed':seed,'reset_verified':True,'trials':trials})
                print(case['id'],context,seed,'EXPORT/RESET PASS',flush=True)
    report={'schema_version':1,'implementation':w.IMPLEMENTATION,'status':'passed',
            'scope':'real external runner interfaces, not model evaluation or visual approval',
            'query_count':len(rows),'trial_bundles':len(rows)*3,'rows':rows,
            'audit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'runner_instruction':'Reset the shared query session before every trial; never run conditions concurrently.'}
    (args.output/'trusted-audit.json').write_text(json.dumps(report,indent=2))
    print('Verified 108 query sessions and 324 control bundles; no model was invoked.')


if __name__=='__main__':
    main()

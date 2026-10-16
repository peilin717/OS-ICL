#!/usr/bin/env python3
"""Export a trusted runner bundle; agent launch metadata excludes hidden rules.

No model is invoked. The current 36-task catalogue uses one matching video per query.
Use --condition zero-shot only for an explicitly labeled experimental control.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import workflows
import artifact_provenance


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compatible_demos(episode, directory, videos, convention=None):
    candidates=[]
    seen=set()
    for path in sorted(directory.glob('osl_*.json')):
        session=json.loads(path.read_text())
        ep=session.get('episode',{})
        if session.get('mode')!='demo' or not (session.get('result') or {}).get('success'):
            continue
        if ep.get('benchmark_version')!=episode['benchmark_version'] or ep.get('schema_version')!=episode['schema_version']:
            continue
        provenance=session.get('video_provenance') or {}
        if ep.get('implementation',{}).get('fingerprint')!=episode['implementation']['fingerprint'] or not provenance.get('replay_verified'):
            continue
        if provenance.get('trace_sha256')!=artifact_provenance.digest(session.get('ui_events',[])) or provenance.get('final_state_sha256')!=artifact_provenance.digest(ep.get('state',{})):
            continue
        desired=episode['convention'] if convention is None else convention
        if ep.get('case',{}).get('id')!=episode['case']['id'] or ep.get('convention')!=desired:
            continue
        seed=ep.get('seed')
        if seed==episode['seed'] or seed in seen:
            continue
        name=session.get('video')
        if not name or Path(name).name!=name or session.get('video_status')!='ready':
            continue
        video=videos/name
        if not video.is_file() or video.stat().st_size<1000:
            continue
        seen.add(seed)
        candidates.append({'episode_id':session['id'],'seed':seed,'case_id':ep['case']['id'],'convention':ep['convention'],'video':name,'sha256':sha_file(video),
                           'recording_source':'browser-interaction-replay','actor':provenance.get('actor','not-attested')})
    return candidates


def manifest_demos(episode, path, convention=None):
    """Read trusted standard-108 metadata; never expose its rule labels to the agent."""
    manifest=json.loads(Path(path).read_text())
    if manifest.get('standard')!='one-demo-per-task-condition' or manifest.get('ready')!=108:
        raise ValueError('Expected a complete standard 108-demo manifest.')
    import tasks36
    expected={(c['id'],rule) for c in tasks36.CASES for rule in ['A','B','C']}
    entries=[(row['case_id'],row['condition']) for row in manifest['videos']]
    if len(entries)!=108 or len(set(entries))!=108 or set(entries)!=expected:
        raise ValueError('Standard manifest must contain exactly one video for each of the 108 task/rule pairs.')
    if manifest['source_fingerprint']!=episode['implementation']['fingerprint']:
        raise ValueError('Standard demo source does not match the query implementation.')
    desired=episode['convention'] if convention is None else convention
    demos=[]
    for row in manifest['videos']:
        if row['case_id']!=episode['case']['id'] or row['condition']!=chr(65+desired):continue
        seeds=row.get('example_seeds',[row['seed']])
        if episode['seed'] in seeds:continue
        demos.append({'episode_id':row['session_id'],'seed':row['seed'],'example_seeds':seeds,'case_id':row['case_id'],'convention':desired,'video':row['video'],'video_url':row['download_url'],'sha256':row['sha256'],'recording_source':row['provenance'].get('source','browser-interaction-replay'),'actor':row['provenance']['actor']})
    return demos


def build_export(session, demos, base_url, condition='matching'):
    episode=session['episode']
    if episode.get('benchmark_version')!=workflows.VERSION or episode.get('schema_version')!=5:
        raise ValueError('Episode was created by an earlier development version; reset or recreate it.')
    if episode.get('implementation',{}).get('fingerprint')!=artifact_provenance.capture()['fingerprint']:
        raise ValueError('Episode implementation differs from the current source; create a matching versioned episode.')
    if session.get('mode')!='evaluation':
        raise ValueError('A benchmark query must be an evaluation session.')
    if condition not in {'matching','zero-shot','wrong-demo'}:
        raise ValueError('Unsupported context condition.')
    distinct={}
    for demo in demos:
        if demo.get('case_id',episode['case']['id'])!=episode['case']['id']:
            raise ValueError('Demonstrations must belong to the query task.')
        demo_context=demo.get('convention',episode['convention'])
        if condition=='matching' and demo_context!=episode['convention'] or condition=='wrong-demo' and demo_context==episode['convention']:
            raise ValueError('Demonstration context does not match the requested experimental condition.')
        if episode['seed'] not in demo.get('example_seeds',[demo['seed']]):
            distinct.setdefault(demo['seed'],demo)
    required=1 if episode.get('task36') else 3
    if condition!='zero-shot' and len(distinct)<required:
        raise ValueError(('Current catalogue requires one successful same-context video on a query-disjoint example.' if required==1 else 'Matching-context evaluation requires three successful same-context videos on distinct, query-disjoint seeds.'))
    selected=list(distinct.values())[:required] if condition!='zero-shot' else []
    launch={'schema_version':1,'benchmark_version':workflows.VERSION,'episode_id':session['id'],
            'task':episode['case']['task'],'launch_url':base_url.rstrip('/')+'/?session='+session['id'],
            'viewport':{'width':1280,'height':720},
            'demonstrations':[{'video_url':d.get('video_url') or base_url.rstrip('/')+'/artifacts/'+d['video'],'sha256':d['sha256']} for d in selected],
            'allowed_observation':'screenshots','allowed_control':'mouse-and-keyboard'}
    trusted={'schema_version':1,'benchmark_version':workflows.VERSION,'condition':condition,
             'session':session,'demonstration_provenance':selected,
             'source_hashes':episode['implementation']['source_hashes']}
    return launch,trusted


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--session',required=True)
    parser.add_argument('--manifest',type=Path,help='Downloaded trusted standard-108 manifest; supports remote video URLs')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:8790')
    parser.add_argument('--condition',choices=['matching','zero-shot','wrong-demo'],default='matching')
    parser.add_argument('--wrong-convention',type=int,choices=[0,1,2])
    args=parser.parse_args()
    if not args.session.startswith('osl_') or not args.session.replace('_','').isalnum():
        parser.error('Invalid episode identifier.')
    session=json.loads((ROOT/'data/episodes'/f'{args.session}.json').read_text())
    try:
        if args.condition=='wrong-demo' and (args.wrong_convention is None or args.wrong_convention==session['episode']['convention']):
            raise ValueError('Wrong-demo control requires a different --wrong-convention.')
        desired=args.wrong_convention if args.condition=='wrong-demo' else None
        demos=manifest_demos(session['episode'],args.manifest,desired) if args.manifest else compatible_demos(session['episode'],ROOT/'data/episodes',ROOT/'data/videos',desired)
        launch,trusted=build_export(session,demos,args.base_url,args.condition)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'agent-launch.json').write_text(json.dumps(launch,indent=2))
    (args.output/'trusted-runner.json').write_text(json.dumps(trusted,indent=2))
    print('Exported agent launch metadata and trusted runner evidence. Do not expose trusted-runner.json to the model.')


if __name__=='__main__':
    main()

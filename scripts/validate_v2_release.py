#!/usr/bin/env python3
"""Verify the complete long-horizon video matrix and write a reproducible manifest.

This verifies structure/provenance and decodes every video. Visual quality review
is recorded separately; structural success must not stand in for that review.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import artifact_provenance
import workflows

QUERY_SEEDS=(42,173,4201)


def validate_demo_seeds(seeds):
    if len(seeds)<3 or len(set(seeds))!=len(seeds):
        raise ValueError('Release requires at least three distinct demonstration seeds.')
    if set(seeds)&set(QUERY_SEEDS):
        raise ValueError('Demonstration seeds must not overlap reserved query seeds.')
    # Generation uses seed % 3 to distinguish the healthy initial fixture
    # from two recovery fixtures. Distinct seeds alone can all select the
    # same fixture, leaving the intended branch coverage unrepresented.
    if {seed % 3 for seed in seeds}!={0,1,2}:
        raise ValueError('Demonstration seeds must cover all three initial scenarios, including the healthy scenario.')


def validate_episode_identity(row,session):
    episode=session['episode']
    actual=(episode['case']['id'],episode['convention'],episode['seed'])
    labelled=(row['case_id'],row['convention'],row['seed'])
    if actual!=labelled or session['id']!=row['session_id']:
        raise ValueError(f'Video label does not match episode identity: {labelled} != {actual}')
    if session.get('engine')!='v2' or session.get('mode')!='demo' or session.get('status')!='finished':
        raise ValueError(f'Video must belong to a finished v2 demonstration: {labelled}')


def validate(root, seeds=(1001,1002,1003)):
    validate_demo_seeds(seeds)
    root=root.resolve()
    required={(case['id'],context,seed) for case in workflows.CASES for context in range(3) for seed in seeds}
    entries=[]
    keys=set()
    fingerprint=workflows.IMPLEMENTATION['fingerprint']
    artifact_provenance.assert_unchanged(workflows.IMPLEMENTATION)
    for context in range(3):
        index=root/f'context-{context}'/'results.json'
        if not index.is_file():
            raise ValueError(f'Missing context results: {index}')
        for row in json.loads(index.read_text()):
            key=(row['case_id'],row['convention'],row['seed'])
            if key not in required or key in keys:
                raise ValueError(f'Unexpected or duplicate context/seed entry: {key}')
            if row['convention']!=context or row.get('implementation_fingerprint')!=fingerprint:
                raise ValueError(f'Implementation/context mismatch: {key}')
            if not row.get('replay_hash_verified') or row.get('browser_errors'):
                raise ValueError(f'Browser/replay audit failed: {key}')
            session=json.loads((ROOT/'data/episodes'/f"{row['session_id']}.json").read_text())
            validate_episode_identity(row,session)
            episode=session['episode']
            if episode.get('scenario')!=row['seed'] % 3:
                raise ValueError(f'Episode scenario does not match its generation seed: {key}')
            if episode.get('schema_version')!=5 or episode.get('benchmark_version')!=workflows.VERSION or episode['implementation']['fingerprint']!=fingerprint:
                raise ValueError(f'Wrong episode version: {key}')
            score=workflows.evaluate(episode)
            if not score['success'] or not score['rule_compliance'] or not score['side_effect_free']:
                raise ValueError(f'Episode does not satisfy the complete task: {key}')
            if row.get('result')!=score or session.get('result')!=score:
                raise ValueError(f'Reported result differs from current episode evaluation: {key}')
            meaningful=[e for e in episode['events'] if e['accepted'] and e['before']!=e['after'] and e['action']['op']!='properties' and
                        not (isinstance(e['outcome'],dict) and e['outcome'].get('status')=='Failed')]
            if len(meaningful)<25:
                raise ValueError(f'Insufficient meaningful operations: {key}')
            opened={event['selector'].split('data-open=',1)[1].split('|',1)[0].split(':',1)[0]
                    for event in session['ui_events'] if 'data-open=' in event.get('selector','')}
            if len(opened)<3:
                raise ValueError(f'Fewer than three applications used in the UI trace: {key}')
            video=Path(row['video_path']).resolve()
            if root not in video.parents or not video.is_file():
                raise ValueError(f'Video missing or outside release directory: {key}')
            sha=hashlib.sha256(video.read_bytes()).hexdigest()
            if sha!=row.get('video_sha256'):
                raise ValueError(f'Video checksum mismatch: {key}')
            provenance=session.get('video_provenance') or {}
            if provenance!=row.get('video_provenance') or provenance!=artifact_provenance.video_metadata(session):
                raise ValueError(f'Video provenance does not match episode/trace: {key}')
            if provenance['actor']!='oracle-assisted-browser-audit':
                raise ValueError(f'Unexpected or unverified recording actor: {key}')
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name','-show_entries','format=duration,size','-of','json',str(video)]))
            stream=probe['streams'][0]
            if (stream['width'],stream['height'])!=(1280,720) or float(probe['format']['duration'])<10:
                raise ValueError(f'Invalid video geometry/duration: {key}')
            subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True,capture_output=True,timeout=120)
            keys.add(key)
            entries.append({'case_id':key[0],'convention':key[1],'seed':key[2],'scenario':episode['scenario'],
                            'episode_id':session['id'],'video':str(video.relative_to(root)),'sha256':sha,
                            'duration_seconds':float(probe['format']['duration']),'width':1280,'height':720,
                            'meaningful_operations':len(meaningful),'ui_events':len(session['ui_events']),
                            'applications_opened':sorted(opened),
                            'state_hash':score['state_hash'],'recording_actor':provenance['actor'],
                            'trace_sha256':provenance['trace_sha256'],'replay_verified':True})
    missing=required-keys
    if missing:
        raise ValueError(f'Missing {len(missing)} required videos, including {sorted(missing)[:5]}')
    return {'schema_version':1,'benchmark_version':workflows.VERSION,'implementation':workflows.IMPLEMENTATION,
            'cases':12,'contexts_per_case':3,'demos_per_context':len(seeds),'video_count':len(entries),
            'demo_seeds':list(seeds),'reserved_query_seeds':list(QUERY_SEEDS),
            'structural_audit':'passed','visual_review':'pending',
            'recording_source':'oracle-assisted UI interaction replay',
            'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'entries':sorted(entries,key=lambda e:(e['case_id'],e['convention'],e['seed']))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--seeds',default='1001,1002,1003')
    args=parser.parse_args()
    try:
        manifest=validate(args.root,tuple(int(s) for s in args.seeds.split(',')))
    except (ValueError,KeyError,subprocess.CalledProcessError) as error:
        parser.error(str(error))
    output=args.root/'manifest.json'
    output.write_text(json.dumps(manifest,indent=2))
    print(f"Verified {manifest['video_count']} videos; visual review remains pending. Manifest: {output}")


if __name__=='__main__':
    main()

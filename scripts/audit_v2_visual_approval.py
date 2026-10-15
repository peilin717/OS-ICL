#!/usr/bin/env python3
"""Validate explicit visual-review attestations after structural validation.

This does not inspect videos automatically or prove a reviewer's truthfulness.
Never mark a sampled-only review as whole-video approval.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from validate_v2_release import validate

CHECKS=('task_meaning','input_selection','settings_readable','recovery_if_present',
        'output_inspection','geometry','legibility','no_private_instructions','critical_transitions')
FULL_SCOPE='whole-timeline-and-critical-transitions'


def check_reviews(manifest,review):
    if manifest.get('structural_audit')!='passed':
        raise ValueError('Structural validation must pass before visual approval.')
    fingerprint=manifest['implementation']['fingerprint']
    if review.get('implementation_fingerprint')!=fingerprint:
        raise ValueError('Visual review belongs to a different implementation.')
    expected={(entry['case_id'],entry['convention'],entry['seed']):entry for entry in manifest['entries']}
    approved={}
    for row in review.get('entries',[]):
        key=(row['case_id'],row['convention'],row['seed'])
        if key not in expected or key in approved:
            raise ValueError('Unexpected or duplicate visual-review identity: '+str(key))
        entry=expected[key]
        if row.get('sha256')!=entry['sha256']:
            raise ValueError('Visual review refers to different video bytes: '+str(key))
        if row.get('status')!='passed' or row.get('scope')!=FULL_SCOPE:
            raise ValueError('Video lacks whole-timeline/critical-transition approval: '+str(key))
        if not isinstance(row.get('reviewer'),str) or not row['reviewer'].strip():
            raise ValueError('Visual reviewer is missing: '+str(key))
        if not isinstance(row.get('notes'),str) or len(row['notes'].strip())<20:
            raise ValueError('Specific visual inspection notes are missing: '+str(key))
        coverage=row.get('coverage',{})
        start=coverage.get('start_seconds');end=coverage.get('end_seconds')
        if type(start) not in (int,float) or start!=0 or type(end) not in (int,float) or not math.isfinite(end) or end<entry['duration_seconds']:
            raise ValueError('Visual review does not cover the complete timeline: '+str(key))
        if any(row.get('checks',{}).get(name) is not True for name in CHECKS):
            raise ValueError('Visual criteria are incomplete or failed: '+str(key))
        approved[key]=row
    if set(approved)!=set(expected):
        raise ValueError(f'Missing {len(set(expected)-set(approved))} visual approvals.')
    return {'status':'passed','videos':len(approved),'implementation_fingerprint':fingerprint,
            'scope':FULL_SCOPE,'automatic_visual_inspection':False,
            'reviewer_attestations_validated':True}


def pending_template(manifest):
    return {'schema_version':1,'implementation_fingerprint':manifest['implementation']['fingerprint'],
            'instructions':'Inspect the actual complete timeline and critical transitions. Sampling alone cannot pass.',
            'entries':[{'case_id':entry['case_id'],'convention':entry['convention'],'seed':entry['seed'],
                        'sha256':entry['sha256'],'status':'pending','scope':'','reviewer':'','notes':'',
                        'coverage':{'start_seconds':0,'end_seconds':0},
                        'checks':{name:False for name in CHECKS}} for entry in manifest['entries']]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--reviews',type=Path)
    parser.add_argument('--template',type=Path,help='Create a pending-only checklist; never auto-approve')
    args=parser.parse_args()
    if bool(args.reviews)==bool(args.template):parser.error('Choose exactly one of --reviews or --template')
    try:
        manifest=validate(args.root)
        if args.template:
            if args.template.exists():raise ValueError('Refusing to overwrite an existing review checklist.')
            args.template.parent.mkdir(parents=True,exist_ok=True)
            args.template.write_text(json.dumps(pending_template(manifest),indent=2))
            print('Created pending visual checklist; no video is approved.')
            return
        review=json.loads(args.reviews.read_text())
        report=check_reviews(manifest,review)
    except (ValueError,KeyError) as error:parser.error(str(error))
    report['review_sha256']=hashlib.sha256(args.reviews.read_bytes()).hexdigest()
    report['validator_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.root/'visual-approval.json').write_text(json.dumps(report,indent=2))
    print(f"Validated explicit review attestations for {report['videos']} videos; this is not automatic visual inspection.")


if __name__=='__main__':main()

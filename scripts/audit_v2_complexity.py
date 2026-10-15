#!/usr/bin/env python3
"""Measure task structure, not empirical agent difficulty or video quality."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import artifact_provenance
import workflows as w

DEMO_SEEDS=(1001,1002,1003)
QUERY_SEEDS=(42,173,4201)


def dependency_depth(jobs):
    """Longest actual job dependency chain, counting jobs rather than edges."""
    by_name={job['name']:job for job in jobs}
    if len(by_name)!=len(jobs):raise ValueError('Duplicate job names')
    memo={}
    visiting=set()
    def visit(name):
        if name in memo:return memo[name]
        if name in visiting:raise ValueError('Cyclic job dependencies')
        if name not in by_name:raise ValueError('Missing job dependency: '+name)
        visiting.add(name)
        parent=by_name[name].get('dependency')
        memo[name]=1+(visit(parent) if parent else 0)
        visiting.remove(name)
        return memo[name]
    return max((visit(name) for name in by_name),default=0)


def meaningful(events):
    return [event for event in events if event['accepted'] and event['before']!=event['after']
            and event['action']['op']!='properties' and not
            (isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed')]


def profile(case_id,context,seed):
    ep=w.generate(case_id,context,seed)
    for action in ep['reference']:w.transition(ep,action)
    result=w.evaluate(ep)
    if not result['success']:raise ValueError('Reference workflow failed: '+str((case_id,context,seed)))
    events=ep['events']
    mutations=meaningful(events)
    if len(mutations)<25:raise ValueError('Long-horizon mutation gate failed')
    jobs=ep['state']['jobs']
    source_indices=[int(file['id'].removeprefix('source-')) for file in ep['initial']['files'] if file['id'].startswith('source-')]
    selected_sources=[w.domain_checks.required_source(ep['initial'],ep['case'],index) for index in source_indices]
    return {'case_id':case_id,'convention':context,'seed':seed,'scenario':ep['scenario'],
            'split':'demonstration' if seed in DEMO_SEEDS else 'query',
            'meaningful_mutations':len(mutations),'semantic_attempts':len(events),
            'mutation_types':sorted({event['action']['op'] for event in mutations}),
            'rejected_attempts':sum(not event['accepted'] for event in events),
            'failed_outcomes':sum(isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed' for event in events),
            'job_count':len(jobs),'completed_jobs':sum(job['status']=='Completed' for job in jobs),
            'job_dependency_depth':dependency_depth(jobs),
            'initial_source_directories':len({file['parent'] for file in selected_sources}),
            'new_live_files':sum(not file['deleted'] and file['kind']!='folder' and file['id'] not in
                                 {original['id'] for original in ep['initial']['files']} for file in ep['state']['files']),
            'state_hash':result['state_hash']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rows=[profile(case['id'],context,seed) for case in w.CASES
          for context in range(3) for seed in DEMO_SEEDS+QUERY_SEEDS]
    summary=[]
    for case in w.CASES:
        group=[row for row in rows if row['case_id']==case['id']]
        summary.append({'case_id':case['id'],**{metric:[min(row[metric] for row in group),max(row[metric] for row in group)]
                       for metric in ['meaningful_mutations','semantic_attempts','job_count','job_dependency_depth','new_live_files']}})
    artifact_provenance.assert_unchanged(w.IMPLEMENTATION)
    report={'schema_version':1,'status':'passed','implementation_fingerprint':w.IMPLEMENTATION['fingerprint'],
            'scope':'engine reference structural complexity; not observed agent difficulty',
            'model_evaluation':False,'video_approval':False,'measures_mouse_clicks':False,
            'dependency_depth_definition':'Longest actual job chain, counting jobs; excludes file/process dependencies',
            'demo_seeds':list(DEMO_SEEDS),'query_seeds':list(QUERY_SEEDS),'paths':len(rows),
            'summary':summary,'rows':rows,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({'paths':len(rows),'summary':summary}),flush=True)


if __name__=='__main__':main()

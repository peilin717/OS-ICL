import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_every_template_accepts_alternative_plans_across_contexts_and_branches():
    for case in w.CASES:
        for convention in range(3):
            for seed in [1001,1002]:
                for variant in ['configure-first','reverse-sources']:
                    ep=w.generate(case['id'],convention,seed,variant)
                    for action in ep['reference']:w.transition(ep,action)
                    result=w.evaluate(ep)
                    assert result['success'],(case['id'],convention,seed,variant,result)


def test_plan_variants_change_actions_without_leaking_or_changing_initial_query():
    variants=[w.generate('OS-LH-07',1,1001,v) for v in ['standard','configure-first','reverse-sources']]
    assert variants[0]['initial']==variants[1]['initial']==variants[2]['initial']
    assert w.public(variants[0])==w.public(variants[1])==w.public(variants[2])
    assert variants[0]['reference']!=variants[1]['reference']!=variants[2]['reference']
    assert 'plan_variant' not in w.public(variants[1])
    reverse=[a['target'] for a in variants[2]['reference'] if a['op']=='copy' and a['parent']!='documents']
    assert reverse==['source-3','source-2','source-1','source-0']

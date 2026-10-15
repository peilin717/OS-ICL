import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def solve():
    ep=w.generate('OS-LH-03',0,1002)
    for action in ep['reference']:w.transition(ep,action)
    assert w.evaluate(ep)['success']
    return ep


def test_saving_unchanged_original_is_a_harmless_noop():
    ep=solve()
    file=w.get_file(ep['state'],'source-0')
    revision=file['revision']
    result=w.transition(ep,{'op':'write','target':file['id'],'content':file['content']})
    assert result['accepted'] and result['before']==result['after']
    assert w.get_file(ep['state'],'source-0')['revision']==revision
    assert w.evaluate(ep)['success']


def test_altering_original_then_restoring_bytes_does_not_preserve_original_revision():
    ep=solve()
    original=w.get_file(ep['state'],'source-0')['content']
    w.transition(ep,{'op':'write','target':'source-0','content':'Temporary source change'})
    w.transition(ep,{'op':'write','target':'source-0','content':original})
    assert not w.evaluate(ep)['side_effect_free']
    assert not w.evaluate(ep)['success']

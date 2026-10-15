import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_release_repairs_missing_entry_then_revalidates_and_delivers_matching_version():
    ep=w._generate_fixture('OS-LH-02',1,1001)
    failures=[]
    for action in ep['reference']:
        event=w.transition(ep,action)
        if isinstance(event['outcome'],dict) and event['outcome'].get('status')=='Failed':
            failures.append(event['outcome']['error'])
    assert any('Processing tools' in error for error in failures)
    assert any('Build entry not found' in error for error in failures)
    assert w.evaluate(ep)['success'],w.evaluate(ep)
    assert w.evaluate(ep)['checks']['release_version_consistent']
    initial=json.loads(w.get_file(ep['initial'],'source-2')['content'])
    assert initial['entry']=='application-old.js'
    assert w.get_file(ep['state'],'source-2')['content']==w.get_file(ep['initial'],'source-2')['content']
    assert w.get_file(ep['state'],'old-output')['content']==w.get_file(ep['initial'],'old-output')['content']
    # A new build cannot silently substitute last release's notes.
    build=next(j for j in ep['state']['jobs'] if j['kind']=='build')
    note=next(f for f in ep['state']['files'] if f['parent']==build['input'] and f.get('source')=='source-1')
    w.transition(ep,{'op':'write','target':note['id'],'content':'Version: 0.0.0\nOutdated notes\n'})
    assert 'Release version mismatch' in w.job_error(ep['state'],build,ep['case'])
    assert not w.evaluate(ep)['success']


def test_healthy_release_does_not_require_an_artificial_failure():
    ep=w._generate_fixture('OS-LH-02',2,1002)
    for action in ep['reference']:
        event=w.transition(ep,action)
        assert event['accepted']
        assert not isinstance(event['outcome'],dict) or event['outcome'].get('status')!='Failed'
    assert w.evaluate(ep)['success']

import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_current_demo_manifest_is_complete_and_contains_no_private_solutions():
    manifest=json.loads((ROOT/'docs/STANDARD108_MANIFEST.json').read_text())
    entries=manifest['videos']
    assert manifest['expected']==manifest['ready']==108
    assert len({(e['case_id'],e['condition'],e['seed']) for e in entries})==108
    assert Counter(e['condition'] for e in entries)==Counter({'A':36,'B':36,'C':36})
    assert Counter(e['difficulty'] for e in entries)==Counter({'easy':36,'medium':36,'hard':36})
    assert all(len(e['sha256'])==64 and e['bytes']>1000 for e in entries)
    assert all(e['provenance']['replay_verified'] for e in entries)
    encoded=json.dumps(manifest)
    assert not any('"'+key+'"' in encoded for key in ['reference','_judge36','recorder_brief','rule_text','state'])

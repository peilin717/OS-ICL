import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workflows as w


def test_preview_profiles_produce_different_actual_metadata_for_same_query():
    results=[]
    for convention,dimensions in [(0,(1280,720)),(1,(640,360)),(2,(1920,1080))]:
        ep=w.generate('OS-LH-04',convention,1002)
        for action in ep['reference']:w.transition(ep,action)
        assert w.evaluate(ep)['success'],w.evaluate(ep)
        task=next(j for j in ep['state']['jobs'] if j['kind']=='transcode')
        processing=w.get_file(ep['state'],task['artifact'])['provenance']['processing']
        previews=[f for f in ep['state']['files'] if f['parent']==processing['preview_folder'] and not f['deleted']]
        for preview in previews:
            metadata=json.loads(preview['content'])
            assert (metadata['width'],metadata['height'])==dimensions
        results.append(dimensions)
    assert len(set(results))==3


def test_wrong_preview_profile_is_legal_tool_use_but_fails_learned_specification():
    ep=w.generate('OS-LH-04',1,1002)
    for original in ep['reference']:
        action=copy.deepcopy(original)
        if action['op']=='setting' and action['key']=='media.preview':action['value']='review'
        event=w.transition(ep,action)
        assert event['accepted'],event
        assert not isinstance(event['outcome'],dict) or event['outcome'].get('status')!='Failed'
    result=w.evaluate(ep)
    assert result['checks']['captioned_previews'] and result['checks']['media_catalogue_delivered']
    assert not result['checks']['media.preview']
    assert not result['success'] and not result['rule_compliance']

import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('external_export_audit',ROOT/'scripts/audit_v2_external_exports.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.mark.parametrize('key',['convention','reference','condition','pipeline','state','rules','policy'])
def test_private_fields_cannot_hide_in_nested_launch_metadata(key):
    with pytest.raises(ValueError,match='Private runner data'):
        audit.assert_agent_privacy({'demonstrations':[{'nested':{key:'private'}}]})


def test_normal_visual_launch_is_allowed():
    audit.assert_agent_privacy({'episode_id':'osl_opaque','task':'Prepare the project.',
                               'viewport':{'width':1280,'height':720},
                               'demonstrations':[{'video_url':'http://localhost/artifacts/osl_opaque.webm','sha256':'a'*64}],
                               'allowed_control':'mouse-and-keyboard'})

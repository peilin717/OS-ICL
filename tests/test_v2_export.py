import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('export_v2',ROOT/'scripts/export_v2_episode.py')
export=importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)
import workflows
import artifact_provenance


def test_export_enforces_three_disjoint_demonstrations_and_agent_privacy():
    ep=workflows.generate('OS-LH-06',2,4201)
    session={'id':'osl_test','mode':'evaluation','episode':ep,'status':'active'}
    with pytest.raises(ValueError,match='three successful'):
        export.build_export(session,[],'http://localhost:8790')
    demos=[{'seed':n,'video':f'demo-{n}.webm','sha256':'a'*64,'episode_id':f'osl_{n}'} for n in [1001,1002,1003]]
    launch,trusted=export.build_export(session,demos,'http://localhost:8790')
    assert len(launch['demonstrations'])==3
    assert not {'convention','reference','state','initial','recorder_brief','checks'}.intersection(launch)
    assert trusted['session']['episode']['convention']==2
    assert set(trusted['source_hashes'])==set(artifact_provenance.SOURCES)
    assert {'static/recording.html','static/recording-studio.html'} <= set(trusted['source_hashes'])
    with pytest.raises(ValueError,match='three successful'):
        export.build_export(session,[*demos[:2],{**demos[2],'seed':4201}],'http://localhost:8790')
    zero,control=export.build_export(session,[],'http://localhost:8790','zero-shot')
    assert control['condition']=='zero-shot' and zero['demonstrations']==[]
    assert 'context_condition' not in zero
    wrong=[{**d,'convention':0} for d in demos]
    blinded,control=export.build_export(session,wrong,'http://localhost:8790','wrong-demo')
    assert control['condition']=='wrong-demo' and 'context_condition' not in blinded
    assert len(blinded['demonstrations'])==3
    with pytest.raises(ValueError,match='experimental condition'):
        export.build_export(session,wrong,'http://localhost:8790','matching')

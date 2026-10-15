"""Negative structural-release controls, not a substitute for video QA."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('release_validator',ROOT/'scripts/validate_v2_release.py')
validator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
import workflows as w


@pytest.mark.parametrize('seeds', [(1001,), (1001,1002), (1001,1001,1002),
                                  (1001,1002,42), (1001,173,1003), (4201,1002,1003)])
def test_insufficient_duplicate_or_query_overlapping_demos_cannot_be_a_release(tmp_path,seeds):
    with pytest.raises(ValueError,match='distinct|overlap'):
        validator.validate(tmp_path,seeds)


def test_valid_demo_seeds_still_require_actual_matrix(tmp_path):
    validator.validate_demo_seeds((1001,1002,1003))
    with pytest.raises(ValueError,match='Missing context results'):
        validator.validate(tmp_path)


@pytest.mark.parametrize('seeds', [(1002,1005,1008), (1001,1004,1007),
                                  (1003,1006,1009), (1001,1002,1004)])
def test_distinct_seeds_without_full_initial_scenario_coverage_are_rejected(seeds):
    with pytest.raises(ValueError,match='all three initial scenarios'):
        validator.validate_demo_seeds(seeds)


def test_more_than_three_demos_can_cover_all_initial_scenarios():
    validator.validate_demo_seeds((1001,1002,1003,1004))


def fixture():
    ep=w.generate('OS-LH-09',2,1001)
    session={'id':'osl_identity_fixture','engine':'v2','mode':'demo','status':'finished','episode':ep}
    row={'session_id':session['id'],'case_id':'OS-LH-09','convention':2,'seed':1001}
    return row,session


@pytest.mark.parametrize('field,value', [('case_id','OS-LH-01'),('convention',0),
                                        ('seed',1002),('session_id','osl_other')])
def test_video_labels_must_match_real_episode_identity(field,value):
    row,session=fixture()
    validator.validate_episode_identity(row,session)  # identity only, not a success claim
    row[field]=value
    with pytest.raises(ValueError,match='episode identity'):
        validator.validate_episode_identity(row,session)


@pytest.mark.parametrize('field,value', [('engine','v1'),('mode','evaluation'),('status','active')])
def test_evaluation_or_unfinished_sessions_are_not_demonstrations(field,value):
    row,session=fixture()
    session[field]=value
    with pytest.raises(ValueError,match='finished v2 demonstration'):
        validator.validate_episode_identity(row,session)

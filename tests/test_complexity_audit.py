"""Structural metrics must not turn failed attempts/noops into complexity."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('complexity_audit',Path(__file__).resolve().parents[1]/'scripts/audit_v2_complexity.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_empty_and_parallel_job_graphs():
    assert audit.dependency_depth([])==0
    assert audit.dependency_depth([{'name':'a','dependency':''},{'name':'b','dependency':''}])==1


def test_actual_chain_depth_is_order_independent():
    assert audit.dependency_depth([{'name':'c','dependency':'b'},{'name':'a','dependency':''},{'name':'b','dependency':'a'}])==3


@pytest.mark.parametrize('jobs,reason', [
    ([{'name':'a','dependency':'missing'}],'Missing'),
    ([{'name':'a','dependency':'a'}],'Cyclic'),
    ([{'name':'a','dependency':'b'},{'name':'b','dependency':'a'}],'Cyclic'),
    ([{'name':'a'},{'name':'a'}],'Duplicate'),
])
def test_invalid_graph_is_not_a_complexity_measure(jobs,reason):
    with pytest.raises(ValueError,match=reason):audit.dependency_depth(jobs)


def test_properties_rejections_failed_outcomes_and_noops_do_not_count():
    def event(op='write',accepted=True,before='a',after='b',outcome=True):
        return {'action':{'op':op},'accepted':accepted,'before':before,'after':after,'outcome':outcome}
    valid=event()
    assert audit.meaningful([valid,event('properties'),event(accepted=False),event(after='a'),event(outcome={'status':'Failed'})])==[valid]

"""Synthetic gate fixtures only; these tests do not approve release videos."""
import copy
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('visual_approval',ROOT/'scripts/audit_v2_visual_approval.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def fixture():
    manifest={'structural_audit':'passed','implementation':{'fingerprint':'unit-fixture'},
              'entries':[{'case_id':'OS-LH-01','convention':0,'seed':1001,'sha256':'a'*64,'duration_seconds':20}]}
    review=audit.pending_template(manifest)
    row=review['entries'][0]
    row.update(status='passed',scope=audit.FULL_SCOPE,reviewer='synthetic unit fixture',
               notes='Synthetic metadata gate test, not an actual video review.',
               coverage={'start_seconds':0,'end_seconds':20},checks={name:True for name in audit.CHECKS})
    return manifest,review


def test_generated_checklist_cannot_approve_itself():
    manifest,_=fixture()
    pending=audit.pending_template(manifest)
    assert all(row['status']=='pending' and not any(row['checks'].values()) for row in pending['entries'])
    with pytest.raises(ValueError,match='whole-timeline'):audit.check_reviews(manifest,pending)


@pytest.mark.parametrize('field,value',[('status','sampled'),('scope','storyboards-only'),
                                      ('sha256','b'*64),('reviewer',''),('notes','Looks fine'),
                                      ('coverage',{'start_seconds':4,'end_seconds':20}),
                                      ('coverage',{'start_seconds':0,'end_seconds':19}),
                                      ('coverage',{'start_seconds':0,'end_seconds':float('nan')}),
                                      ('coverage',{'start_seconds':0,'end_seconds':float('inf')}),
                                      ('coverage',{'start_seconds':False,'end_seconds':20}),
                                      ('checks',{'geometry':True})])
def test_partial_stale_or_unattested_reviews_do_not_pass(field,value):
    manifest,review=fixture();review['entries'][0][field]=value
    with pytest.raises(ValueError):audit.check_reviews(manifest,review)


def test_missing_duplicate_and_other_version_reviews_fail():
    manifest,review=fixture()
    for altered in [{**review,'entries':[]},
                    {**review,'entries':[review['entries'][0],copy.deepcopy(review['entries'][0])]},
                    {**review,'implementation_fingerprint':'other'}]:
        with pytest.raises(ValueError):audit.check_reviews(manifest,altered)


def test_valid_attestation_is_not_claimed_as_machine_visual_inspection():
    manifest,review=fixture();result=audit.check_reviews(manifest,review)
    assert result['status']=='passed' and not result['automatic_visual_inspection']
    assert result['reviewer_attestations_validated']

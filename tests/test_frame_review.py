"""Preparation must retain every timestamp, including identical-frame repeats."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('frame_review',Path(__file__).resolve().parents[1]/'scripts/prepare_v2_frame_review.py')
review=importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def record(pts=0,size=6,digest='a'*64,stream=0):
    return f'{stream}, {pts}, {pts}, 1, {size}, {digest}\n'


def test_identical_frames_are_not_dropped_from_timeline():
    frames=review.parse_hashes('#tb 0: 1/25\n'+record()+record(pts=1),2,1)
    assert len(frames)==2
    assert [frame['seconds'] for frame in frames]==[0,.04]
    assert frames[0]['sha256']==frames[1]['sha256']


@pytest.mark.parametrize('raw,reason', [
    ('#tb 0: 1/25\n','No decoded'),
    (record(),'Unexpected'),
    ('#tb 0: 1/25\n'+record(size=5),'complete RGB24'),
    ('#tb 0: 1/25\n'+record(digest='a'*32),'SHA-256'),
    ('#tb 0: 1/25\n'+record(stream=1),'Unexpected'),
    ('#tb 0: 1/25\n'+record()+record(),'Non-monotonic'),
])
def test_incomplete_or_ambiguous_frame_stream_is_rejected(raw,reason):
    with pytest.raises(ValueError,match=reason):review.parse_hashes(raw,2,1)

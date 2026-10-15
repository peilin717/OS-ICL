"""Source snapshots include new files but exclude runtime state and links."""
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_v2_source_archive as audit


def required_members():
    return [tarfile.TarInfo(name) for name in sorted(audit.ROOT_FILES | {audit.PUBLIC_MANIFEST})]


def test_complete_source_member_set_is_accepted():
    audit.validate_members(required_members() + [tarfile.TarInfo('tests/test_source_archive.py')])


@pytest.mark.parametrize('name', [
    '../escape', '/absolute', 'static/../../escape', 'static\\escape.py',
    'C:/escape.py', 'data/episodes/osl_private.json', '.git/config',
    'static/__pycache__/compiled.pyc',
])
def test_unsafe_or_runtime_members_are_rejected(name):
    with pytest.raises(ValueError):
        audit.validate_members(required_members() + [tarfile.TarInfo(name)])


def test_links_are_rejected_before_extraction():
    link = tarfile.TarInfo('static/link.py')
    link.type = tarfile.SYMTYPE
    link.linkname = '../private.py'
    with pytest.raises(ValueError, match='linked or special'):
        audit.validate_members(required_members() + [link])


def test_duplicate_paths_are_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        audit.validate_members(required_members() + [tarfile.TarInfo('cases.py')])


def test_missing_metadata_is_rejected():
    members = [m for m in required_members() if m.name != 'CITATION.cff']
    with pytest.raises(ValueError, match='lacks required'):
        audit.validate_members(members)

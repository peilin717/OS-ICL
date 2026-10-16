"""Current checkout citation must not identify an archived benchmark version."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import workflows


def test_citation_identifies_current_engine_version():
    citation = (ROOT / 'CITATION.cff').read_text(encoding='utf-8')
    version = re.search(r'^version:\s*([^\n]+)$', citation, re.MULTILINE)
    assert version is not None
    assert version.group(1).strip().strip('"\'') == workflows.VERSION


def test_development_citation_does_not_claim_release_date():
    if '-dev.' not in workflows.VERSION:
        return
    citation = (ROOT / 'CITATION.cff').read_text(encoding='utf-8')
    assert not re.search(r'^date-released:', citation, re.MULTILINE)
    message = re.search(r'^message:\s*([^\n]+)$', citation, re.MULTILINE)
    assert message is not None
    assert 'source revision' in message.group(1).lower()
    assert 'demonstration manifest' in message.group(1).lower()

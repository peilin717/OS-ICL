"""Static containment is not authentication or evaluation-agent isolation."""
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.request

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


@pytest.fixture
def isolated_static_service(tmp_path, monkeypatch):
    static = tmp_path / 'static'
    videos = tmp_path / 'videos'
    private = tmp_path / 'private'
    for directory in (static, videos, private):
        directory.mkdir()
    (static / 'index.html').write_text('public desktop fixture', encoding='utf-8')
    (videos / 'fixture.webm').write_bytes(b'public artifact fixture')
    (private / 'episode.json').write_text('private-demo-policy', encoding='utf-8')
    monkeypatch.setattr(server, 'STATIC', static)
    monkeypatch.setattr(server, 'VIDEOS', videos)
    http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    worker = threading.Thread(target=http.serve_forever, daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{http.server_port}', static, private
    finally:
        http.shutdown()
        http.server_close()
        worker.join(timeout=2)


@pytest.mark.parametrize('path', [
    '/../private/episode.json', '/../../private/episode.json',
    '/data/episodes/episode.json', '/workflows.py', '/protocols.py',
    '/..%2fprivate%2fepisode.json', '/artifacts/../episode.json',
])
def test_private_files_are_not_served_as_static_assets(isolated_static_service, path):
    base, _, _ = isolated_static_service
    with pytest.raises(urllib.error.HTTPError) as rejected:
        urllib.request.urlopen(base + path, timeout=5)
    assert rejected.value.code == 404
    assert b'private-demo-policy' not in rejected.value.read()


def test_static_and_artifact_routes_still_work(isolated_static_service):
    base, _, _ = isolated_static_service
    with urllib.request.urlopen(base + '/', timeout=5) as response:
        assert response.read() == b'public desktop fixture'
    with urllib.request.urlopen(base + '/artifacts/fixture.webm', timeout=5) as response:
        assert response.read() == b'public artifact fixture'


def test_static_symlink_cannot_escape_allowed_roots(isolated_static_service):
    base, static, private = isolated_static_service
    try:
        (static / 'linked.json').symlink_to(private / 'episode.json')
    except (OSError, NotImplementedError) as error:
        pytest.skip('Host does not permit creating test symlinks: ' + str(error))
    with pytest.raises(urllib.error.HTTPError) as rejected:
        urllib.request.urlopen(base + '/linked.json', timeout=5)
    assert rejected.value.code == 404
    assert b'private-demo-policy' not in rejected.value.read()

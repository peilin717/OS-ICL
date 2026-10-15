"""Stale development sessions cannot silently execute against a new reducer."""
import json
import sys
import threading
import urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import workflows as w
from test_v2_http import request


@pytest.mark.parametrize('plan', ['standard', 'module-demo'])
@pytest.mark.parametrize('stale', ['fingerprint', 'schema'])
def test_stale_reset_preserves_authoring_plan_and_rejects_actions(plan, stale):
    http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    worker = threading.Thread(target=http.serve_forever, daemon=True)
    worker.start()
    base = f'http://127.0.0.1:{http.server_port}'
    try:
        original = request(base, '/api/v2/sessions', {
            'case_id': 'OS-H-09', 'convention': 2, 'seed': 1001,
            'mode': 'evaluation', 'plan_variant': plan,
        })
        sid = original['id']
        assert original['compatible'] is True
        ep = server.SESSIONS[sid]['episode']
        if stale == 'schema':
            ep['schema_version'] = 0
        else:
            ep['implementation']['fingerprint'] = 'stale-test-fixture'
        saved = request(base, f'/api/v2/sessions/{sid}')
        assert saved['compatible'] is False
        assert 'plan_variant' not in saved and 'convention' not in saved
        before = json.dumps(ep['state'], sort_keys=True)
        for command, body in [('action', {'op': 'setting', 'key': 'privacy.method', 'value': 'remove'}),
                              ('ui-event', {'type': 'scroll', 'scrollTop': 112}),
                              ('finish', {}), ('replay', {})]:
            with pytest.raises(urllib.error.HTTPError) as exc:
                request(base, f'/api/v2/sessions/{sid}/{command}', body)
            assert exc.value.code == 409
        assert json.dumps(ep['state'], sort_keys=True) == before
        assert not server.SESSIONS[sid]['actions'] and not server.SESSIONS[sid]['ui_events']
        upgraded = request(base, f'/api/v2/sessions/{sid}/reset', {})
        assert upgraded['compatible'] is True
        assert upgraded['state_hash'] == original['state_hash']
        actual = server.SESSIONS[sid]['episode']
        expected = w.generate('OS-H-09', 2, 1001, plan)
        assert actual['plan_variant'] == plan and actual['reference'] == expected['reference']
        assert actual['schema_version'] == w.SCHEMA_VERSION
        assert actual['implementation'] == w.IMPLEMENTATION
    finally:
        http.shutdown()
        http.server_close()
        worker.join(timeout=2)

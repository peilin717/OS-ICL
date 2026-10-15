#!/usr/bin/env python3
"""Trusted stale-session fixture; recovery must use the visible reset button."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server
from audit_v2_browser import request
from playwright.sync_api import sync_playwright


def main():
    http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    server.Handler.log_message = lambda *_: None
    threading.Thread(target=http.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{http.server_port}'
    try:
        created = request(base, '/api/v2/sessions', {
            'case_id': 'OS-LH-09', 'convention': 2, 'seed': 1001,
            'mode': 'evaluation', 'plan_variant': 'reverse-sources',
        })
        sid = created['id']
        # Test fixture only: no hidden state is read by an evaluated agent.
        server.SESSIONS[sid]['episode']['implementation']['fingerprint'] = 'stale-ui-fixture'
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/google-chrome',
                                         headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1280, 'height': 720})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + f'/?session={sid}')
            page.get_by_role('heading', name='Session update required').wait_for()
            assert page.locator('.desktop').count() == 0
            text = page.locator('.brief').inner_text()
            assert 'pseudonym' not in text.lower() and 'reverse-sources' not in text
            page.get_by_role('button', name='Reset session').click()
            page.locator('.desktop').wait_for()
            updated = request(base, f'/api/v2/sessions/{sid}')
            assert updated['compatible'] and updated['state_hash'] == created['state_hash']
            assert server.SESSIONS[sid]['episode']['plan_variant'] == 'reverse-sources'
            page.goto(base + '/studio')
            page.locator('select[name="mode"]').select_option('practice')
            page.locator('select[name="plan_variant"]').select_option('configure-first')
            page.get_by_role('button', name='Create session').click()
            page.locator('.desktop').wait_for()
            author_sid = parse_qs(urlparse(page.url).query)['session'][0]
            assert server.SESSIONS[author_sid]['episode']['plan_variant'] == 'configure-first'
            page.goto(base + '/recording-studio.html')
            page.locator('#cases option').first.wait_for(state='attached')
            page.locator('select[name="plan_variant"]').select_option('reverse-sources')
            page.get_by_role('button', name='Open recording workspace').click()
            page.wait_for_url('**/recording.html?session=*')
            page.frame_locator('#os-frame').locator('#begin-demo').wait_for()
            recording_sid = parse_qs(urlparse(page.url).query)['session'][0]
            assert server.SESSIONS[recording_sid]['episode']['plan_variant'] == 'reverse-sources'
            assert server.SESSIONS[recording_sid]['mode'] == 'demo'
            assert not errors, errors
            print(json.dumps({'visible_upgrade_gate': True, 'reset_button_works': True,
                              'original_plan_preserved': True, 'authoring_plan_forms': True,
                              'browser_errors': errors}))
            browser.close()
    finally:
        http.shutdown()
        http.server_close()


if __name__ == '__main__':
    main()

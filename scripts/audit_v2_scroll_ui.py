#!/usr/bin/env python3
"""Trusted browser check: real wheel input must survive recording and replay.

No resource mutations or model calls are needed for this presentation test.
"""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

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
        session = request(base, '/api/v2/sessions', {
            'case_id': 'OS-LH-01', 'convention': 0, 'seed': 1001,
            'mode': 'practice',
        })
        sid = session['id']
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path='/usr/bin/google-chrome', headless=True,
                args=['--no-sandbox'],
            )
            page = browser.new_page(viewport={'width': 1280, 'height': 720})
            page.goto(base + f'/?session={sid}')
            page.locator('.desktop').wait_for()
            page.locator('.taskbar [data-open="settings"]').click()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            page.locator('[data-command="settings-page"][data-target="Storage & backup"]').click()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            # Ordinary resize gesture creates a realistically short window.
            handle = page.locator('.window').last.locator('.resize-handle')
            box = handle.bounding_box()
            page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            page.mouse.down()
            page.mouse.move(box['x'] + box['width']/2, box['y'] - 200, steps=8)
            page.mouse.up()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            panel = page.locator('.window').last.locator('.settings-main')
            geometry = panel.evaluate('(el)=>({height:el.clientHeight,total:el.scrollHeight})')
            assert geometry['total'] > geometry['height'], geometry
            panel.hover()
            page.mouse.wheel(0, 400)
            page.wait_for_function('document.querySelector(".settings-main").scrollTop > 0')
            page.wait_for_timeout(150)
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            observed = panel.evaluate('(el)=>el.scrollTop')
            trace = server.SESSIONS[sid]['ui_events']
            scrolls = [event for event in trace if event['type'] == 'scroll']
            assert scrolls, f'Wheel moved panel to {observed}px but no scroll was recorded'
            assert scrolls[-1]['scrollTop'] == observed, (scrolls[-1], observed)
            # Isolated presentation replay: navigation has no benchmark result,
            # so supply a fresh real initial session through a test-only route.
            # Never mark an unfinished workflow successful to bypass the gate.
            clone = request(base, '/api/v2/sessions', {
                'case_id': 'OS-LH-01', 'convention': 0, 'seed': 1001,
                'mode': 'practice',
            })
            replay_payload = {'session': clone, 'trace': trace,
                              'expected_hash': session['state_hash']}
            page.route('**/api/v2/sessions/' + sid + '/replay',
                       lambda route: route.fulfill(json=replay_payload))
            page.goto(base + f'/?session={sid}&replay=1&audit_speed=fast')
            page.wait_for_function('window.__REPLAY_DONE__ || window.__REPLAY_ERROR__', timeout=30000)
            error = page.evaluate('window.__REPLAY_ERROR__ || null')
            assert not error, error
            replayed = page.locator('.settings-main').evaluate('(el)=>el.scrollTop')
            assert replayed == observed, (replayed, observed)
            # A normal setting change must not jump the user's scroll position
            # back to the top of the same panel after the state refresh.
            page.locator('select[data-key="backup.include-text"]').select_option('false')
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            after_change = page.locator('.settings-main').evaluate('(el)=>el.scrollTop')
            assert after_change == observed, f'Setting change lost scroll position: {observed} -> {after_change}'
            power_tab = page.locator('[data-command="settings-page"][data-target="Power & scheduling"]')
            # A tab click may naturally scroll that offscreen control into view.
            # Preserve the real position at departure, not an earlier offset.
            power_tab.scroll_into_view_if_needed()
            departure = page.locator('.settings-main').evaluate('(el)=>el.scrollTop')
            power_tab.click()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            assert page.locator('.settings-main').evaluate('(el)=>el.scrollTop') == 0
            page.locator('[data-command="settings-page"][data-target="Storage & backup"]').click()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            assert page.locator('.settings-main').evaluate('(el)=>el.scrollTop') == departure
            page.locator('.settings-main').hover()
            page.mouse.wheel(0, 400)
            page.wait_for_function('document.querySelector(".settings-main").scrollTop > 0')
            page.wait_for_timeout(150)
            restored_offset = page.locator('.settings-main').evaluate('(el)=>el.scrollTop')
            page.locator('.window').last.locator('[data-command="minimize"]').click()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            page.locator('.taskbar [data-open="settings"]').click()
            page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            assert page.locator('.settings-main').evaluate('(el)=>el.scrollTop') == restored_offset
            print(json.dumps({'settings_wheel_recorded': True, 'replay_scrollTop': replayed,
                              'setting_change_preserves_scroll': True, 'page_offsets_independent': True,
                              'minimize_restore_preserves_scroll': True}))
            browser.close()
    finally:
        http.shutdown()
        http.server_close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Exercise visible failed-transfer diagnosis, adapter repair and retry."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
from audit_v2_browser import request, Desktop
from playwright.sync_api import sync_playwright


def main():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    server.Handler.log_message=lambda *_:None
    threading.Thread(target=http.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{http.server_port}'
    try:
        session=request(base,'/api/v2/sessions',{'case_id':'OS-LH-06','convention':0,'seed':1001,'mode':'practice'})
        sid=session['id']
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            page.goto(base+f'/?session={sid}')
            page.locator('.desktop').wait_for()
            ui=Desktop(page)
            win=ui.front('transfers')
            ui.click(win.locator('[data-command="download"][data-target="download-0"]'))
            if page.locator('[data-command="dismiss-notice"]').count():
                ui.click(page.locator('[data-command="dismiss-notice"]'))
            ui.click(win.locator('[data-command="section"][data-target="Failed"]'))
            card=page.locator('.setting-card').filter(has=page.locator('[data-target="download-0"]'))
            assert 'Attempts: 1' in card.inner_text() and 'Field relay' in card.inner_text()
            assert card.locator('[data-command="download"]').inner_text()=='Retry'
            win=ui.front('devices')
            ui.click(win.locator('[data-command="device"][data-target="field-relay"]'))
            win=ui.front('transfers')
            ui.click(win.locator('[data-command="download"][data-target="download-0"]'))
            assert win.locator('.setting-card').count()==0
            ui.click(win.locator('[data-command="section"][data-target="Completed"]'))
            card=page.locator('.setting-card').filter(has=page.locator('[data-target="download-0"]'))
            assert '100%' in card.inner_text() and 'Attempts: 2' in card.inner_text()
            assert card.locator('[data-command="download"]').is_disabled()
            print(json.dumps({'failure_message_visible':True,'retry_label_visible':True,'adapter_repaired_via_ui':True,'completed_after_retry':True}))
            browser.close()
    finally:
        http.shutdown();http.server_close()


if __name__=='__main__':
    main()

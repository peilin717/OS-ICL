#!/usr/bin/env python3
"""Browser display regression; API actions prepare fixtures, not agent runs."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
from audit_v2_browser import request
from playwright.sync_api import sync_playwright


def main():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    server.Handler.log_message=lambda *_:None
    threading.Thread(target=http.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{http.server_port}'
    try:
        session=request(base,'/api/v2/sessions',{'case_id':'OS-LH-11','convention':1,'seed':173,'mode':'practice'})
        sid=session['id']
        # Trusted authoring fixture, never exposed to evaluated agents.
        reference=server.SESSIONS[sid]['episode']['reference']
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            def observe():
                page.goto(base+f'/?session={sid}')
                page.locator('.desktop').wait_for()
                page.locator('.taskbar [data-open="monitor"]').click()
                page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                page.locator('[data-command="section"][data-target="performance"]').click()
                page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                values=page.locator('.performance strong').all_text_contents()
                return dict(zip(['count','used','cache','released'],[int(v.replace(',','').replace(' B','')) for v in values]))
            before=observe()
            for action in reference:
                request(base,f'/api/v2/sessions/{sid}/action',action)
            after=observe()
            assert before['cache']>0 and after['cache']==0
            assert after['released']==before['cache']
            assert page.locator('.settings-main').inner_text().find('Lossless DEFLATE')>=0
            assert '12%' not in page.locator('.settings-main').inner_text()
            print(json.dumps({'before':before,'after':after,'compressed_artifact_visible':True},indent=2))
            browser.close()
    finally:
        http.shutdown();http.server_close()


if __name__=='__main__':
    main()

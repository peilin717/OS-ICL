#!/usr/bin/env python3
"""Inspect default app geometry and window controls at desktop aspect ratios."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
from playwright.sync_api import sync_playwright


def main():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    server.Handler.log_message=lambda *_:None
    thread=threading.Thread(target=http.serve_forever,daemon=True)
    thread.start()
    results=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            for width,height in [(1280,720),(1600,900),(1920,1080)]:
                context=browser.new_context(viewport={'width':width,'height':height})
                page=context.new_page()
                page.goto(f'http://127.0.0.1:{http.server_port}/')
                page.locator('.desktop').wait_for()
                for app in ['files','editor','settings','scheduler','transfers','monitor','devices','events','terminal']:
                    page.locator(f'.taskbar [data-open="{app}"]').click()
                    page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                    box=page.locator('.window').last.bounding_box()
                    assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height-48+1,(app,box)
                win=page.locator('.window').last
                win.locator('[data-command="maximize"]').click()
                page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                box=page.locator('.window').last.bounding_box()
                assert round(box['width'])==width and round(box['height'])==height-48
                page.locator('.window').last.locator('[data-command="minimize"]').click()
                page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                page.locator('.taskbar [data-open="terminal"]').click()
                page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                assert page.locator('.window').last.is_visible()
                results.append({'viewport':[width,height],'apps_checked':9,'bounded_windows':True,'maximize_minimize_restore':True})
                context.close()
            browser.close()
    finally:
        http.shutdown();http.server_close()
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()

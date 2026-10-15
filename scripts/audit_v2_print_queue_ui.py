#!/usr/bin/env python3
"""Trusted completed fixture, followed by ordinary visible queue controls."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
from audit_v2_browser import request,Desktop
from playwright.sync_api import sync_playwright


def main():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    server.Handler.log_message=lambda *_:None
    threading.Thread(target=http.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{http.server_port}'
    try:
        session=request(base,'/api/v2/sessions',{'case_id':'OS-LH-05','convention':1,'seed':1001,'mode':'practice'})
        sid=session['id']
        for action in server.SESSIONS[sid]['episode']['reference']:
            request(base,f'/api/v2/sessions/{sid}/action',action)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+f'/?session={sid}')
            page.locator('.desktop').wait_for()
            ui=Desktop(page)
            win=ui.front('devices')
            ui.click(win.locator('[data-command="section"][data-target="print-queue"]'))
            assert 'Queued' in win.locator('.setting-card').inner_text()
            assert '5 pages' in win.locator('.setting-card').inner_text()
            ui.click(win.get_by_role('button',name='Pause',exact=True))
            assert 'Paused' in win.locator('.setting-card').inner_text()
            ui.click(win.get_by_role('button',name='Resume',exact=True))
            assert 'Queued' in win.locator('.setting-card').inner_text()
            ui.click(win.get_by_role('button',name='Cancel',exact=True))
            assert 'Cancelled' in win.locator('.setting-card').inner_text()
            assert win.get_by_role('button',name='Resume',exact=True).count()==0
            assert not errors,errors
            print(json.dumps({'queue_visible':True,'pause_resume_cancel_via_ui':True,'page_errors':errors}))
            browser.close()
    finally:http.shutdown();http.server_close()


if __name__=='__main__':main()

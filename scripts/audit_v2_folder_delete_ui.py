#!/usr/bin/env python3
"""Visible folder deletion and lock regression with a trusted virtual fixture."""
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
        session=request(base,'/api/v2/sessions',{'case_id':'OS-LH-01','convention':0,'seed':1002,'mode':'practice'})
        sid=session['id']
        def create(action):
            return request(base,f'/api/v2/sessions/{sid}/action',action)['last_event']['outcome']
        folder=create({'op':'mkdir','parent':'documents','name':'Disposable folder'})
        nested=create({'op':'mkdir','parent':folder,'name':'Nested'})
        document=create({'op':'create-document','parent':nested,'name':'notes.txt','content':'Virtual test fixture'})
        # Only the initial lock is injected; the repair and deletion use UI.
        server.SESSIONS[sid]['episode']['state']['processes'][0]['locks']=[document]
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(base+f'/?session={sid}')
            page.locator('.desktop').wait_for()
            ui=Desktop(page);ui.base=base;ui.sid=sid
            win=ui.folder('documents')
            ui.click(win.locator(f'.file-row[data-target="{folder}"]'))
            ui.click(win.locator('[data-command="delete"]'))
            assert 'in use' in page.locator('.notification').inner_text()
            state=request(base,f'/api/v2/sessions/{sid}')['state']
            assert all(not f['deleted'] for f in state['files'] if f['id'] in {folder,nested,document})
            ui.click(page.locator('[data-command="dismiss-notice"]'))
            ui.action({'op':'process','target':'indexer','status':'Paused'})
            win=ui.folder('documents')
            ui.click(win.locator(f'.file-row[data-target="{folder}"]'))
            ui.click(win.locator('[data-command="delete"]'))
            assert win.locator(f'.file-row[data-target="{folder}"]').count()==0
            state=request(base,f'/api/v2/sessions/{sid}')['state']
            assert all(f['deleted'] for f in state['files'] if f['id'] in {folder,nested,document})
            assert not errors,errors
            print(json.dumps({'locked_subtree_rejected':True,'pause_via_ui':True,'entire_subtree_deleted':True,'browser_errors':errors}))
            browser.close()
    finally:
        http.shutdown();http.server_close()


if __name__=='__main__':main()

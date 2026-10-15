#!/usr/bin/env python3
"""File clipboard shortcuts must not act on files while editing search text."""
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
        created=request(base,'/api/v2/sessions',{'case_id':'OS-LH-01','convention':0,'seed':42,'mode':'practice'})
        sid=created['id']
        result=request(base,f'/api/v2/sessions/{sid}/action',{'op':'create-document','parent':'documents','name':'Clipboard focus source.txt'})
        source=result['last_event']['outcome']
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            # Do not read/write the host clipboard. Cancel the browser's native
            # clipboard default only; the application's key handler still runs.
            page.add_init_script('''document.addEventListener('keydown',event=>{
                if(event.ctrlKey&&['c','x','v'].includes(event.key.toLowerCase()))event.preventDefault();
            },true)''')
            page.goto(base+f'/?session={sid}');page.locator('.desktop').wait_for()
            def idle():page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            def click(locator):locator.click();idle()
            click(page.locator('.taskbar [data-open="files"]'))
            click(page.locator('.navigation [data-target="documents"]'))
            click(page.locator(f'.file-row[data-target="{source}"]'))
            click(page.locator('[data-command="copy"]'))
            click(page.locator('.navigation [data-target="downloads"]'))
            search=page.locator('input[data-field="search"]')
            search.fill('Nothing matches this text');idle()
            before=request(base,f'/api/v2/sessions/{sid}')['state']
            search.press('Control+v');idle()
            after=request(base,f'/api/v2/sessions/{sid}')['state']
            assert after['files']==before['files'],'Pasting into search performed a file paste'
            assert page.locator('.notification').count()==0,'Text shortcut emitted a file operation notice'
            search=page.locator('input[data-field="search"]');search.fill('');idle()
            click(page.locator('.navigation [data-target="downloads"]'))
            page.keyboard.press('Control+v');idle()
            after=request(base,f'/api/v2/sessions/{sid}')['state']
            copied=[f for f in after['files'] if f['parent']=='downloads' and f.get('source')==source and not f['deleted']]
            assert len(copied)==1,'Virtual file paste stopped working outside text inputs'
            click(page.locator('[data-command="new-folder"]'))
            page.locator('.dialog input[name="name"]').focus()
            page.keyboard.press('Escape');idle()
            assert page.locator('.dialog').count()==0,'Escape did not cancel a dialog with text focus'
            print(json.dumps({'text_focus_has_no_file_side_effects':True,'file_shortcut_still_works':True,
                              'host_clipboard_accessed':False,'escape_cancels_focused_dialog':True}))
            browser.close()
    finally:http.shutdown();http.server_close()


if __name__=='__main__':main()

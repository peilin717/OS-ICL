#!/usr/bin/env python3
"""Observe actual property-panel visibility during normal browser replay.

An isolated presentation fixture, not a completed benchmark demonstration.
"""
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
    body={'case_id':'OS-LH-01','convention':0,'seed':1001,'mode':'practice'}
    try:
        original=request(base,'/api/v2/sessions',body)
        sid=original['id']
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            page.goto(base+f'/?session={sid}')
            page.locator('.desktop').wait_for()
            def click(locator):
                locator.click()
                page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            click(page.locator('.taskbar [data-open="files"]'))
            click(page.locator('.navigation [data-target="documents"]'))
            click(page.locator('.file-row').first)
            click(page.locator('[data-command="properties"]').first)
            assert page.locator('.dialog pre').is_visible()
            approved_visible=page.locator('.dialog pre').evaluate('''el=>{
                const index=el.textContent.indexOf('"approved"');
                const range=document.createRange();range.setStart(el.firstChild,index);range.setEnd(el.firstChild,index+10);
                const text=range.getBoundingClientRect(),panel=el.closest('.dialog').getBoundingClientRect();
                return index>=0&&text.top>=panel.top&&text.bottom<=panel.bottom;
            }''')
            assert approved_visible,'Approval metadata is clipped out of the property panel'
            click(page.locator('.dialog button[type="submit"]'))
            trace=server.SESSIONS[sid]['ui_events']
            final=request(base,f'/api/v2/sessions/{sid}')
            clone=request(base,'/api/v2/sessions',body)
            payload={'session':clone,'trace':trace,'expected_hash':final['state_hash']}
            page.route('**/api/v2/sessions/'+sid+'/replay',lambda route:route.fulfill(json=payload))
            page.add_init_script('''
                window.__PROPERTY_INTERVALS__=[];
                addEventListener('DOMContentLoaded',()=>{
                    let since=null;
                    new MutationObserver(()=>{
                        const shown=!!document.querySelector('.dialog pre');
                        if(shown&&since===null)since=performance.now();
                        if(!shown&&since!==null){window.__PROPERTY_INTERVALS__.push(performance.now()-since);since=null}
                    }).observe(document.body,{childList:true,subtree:true});
                });
            ''')
            page.goto(base+f'/?session={sid}&replay=1')
            page.wait_for_function('window.__REPLAY_DONE__ || window.__REPLAY_ERROR__',timeout=30000)
            error=page.evaluate('window.__REPLAY_ERROR__ || null')
            assert not error,error
            intervals=page.evaluate('window.__PROPERTY_INTERVALS__')
            assert len(intervals)==1 and intervals[0]>=2500,intervals
            print(json.dumps({'property_visibility_ms':intervals[0],'approval_metadata_visible':True,
                              'replay_hash_verified':True,'scope':'isolated presentation replay'}))
            browser.close()
    finally:
        http.shutdown();http.server_close()


if __name__=='__main__':
    main()

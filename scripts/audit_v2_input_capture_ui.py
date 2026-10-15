#!/usr/bin/env python3
"""Native multiline inputs retain their trace without repeated replay pauses.

The replay route is an isolated unfinished presentation fixture, not a
successful benchmark demonstration or evaluated-agent run.
"""
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
        session=request(base,'/api/v2/sessions',{'case_id':'OS-LH-01','convention':0,'seed':1002,'mode':'demo'})
        sid=session['id']
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+session['launch_url'])
            page.locator('#begin-demo').click()
            ui=Desktop(page);ui.base=base;ui.sid=sid
            ui.action({'op':'create-document','parent':'documents','name':'Capture test.txt'})
            measurements=[]
            for text in ['A single replacement input.',json.dumps({'project':'Capture fixture','entry':'/Projects/Example/Preparation/ready-application.js','resources':['application.js','notes.txt','config.json','assets.csv']},indent=2)]:
                before=len(server.SESSIONS[sid]['ui_events'])
                page.locator('textarea').fill(text);ui.idle()
                captured=server.SESSIONS[sid]['ui_events'][before:]
                inputs=[e for e in captured if e['type']=='input' and 'TEXTAREA' in e['selector']]
                measurements.append({'textarea_inputs_for_one_fill':len(inputs),
                                     'unique_values':len({e.get('value') for e in inputs}),
                                     'replacement_length':len(text)})
                print(json.dumps(measurements[-1]),flush=True)
                assert inputs and all(e['value']==text for e in inputs)
            print(json.dumps({'measurements':measurements,'browser_errors':errors}),flush=True)
            trace=server.SESSIONS[sid]['ui_events']
            final=request(base,f'/api/v2/sessions/{sid}')
            clone=request(base,'/api/v2/sessions',{'case_id':'OS-LH-01','convention':0,'seed':1002,'mode':'practice'})
            payload={'session':clone,'trace':trace,'expected_hash':final['state_hash']}
            page.route('**/api/v2/sessions/'+sid+'/replay',lambda route:route.fulfill(json=payload))
            page.add_init_script('''
                window.__TEXT_DWELLS__=[];
                const nativeTimer=window.setTimeout.bind(window);
                window.setTimeout=(callback,delay,...args)=>{
                    if(delay===700)window.__TEXT_DWELLS__.push(delay);
                    return nativeTimer(callback,delay,...args);
                };
            ''')
            page.goto(base+f'/?session={sid}&replay=1')
            page.wait_for_function('window.__REPLAY_DONE__ || window.__REPLAY_ERROR__',timeout=30000)
            error=page.evaluate('window.__REPLAY_ERROR__ || null')
            assert not error,error
            dwells=page.evaluate('window.__TEXT_DWELLS__')
            assert len(dwells)==4,dwells
            assert page.locator('textarea').input_value()==text
            print(json.dumps({'changed_text_values':2,'reading_pauses':len(dwells),
                              'duplicate_native_events_preserved':True,'replay_hash_verified':True,
                              'scope':'isolated presentation replay'}),flush=True)
            assert not errors,errors
            browser.close()
    finally:
        http.shutdown();http.server_close()


if __name__=='__main__':main()

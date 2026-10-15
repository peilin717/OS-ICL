#!/usr/bin/env python3
"""Human editor safety: switching documents must not silently discard a draft."""
import json
import copy
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
import workflows as w
from audit_v2_browser import request
from playwright.sync_api import sync_playwright


def main():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    server.Handler.log_message=lambda *_:None
    threading.Thread(target=http.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{http.server_port}'
    try:
        session=request(base,'/api/v2/sessions',{'case_id':'OS-LH-01','convention':0,'seed':42,'mode':'practice'})
        sid=session['id']
        # Trusted fixture only; these documents are not a scored demonstration.
        identifiers=[]
        for name in ['Draft safety first.txt','Draft safety second.txt']:
            result=request(base,f'/api/v2/sessions/{sid}/action',{'op':'create-document','parent':'documents','name':name})
            identifiers.append(result['last_event']['outcome'])
        owner=server.SESSIONS[sid]['episode']['state']['processes'][0]
        owner['locks'].append(identifiers[0])
        fixture=copy.deepcopy(server.SESSIONS[sid]['episode']['state'])
        server.SESSIONS[sid]['episode']['initial']=copy.deepcopy(fixture)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720})
            page.goto(base+f'/?session={sid}')
            page.locator('.desktop').wait_for()
            def idle():page.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
            page.locator('.taskbar [data-open="editor"]').click();idle()
            def choose(identifier):
                page.locator('[data-command="choose-document"]').click();idle()
                # Real mouse + keyboard type-ahead, not DOM select_option.
                state=request(base,f'/api/v2/sessions/{sid}')['state']
                page.locator('.dialog select[name="target"]').click()
                page.keyboard.press('Home')
                page.keyboard.type(w.path(state,identifier),delay=15)
                page.keyboard.press('Enter');idle()
                assert page.locator('.dialog select[name="target"]').input_value()==identifier
                page.locator('.dialog button[type="submit"]').click();idle()
            choose(identifiers[0])
            page.locator('textarea').fill('Unsaved draft must survive document switching.');idle()
            choose(identifiers[1])
            assert page.locator('.dialog').get_by_text('Save changes?',exact=True).is_visible(), 'Open silently discarded the unsaved draft'
            page.locator('[data-command="cancel"]').click();idle()
            assert page.locator('textarea').input_value()=='Unsaved draft must survive document switching.'
            assert 'Draft safety first.txt' in page.locator('.titlebar').inner_text()
            choose(identifiers[0])  # Choosing the same document must retain its draft.
            assert page.locator('.dialog').count()==0
            assert page.locator('textarea').input_value()=='Unsaved draft must survive document switching.'
            page.locator('.taskbar [data-open="monitor"]').click();idle()
            page.locator(f'[data-command="process"][data-target="{owner["id"]}"]').click();idle()
            page.locator('.taskbar [data-open="editor"]').click();idle()
            choose(identifiers[1])
            page.locator('[data-command="save-changes"]').click();idle()
            state=request(base,f'/api/v2/sessions/{sid}')['state']
            first=next(f for f in state['files'] if f['id']==identifiers[0])
            assert first['content']=='Unsaved draft must survive document switching.'
            assert 'Draft safety second.txt' in page.locator('.window').last.locator('.titlebar').inner_text()
            assert page.locator('textarea').input_value()==''
            page.locator('textarea').fill('Discard only this unsaved draft.');idle()
            choose(identifiers[0])
            page.locator('[data-command="discard-changes"]').click();idle()
            state=request(base,f'/api/v2/sessions/{sid}')['state']
            assert next(f for f in state['files'] if f['id']==identifiers[1])['content']==''
            assert page.locator('textarea').input_value()==first['content']
            page.locator('textarea').fill('Failed saves must not open the next document.');idle()
            page.locator('.taskbar [data-open="monitor"]').click();idle()
            page.locator(f'[data-command="process"][data-target="{owner["id"]}"]').click();idle()
            page.locator('.taskbar [data-open="editor"]').click();idle()
            choose(identifiers[1])
            page.locator('[data-command="save-changes"]').click();idle()
            assert page.locator('.dialog').get_by_text('Save changes?',exact=True).is_visible()
            assert 'Draft safety first.txt' in page.locator('.window').last.locator('.titlebar').inner_text()
            assert page.locator('textarea').input_value()=='Failed saves must not open the next document.'
            state=request(base,f'/api/v2/sessions/{sid}')['state']
            assert next(f for f in state['files'] if f['id']==identifiers[0])['content']==first['content']
            page.locator('[data-command="cancel"]').click();idle()
            dismiss=page.locator('[data-command="dismiss-notice"]')
            if dismiss.count():dismiss.click();idle()
            page.locator('.taskbar [data-open="monitor"]').click();idle()
            page.locator(f'[data-command="process"][data-target="{owner["id"]}"]').click();idle()
            page.locator('.taskbar [data-open="editor"]').click();idle()
            choose(identifiers[1])
            page.locator('[data-command="save-changes"]').click();idle()
            state=request(base,f'/api/v2/sessions/{sid}')['state']
            assert next(f for f in state['files'] if f['id']==identifiers[0])['content']=='Failed saves must not open the next document.'
            assert 'Draft safety second.txt' in page.locator('.window').last.locator('.titlebar').inner_text()
            final=request(base,f'/api/v2/sessions/{sid}')
            trace=copy.deepcopy(server.SESSIONS[sid]['ui_events'])
            clone=request(base,'/api/v2/sessions',{'case_id':'OS-LH-01','convention':0,'seed':42,'mode':'practice'})
            clone_ep=server.SESSIONS[clone['id']]['episode']
            clone_ep['initial']=copy.deepcopy(fixture);clone_ep['state']=copy.deepcopy(fixture)
            clone_public=request(base,f"/api/v2/sessions/{clone['id']}")
            payload={'session':clone_public,'trace':trace,'expected_hash':final['state_hash']}
            # Isolated fixture replay transport; no fake benchmark success.
            page.route('**/api/v2/sessions/'+sid+'/replay',lambda route:route.fulfill(json=payload))
            page.goto(base+f'/?session={sid}&replay=1&audit_speed=fast')
            page.wait_for_function('window.__REPLAY_DONE__ || window.__REPLAY_ERROR__',timeout=30000)
            error=page.evaluate('window.__REPLAY_ERROR__ || null')
            assert not error,error
            print(json.dumps({'open_unsaved_prompt':True,'cancel_preserves_draft':True,
                              'save_then_open':True,'discard_then_open':True,'same_file_keeps_draft':True,
                              'failed_save_keeps_original_and_draft':True,'retry_after_owner_pause':True,
                              'native_keyboard_selection':True,'fixture_replay_hash_verified':True}))
            browser.close()
    finally:
        http.shutdown();http.server_close()


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Verify scaled authoring keeps the child's canonical coordinates intact."""
import json
import sys
import threading
import urllib.request
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
    base=f'http://127.0.0.1:{http.server_port}'
    rows=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            studio=browser.new_page(viewport={'width':1600,'height':900})
            studio.goto(base+'/recording-studio.html')
            studio.locator('#cases option').first.wait_for(state='attached')
            studio.locator('#cases').select_option('OS-LH-05')
            studio.locator('button[type="submit"]').click()
            studio.frame_locator('#os-frame').locator('#begin-demo').wait_for()
            studio.frame_locator('#os-frame').locator('#begin-demo').click()
            studio.frame_locator('#os-frame').locator('.desktop').wait_for()
            studio.close()
            for width,height in [(1024,768),(1600,900),(1920,1080)]:
                request=urllib.request.Request(base+'/api/v2/sessions',data=json.dumps({'mode':'practice','seed':1002}).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request) as response:session=json.loads(response.read())
                page=browser.new_page(viewport={'width':width,'height':height})
                page.goto(base+'/recording.html?session='+session['id'])
                frame=page.frame_locator('#os-frame')
                frame.locator('.desktop').wait_for()
                child=page.frames[1]
                viewport=child.evaluate('({width:innerWidth,height:innerHeight})')
                assert viewport=={'width':1280,'height':720}
                rect=frame.locator('[data-command="start"]').evaluate('(el)=>{const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}}')
                frame.locator('[data-command="start"]').click()
                child.evaluate('async()=>await window.__OS_WAIT_IDLE__()')
                trace=server.SESSIONS[session['id']]['ui_events']
                assert abs(trace[-1]['x']-rect['x'])<2 and abs(trace[-1]['y']-rect['y'])<2,(trace[-1],rect)
                rows.append({'outer_viewport':[width,height],'logical_viewport':viewport,'canonical_click_coordinates':True})
                page.close()
            browser.close()
    finally:
        http.shutdown();http.server_close()
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    main()

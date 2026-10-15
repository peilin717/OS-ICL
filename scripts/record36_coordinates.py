#!/usr/bin/env python3
"""Oracle-assisted computer-use authoring: screenshots + mouse/keyboard only.

The trusted author knows the rules/fixtures. State reads verify input delivery;
they never mutate the live episode. No DOM selectors, accessibility tree,
DOM state access, semantic-action HTTP or injected event dispatch are used.
The existing application-idle promise is awaited only for input synchronization.
The existing server records the real browser input and renders verified replay.
"""
import argparse,copy,json,time,sys,traceback,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'workflows.py').exists():ROOT=Path('/root/VideoICL-bench/OS-ICL')
sys.path.insert(0,str(ROOT))
import workflows as w
import tasks36
from playwright.sync_api import sync_playwright

APP={'files':88,'editor':128,'settings':168,'scheduler':208,'transfers':248,'monitor':288,'devices':328,'events':368,'terminal':408}
KINDS=['inventory','validate','dry-run','index','build','test','sign','backup','restore','compare','transcode','catalogue','layout','proof','cache','migrate','redact','replicate','compact','package','verify','audit','verify-backup','deliver']


def request(base,path,body=None):
    req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=60))


class Author:
    def __init__(self,page,episode,directory):
        self.p=page;self.ep=episode;self.s=copy.deepcopy(episode['initial']);self.directory=directory
        self.current=None;self.folder='project';self.step=0;self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)))
        self.pending=set();self.last_network=time.monotonic()
        def started(req):self.pending.add(req);self.last_network=time.monotonic()
        def ended(req):self.pending.discard(req);self.last_network=time.monotonic()
        self.p.on('request',started);self.p.on('requestfinished',ended);self.p.on('requestfailed',ended)
    def pause(self,ms=80):
        self.p.wait_for_timeout(ms);deadline=time.monotonic()+30
        while self.pending or time.monotonic()-self.last_network<0.07:
            if time.monotonic()>deadline:raise TimeoutError('Browser requests did not settle')
            self.p.wait_for_timeout(35)
        self.p.evaluate('window.__OS_WAIT_IDLE__ ? window.__OS_WAIT_IDLE__() : null')
    def click(self,x,y):self.p.mouse.click(x,y);self.pause()
    def capture(self,label):self.p.screenshot(path=str(self.directory/f'{self.step:03}-{label}.png'))
    def open_app(self,app):
        if self.current==app:return
        if self.current:self.click(1117,58)
        self.click(APP[app],697);self.current=app
        if app=='files':self.folder='project'
    def native(self,x,y,index):
        self.click(x,y);self.p.keyboard.press('Home')
        for _ in range(index):self.p.keyboard.press('ArrowDown')
        self.p.keyboard.press('Enter');self.pause(200)
    def type_at(self,x,y,text):
        self.click(x,y);self.p.keyboard.press('Control+a');self.p.keyboard.insert_text(str(text));self.pause()
    def files(self):return [f for f in self.s['files'] if not f.get('deleted')]
    def get(self,identifier):return next(f for f in self.files() if f['id']==identifier)
    def children(self,folder):return sorted([f for f in self.files() if f['parent']==folder],key=lambda f:f['name'].lower())
    def navigate(self,target):
        self.open_app('files')
        ancestors=[];f=self.get(target)
        while f['id'] not in {'project','documents','downloads','desktop','projects'}:
            ancestors.append(f['id']);f=self.get(f['parent'])
        root=f['id'];sidebar={'project':111,'projects':152,'documents':193,'downloads':234,'desktop':275}
        self.click(205,sidebar[root]);self.folder=root
        for child in reversed(ancestors):
            index=[x['id'] for x in self.children(self.folder)].index(child)
            self.p.mouse.click(480,225+40*index,click_count=2);self.pause();self.folder=child
    def select_file(self,identifier):
        f=self.get(identifier);self.navigate(f['parent']);index=[x['id'] for x in self.children(self.folder)].index(identifier)
        if index>=9:raise RuntimeError('Uncalibrated file-list scroll; review screenshot before continuing')
        self.click(480,225+40*index)
    def inspect_properties(self,identifier):
        self.select_file(identifier);self.click(780,148);self.pause(450);self.capture('properties');self.p.keyboard.press('Escape');self.pause()
    def document(self,identifier,read=True):
        self.open_app('editor');self.click(172,98)
        docs=[f['id'] for f in self.files() if f['kind']!='folder']
        self.native(640,363,docs.index(identifier));self.click(858,426);self.pause(450)
        if read:
            self.capture('document-input')
            text=self.get(identifier)['content']
            if len(text.splitlines())>18:
                self.p.mouse.move(740,420);self.p.mouse.wheel(0,550);self.pause(450);self.capture('document-lower');self.p.mouse.wheel(0,-2000);self.pause(200)
    def job(self,identifier):
        self.open_app('scheduler');self.click(210,111)
        index=[x['id'] for x in self.s['jobs']].index(identifier)
        if index>=7:raise RuntimeError('Uncalibrated job scroll')
        self.click(480,185+41*index)
    def create_job(self,a):
        self.open_app('scheduler');self.click(922,106);self.type_at(510,254,a['name'])
        self.native(760,254,KINDS.index(a['kind']))
        folders=[f['id'] for f in self.files() if f['kind']=='folder']
        self.native(640,323,folders.index(a['input']));self.native(640,392,folders.index(a['output']))
        names=['']+[j['name'] for j in self.s['jobs']];self.native(510,460,names.index(a.get('dependency','')))
        self.native(760,460,['manual','idle','plugged-in'].index(a.get('trigger','manual')));self.capture('task-configuration');self.click(858,534)
    def setting(self,a):
        self.open_app('settings');key,value=a['key'],a['value']
        if key=='media.preview':
            self.click(184,194);self.click(500,170);index=['compact','review','detail'].index(value);self.native(1010,298,index)
        elif key.startswith('printer.'):
            self.click(194,235);choices={'paper':['A4','Letter'],'duplex':[True,False],'order':['forward','reverse']}
            row={'paper':1,'duplex':2,'order':3}[key.split('.')[1]];self.native(1010,298+89*row,choices[key.split('.')[1]].index(value))
        elif key=='privacy.method':
            self.click(180,276);self.native(1010,476,['mask','remove','pseudonym'].index(value))
        else:raise RuntimeError('Uncalibrated setting '+key)
        self.pause(350);self.capture('setting-saved')
    def action(self,a):
        op=a['op']
        if op in {'copy','move'}:
            self.select_file(a['target']);self.click(530 if op=='copy' else 573,148);self.navigate(a['parent']);self.click(617,148)
        elif op=='rename':
            self.select_file(a['target']);self.click(666,148)
            self.type_at(640,363,a['name']);self.click(858,426);self.pause(250)
        elif op=='delete':self.select_file(a['target']);self.click(721,148)
        elif op=='write':
            self.document(a['target']);self.type_at(650,250,a['content']);self.capture('document-edited');self.click(231,98);self.pause(350);self.capture('document-saved')
        elif op=='process':
            self.open_app('monitor');index=[p['id'] for p in self.s['processes']].index(a['target'])
            self.p.mouse.move(800,400);self.p.mouse.wheel(0,-3000);self.pause()
            if index<5:self.click(1062,194+89*index)
            else:
                self.p.mouse.wheel(0,1000);self.pause();self.capture('process-scroll');self.click(1062,567)
        elif op=='device':
            self.open_app('devices');device=next(d for d in self.s['devices'] if d['id']==a['target'])
            category=device['kind'];self.click(200,{'Camera':153,'Printer':194,'Network storage':235}[category])
            group=[d for d in self.s['devices'] if d['kind']==category];index=[d['id'] for d in group].index(a['target'])
            if device['connected']!=a['connected']:self.click(1057,(229+100*index) if category=='Network storage' else (224+93*index))
        elif op=='print-control':
            self.open_app('devices');self.click(205,276);index=[q['id'] for q in self.s['print_queue']].index(a['target'])
            self.p.mouse.move(800,400);self.p.mouse.wheel(0,-4000);self.pause()
            page_counts=[len(q['pages']) for q in self.s['print_queue']];heights=[122 if n<=5 else 138 for n in page_counts]
            centre=244+sum(h+10 for h in heights[:index])+(8 if page_counts[index]>=6 else 0)
            maximum=183+sum(h+10 for h in heights[:-1])+heights[-1]+25-630
            scroll=max(0,centre-400) if centre>570 else 0
            if scroll:self.p.mouse.wheel(0,scroll);self.pause(300)
            x=min(980,894+51*(page_counts[index]-4));self.capture('queue-before-control');self.click(x,centre-min(scroll,maximum))
        elif op=='export-log':
            self.open_app('events');logs=[f for f in self.files() if f.get('log_channel')];index=[f['id'] for f in logs].index(a['target']);self.click(202,234+41*index);self.click(402,206);self.pause();self.capture('export-dialog')
            folders=[f['id'] for f in self.files() if f['kind']=='folder'];self.native(640,254,folders.index(a['parent']));self.type_at(640,323,a['name']);self.type_at(640,392,a['start']);self.type_at(640,461,a['end']);self.capture('export-interval');self.click(858,534)
        elif op=='update-job':
            self.job(a['target']);self.click(1090,106)
            self.native(760,460,['manual','idle','plugged-in'].index(a['trigger']));self.capture('task-trigger');self.click(858,534)
        elif op=='create-job':self.create_job(a)
        elif op=='run-job':self.job(a['target']);self.click(1010,106)
        elif op=='setting':self.setting(a)
        elif op=='probe':
            self.open_app('terminal');self.click(500,161)
            command={'offline':'offline-test','workspace':'workspace-open','restoration':'restore-check','storage':'storage-audit'}[a['kind']]
            self.p.keyboard.insert_text(command+' "'+w.path(self.s,a['target'])+'"');self.p.keyboard.press('Enter');self.pause(500)
        else:raise RuntimeError('Unsupported coordinate operation '+op)
        w.mutate(self.s,a,self.ep['case']);self.step+=1;self.pause(180);self.capture('after-'+op)
        if op=='export-log':
            exported=next(f for f in self.files() if f['parent']==a['parent'] and f['name']==a['name']);self.document(exported['id'])
        if op=='run-job' and self.ep['case']['id'] in {'OS-H-04','OS-H-05','OS-H-09','OS-H-10'}:
            job=next(j for j in self.s['jobs'] if j['id']==a['target'])
            artifact=w.get_file(self.s,job['artifact']);processing=artifact['provenance']['processing']
            if job['kind']=='transcode':
                for f in self.files():
                    if f['parent']==processing['preview_folder']:self.document(f['id'])
            elif job['kind']=='redact':
                for fid in processing['redacted_files']:self.document(fid)
            elif job['kind'] in {'proof','deliver'}:
                self.document(artifact['id']);self.p.mouse.move(700,400);self.p.mouse.wheel(0,5000);self.pause(650);self.capture('artifact-result-fields')


def record(base,cid,c,seed,output,verify_each=True):
    key=f'{cid}-{c}-{seed}';directory=output/key;directory.mkdir(parents=True,exist_ok=True)
    ep=w.generate(cid,c,seed,'module-demo')
    session=request(base,'/api/v2/sessions',{'case_id':cid,'mode':'demo','convention':c,'seed':seed,'recording_actor':'oracle-assisted-coordinate-ui'})
    assert session['state_hash']==w.digest(ep['initial']),'Service source is stale; restart before recording'
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1,locale='en-US')
        actor=Author(page,ep,directory)
        try:
            page.goto(base+session['launch_url']);actor.pause(500);actor.capture('author-brief');page.keyboard.press('Tab');page.keyboard.press('Enter');actor.pause(300);actor.capture('desktop')
            example=next((f for f in actor.files() if f['name']=='Example input.json'),None)
            if example:actor.document(example['id'])
            if cid in {'OS-H-04','OS-H-05','OS-H-09'}:
                phase=next(a for a in ep['reference'] if a['op']=='create-job')
                source='source-1' if cid=='OS-H-05' else 'source-0'
                example=next(f for f in actor.files() if f['parent']==phase['input'] and f.get('source')==source)
                actor.document(example['id'])
            if cid=='OS-E-03':
                for f in ep['initial']['files']:
                    if f.get('approved') is not None:actor.inspect_properties(f['id'])
            for action in ep['reference']:
                actor.action(action)
                if verify_each:
                    actual=request(base,f'/api/v2/sessions/{session["id"]}')
                    if actual['state_hash']!=w.digest(actor.s):
                        differences=[]
                        for collection in ['files','jobs','devices','processes','print_queue','settings','receipts','log_exports']:
                            if actual['state'].get(collection)!=actor.s.get(collection):differences.append(collection)
                        raise RuntimeError(f'Coordinate input did not match intended {action}: differing {differences}')
            actor.capture('final-state');assert not actor.errors,actor.errors
            judged=request(base,f'/api/v2/sessions/{session["id"]}/judge',{})
            assert judged['result']['success'],judged['result']['failed_checks']
            actor.click(28,697);actor.click(413,625);actor.pause(500)
            finished=request(base,f'/api/v2/sessions/{session["id"]}')
            assert finished['status']=='finished' and finished['result']['success'],finished
            result={'key':key,'case_id':cid,'convention':c,'seed':seed,'session_id':session['id'],'actor':'oracle-assisted-coordinate-ui','inputs':'screenshots-and-coordinate-mouse-keyboard','scope':'local-method','result':finished['result'],'video_status':finished.get('video_status'),'screenshot_count':len(list(directory.glob('*.png')))}
            (directory/'result.json').write_text(json.dumps(result,indent=2));return result
        except Exception:
            actor.capture('ERROR');(directory/'error.txt').write_text(traceback.format_exc());raise
        finally:browser.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:8791');parser.add_argument('--output',type=Path,default=ROOT/'data/task36-recordings');parser.add_argument('--cases',nargs='+');parser.add_argument('--conventions',nargs='+',type=int,default=[0]);parser.add_argument('--seeds',nargs='+',type=int,default=[1001]);parser.add_argument('--workers',type=int,default=1);parser.add_argument('--force',action='store_true');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    wanted=[(cid,c,seed) for cid in args.cases or [x['id'] for x in tasks36.CASES] for c in args.conventions for seed in args.seeds]
    results=[];failures=[];jobs=[]
    for item in wanted:
        path=args.output/f'{item[0]}-{item[1]}-{item[2]}'/'result.json'
        if path.exists() and not args.force:
            previous=json.loads(path.read_text())
            try:
                saved=json.loads((ROOT/'data/episodes'/f'{previous["session_id"]}.json').read_text())
                if saved['episode']['implementation']['fingerprint']==w.IMPLEMENTATION['fingerprint'] and saved.get('video_status') in {'ready','queued','rendering'} and saved.get('result',{}).get('success'):
                    results.append(previous);continue
            except (OSError,ValueError,KeyError):pass
        jobs.append(item)
    print(json.dumps({'resume':len(results),'remaining':len(jobs)}),flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={pool.submit(record,args.base_url,*item,args.output):item for item in jobs}
        for future in as_completed(pending):
            item=pending[future]
            try:
                result=future.result();results.append(result);print(json.dumps({'done':item,'session':result['session_id']}),flush=True)
            except Exception as exc:failures.append({'case_id':item[0],'convention':item[1],'seed':item[2],'error':str(exc)});print(json.dumps({'failed':failures[-1]}),flush=True)
            (args.output/'results.json').write_text(json.dumps({'results':results,'failures':failures},indent=2))
    print(json.dumps({'completed':len(results),'failed':len(failures)}),flush=True)
    if failures:sys.exit(1)


if __name__=='__main__':main()

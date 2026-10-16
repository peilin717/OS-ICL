#!/usr/bin/env python3
"""Standard 108 demos: known-rule coordinate authoring with readable evidence."""
import argparse,copy,hashlib,json,math,sys,time,traceback
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'workflows.py').exists():ROOT=Path('/root/VideoICL-bench/OS-ICL')
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import workflows as w
import tasks36
from record36_coordinates import Author,request
from playwright.sync_api import sync_playwright
AUTHOR_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class ReadableAuthor(Author):
    def __init__(self,*args):
        super().__init__(*args);self.review=[]
    def observe(self,label,hold=3.0):
        self.p.mouse.move(1190,645);self.pause(100)
        name=f'review-{len(self.review):03}-{label}.png'
        self.p.screenshot(path=str(self.directory/name))
        self.review.append({'image':name,'label':label,'epoch_ms':int(time.time()*1000),'hold_seconds':hold,'action_step':self.step})
        self.pause(int(hold*1000))
    def capture(self,label):
        super().capture(label)
        if label in {'properties','export-interval','task-trigger','task-configuration','setting-saved'}:self.observe(label)
    def goto_line(self,line):
        self.type_at(439,98,str(line));self.click(478,98);self.pause(250)
    def document(self,identifier,read=True):
        super().document(identifier,read=False)
        self.p.mouse.move(740,420);self.p.mouse.wheel(0,-100000);self.pause(200)
        if not read:return
        f=self.get(identifier);text=f['content'];lines=text.splitlines();label='document-'+identifier
        self.observe(label+'-top')
        if f.get('generated_by') and len(text)>4000:
            anchors=[]
            for key in ['"paper"','"printer.paper"','"duplex"','"printer.order"','"print_profile"','"preview"','"trigger"']:
                found=[i+1 for i,line in enumerate(lines) if key in line]
                if found:anchors.extend([found[0],found[-1]])
            if not anchors:anchors=[max(1,len(lines)-12)]
            covered=[]
            for line in sorted(set(anchors)):
                if any(abs(line-old)<9 for old in covered):continue
                self.goto_line(line);self.observe(label+f'-line-{line}',4.0);covered.append(line)
        else:
            visual_rows=sum(max(1,math.ceil(len(line)/100)) for line in lines)
            pages=max(0,math.ceil((visual_rows-18)/13))
            for page in range(pages):
                self.p.mouse.move(740,420);self.p.mouse.wheel(0,286);self.pause(250)
                self.observe(label+f'-page-{page+2}')
    def scope_views(self,phase):
        cid=self.ep['case']['id']
        if phase=='before' and cid=='OS-E-01':
            workspace=next(f['id'] for f in self.files() if f['name']=='Workspace' and f['kind']=='folder')
            self.navigate(workspace);self.observe('before-original-filenames')
        elif phase=='before' and cid in {'OS-E-04','OS-M-07','OS-H-07'}:
            if cid=='OS-E-04':
                targets={a['target'] for a in self.ep['reference'] if a['op']=='rename'}
            else:targets={f['id'] for f in self.files() if f['name']=='source.txt'}
            for fid in sorted(targets):self.inspect_properties(fid)
        elif phase=='before' and cid=='OS-H-03':
            workspace=next(f['parent'] for f in self.files() if f['name']=='example-data.csv')
            self.navigate(workspace);self.observe('before-recovery-inputs')
        elif phase=='before' and cid=='OS-H-06':
            action=next(a for a in self.ep['reference'] if a['op']=='rename')
            self.navigate(self.get(action['target'])['parent']);self.observe('before-cache-resource-names')
        elif cid=='OS-E-05':
            self.open_app('monitor')
            for index,delta in enumerate([-100000,100000]):
                self.p.mouse.move(800,400);self.p.mouse.wheel(0,delta);self.pause(250);self.observe(f'{phase}-processes-{index}')
        elif cid=='OS-E-07':
            self.open_app('devices')
            for name,y in [('Camera',153),('Printer',194),('Network-storage',235)]:
                self.click(200,y);self.observe(f'{phase}-devices-{name}')
        elif cid=='OS-E-11':
            self.open_app('devices');self.click(205,276)
            for index,delta in enumerate([-100000,350,100000]):
                self.p.mouse.move(800,400);self.p.mouse.wheel(0,delta);self.pause(250);self.observe(f'{phase}-queue-{index}')
    def action(self,a):
        if a['op']=='write' and self.ep['case']['id']=='OS-E-12':
            self.document(a['target']);before=self.get(a['target'])['content'];at=a['content'].index('\f')
            assert a['content'].replace('\f','',1)==before
            self.goto_line(before[:at].count('\n')+1);self.observe('page-break-heading-boundary')
            self.click(320,98);self.observe('page-break-inserted');self.click(231,98)
            w.mutate(self.s,a,self.ep['case']);self.step+=1;self.document(a['target']);return
        if a['op']=='process':
            self.open_app('monitor');index=[p['id'] for p in self.s['processes']].index(a['target'])
            self.p.mouse.move(800,400);self.p.mouse.wheel(0,-100000);self.pause()
            if index<5:self.click(1062,194+89*index)
            else:
                self.p.mouse.wheel(0,100000);self.pause(250)
                maximum=max(0,89*len(self.s['processes'])-462)
                self.click(1062,194+89*index-maximum)
            w.mutate(self.s,a,self.ep['case']);self.step+=1;self.observe('process-state-saved');return
        super().action(a)
        if a['op']=='write':self.document(a['target'])
        elif a['op'] not in {'setting','run-job','export-log'}:self.observe('saved-'+a['op'])
        elif a['op']=='run-job':self.observe('job-result')


def record(base,cid,c,seed,folder):
    key=f'{cid}-{c}-{seed}';directory=folder/key;directory.mkdir(parents=True,exist_ok=True)
    ep=w.generate(cid,c,seed,'module-demo')
    session=request(base,'/api/v2/sessions',{'case_id':cid,'mode':'demo','convention':c,'seed':seed,'recording_actor':'oracle-assisted-coordinate-ui'})
    assert session['state_hash']==w.digest(ep['initial']),'Restart stale service'
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--hide-scrollbars'])
        page=browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1,locale='en-US');actor=ReadableAuthor(page,ep,directory)
        try:
            page.goto(base+session['launch_url']);actor.pause(400);page.keyboard.press('Tab');page.keyboard.press('Enter');actor.pause(300)
            actor.document('demo-context')
            sample=next((f for f in actor.files() if f['name']=='Example input.json'),None)
            if sample:actor.document(sample['id'])
            if cid in {'OS-E-02','OS-E-03','OS-M-01'}:
                for f in ep['initial']['files']:
                    if f.get('resource_key') and (cid!='OS-M-01' or f['revision']==3):actor.inspect_properties(f['id'])
            if cid in {'OS-H-04','OS-H-05','OS-H-09'}:
                stage=next(a for a in ep['reference'] if a['op']=='create-job');sources={'source-0','source-2'} if cid=='OS-H-04' else {'source-1'} if cid=='OS-H-05' else {'source-0','source-3'}
                for f in actor.files():
                    if f['parent']==stage['input'] and f.get('source') in sources:actor.document(f['id'])
            actor.scope_views('before')
            for a in ep['reference']:
                actor.action(a);actual=request(base,f'/api/v2/sessions/{session["id"]}')
                assert actual['state_hash']==w.digest(actor.s),f'Coordinate input mismatch: {a}'
            actor.scope_views('after');actor.observe('final-saved-result',4.0)
            assert not actor.errors,actor.errors
            judged=request(base,f'/api/v2/sessions/{session["id"]}/judge',{});assert judged['result']['success'],judged
            (directory/'review-frames.json').write_text(json.dumps(actor.review,indent=2))
            actor.click(28,697);actor.click(413,625);actor.pause(400)
            final=request(base,f'/api/v2/sessions/{session["id"]}');assert final['status']=='finished' and final['result']['success']
            result={'key':key,'case_id':cid,'convention':c,'seed':seed,'session_id':session['id'],'result':final['result'],'actor':'oracle-assisted-coordinate-ui','scope':'local-method','review_frame_count':len(actor.review),'authoring_sha256':AUTHOR_SHA256}
            (directory/'result.json').write_text(json.dumps(result,indent=2));return result
        except Exception:
            actor.capture('ERROR');(directory/'error.txt').write_text(traceback.format_exc());raise
        finally:browser.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8791');p.add_argument('--output',type=Path,default=ROOT/'data/task36-standard108-recordings');p.add_argument('--cases',nargs='+');p.add_argument('--conventions',nargs='+',type=int,default=[0,1,2]);p.add_argument('--seed',type=int,default=1001);p.add_argument('--workers',type=int,default=4);p.add_argument('--force',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    wanted=[(cid,c,a.seed) for cid in a.cases or [x['id'] for x in tasks36.CASES] for c in a.conventions];jobs=[];done=0;failed=[]
    for item in wanted:
        f=a.output/f'{item[0]}-{item[1]}-{item[2]}'/'result.json'
        if f.exists() and not a.force:
            r=json.loads(f.read_text());s=json.loads((ROOT/'data/episodes'/f'{r["session_id"]}.json').read_text())
            if r.get('authoring_sha256')==AUTHOR_SHA256 and s['episode']['implementation']['fingerprint']==w.IMPLEMENTATION['fingerprint'] and s.get('video_status') in {'ready','queued','rendering'}:done+=1;continue
        jobs.append(item)
    print(json.dumps({'resume':done,'remaining':len(jobs)}),flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        pending={pool.submit(record,a.base_url,*item,a.output):item for item in jobs}
        for future in as_completed(pending):
            item=pending[future]
            try:future.result();done+=1;print(json.dumps({'done':item}),flush=True)
            except Exception as exc:failed.append({'key':item,'error':str(exc)});print(json.dumps({'failed':failed[-1]}),flush=True)
    print(json.dumps({'completed':done,'failures':failed}),flush=True)
    if failed:sys.exit(1)
if __name__=='__main__':main()

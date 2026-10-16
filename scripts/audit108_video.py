#!/usr/bin/env python3
"""Decode complete videos and locate every authored reading witness in frames."""
import argparse,json,sys,hashlib,math
from pathlib import Path
import cv2,numpy as np
ROOT=Path('/root/VideoICL-bench/OS-ICL')


def thumb(frame):
    # The application window; exclude the desktop clock and taskbar.
    gray=cv2.resize(cv2.cvtColor(frame[76:627,135:1135],cv2.COLOR_BGR2GRAY),(300,165),interpolation=cv2.INTER_AREA).astype(np.float32)
    # Remove flat-background codec shifts while retaining glyphs and panel structure.
    return gray-cv2.GaussianBlur(gray,(0,0),3)


def audit(directory):
    result=json.loads((directory/'result.json').read_text());sid=result['session_id'];session=json.loads((ROOT/'data/episodes'/f'{sid}.json').read_text())
    if session.get('video_status')!='ready':return {'key':result['key'],'status':session.get('video_status')}
    video=ROOT/'data/videos'/session['video'];cap=cv2.VideoCapture(str(video));fps=cap.get(cv2.CAP_PROP_FPS);expected=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));step=max(1,round(fps/2));images=[];times=[];n=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        if n%step==0:images.append(thumb(frame));times.append(n/fps)
        n+=1
    cap.release();assert n==expected or abs(n-expected)<=1,(n,expected)
    frames=np.stack(images);times=np.array(times);markers=json.loads((directory/'review-frames.json').read_text());rows=[]
    for marker in markers:
        ref=thumb(cv2.imread(str(directory/marker['image'])));distance=np.mean(np.abs(frames-ref),axis=(1,2));best=int(distance.argmin());minimum=float(distance[best])
        # Codec noise is allowed; match the nearest nearly-identical rendered view.
        threshold=max(.60,minimum+.15);matching=np.flatnonzero(distance<=threshold);runs=[];run=[]
        for i in matching:
            if run and i!=run[-1]+1:runs.append(run);run=[]
            run.append(int(i))
        if run:runs.append(run)
        longest=max(runs,key=len);span=float(times[longest[-1]]-times[longest[0]]+step/fps)
        passed=minimum<=1.1 and span>=1.5
        rows.append({**marker,'best_video_second':round(float(times[best]),3),'structural_mae':round(minimum,4),'continuous_match_seconds':round(span,3),'passed':passed})
    report={'audit_version':3,'key':result['key'],'case_id':result['case_id'],'condition':chr(65+result['convention']),'seed':result['seed'],'session_id':sid,'status':'audited','seconds':n/fps,'decoded_frames':n,'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'judge_success':session['result']['success'],'replay_verified':session['video_provenance']['replay_verified'],'reading_witnesses':len(rows),'witnesses_passed':sum(r['passed'] for r in rows),'passed':all(r['passed'] for r in rows),'witnesses':rows}
    (directory/'video-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='witnesses'}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directories',nargs='+',type=Path);a=p.parse_args()
    for directory in a.directories:audit(directory)

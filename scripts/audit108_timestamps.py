#!/usr/bin/env python3
"""Check packet timestamps in all 108 final files, including compilation seams."""
import argparse,concurrent.futures,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def audit(root):
    manifest=json.loads((root/'candidate-manifest.json').read_text())
    def check(row):
        path=root/'package'/row['video']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=pts_time','-of','json',str(path)]))
        times=[float(x['pts_time']) for x in probe['packets']];gaps=[b-a for a,b in zip(times,times[1:])]
        assert gaps and all(.038<=x<=.042 for x in gaps) and 0<=times[0]<.05
        clip=row['case_id']+'-'+row['condition'];report=json.loads((root/'audit'/f'{clip}.json').read_text())
        assert report['decoded_frames']==len(times)
        return {'clip':clip,'sha256':row['sha256'],'packets':len(times),'first_pts':times[0],'last_pts':times[-1],'minimum_frame_gap':round(min(gaps),6),'maximum_frame_gap':round(max(gaps),6),'passed':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(check,manifest['videos']))
    assert len(results)==108
    report={'clips':108,'all_passed':True,'videos':results};(root/'media-timestamps.json').write_text(json.dumps(report,indent=2));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT/'data/task36-revision108');args=parser.parse_args()
    print('Verified packet timelines:',audit(args.root)['clips'])

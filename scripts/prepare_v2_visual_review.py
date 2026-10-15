#!/usr/bin/env python3
"""Create timestamped storyboards and a local human/video review index.

Generating frames is not a visual pass. Reviews remain pending until someone
actually inspects the video and records a disposition with a scope statement.
"""
import argparse
import html
import json
import hashlib
import subprocess
from pathlib import Path


def prepare(root, interval=4):
    root=root.resolve()
    output=root/'visual-review'
    output.mkdir(parents=True,exist_ok=True)
    prior={}
    if (output/'index.json').is_file():
        prior={e['identity']:e for e in json.loads((output/'index.json').read_text()).get('entries',[])}
    entries=[]
    indexes=sorted(root.glob('context-*/results.json'))
    if (root/'results.json').is_file():indexes.insert(0,root/'results.json')
    for index in indexes:
        for row in json.loads(index.read_text()):
            video=Path(row.get('video_path','')).resolve()
            if root not in video.parents or not video.is_file():
                continue
            if hashlib.sha256(video.read_bytes()).hexdigest()!=row['video_sha256']:
                raise ValueError('Video bytes differ from the review provenance: '+str(video))
            identity=f"{row['case_id']}-c{row['convention']}-s{row['seed']}"
            folder=output/identity
            folder.mkdir(exist_ok=True)
            stamp=folder/'generated.json'
            provenance={'video_sha256':row['video_sha256'],'interval_seconds':interval,
                        'frame_scale':[960,540],'tiles':[2,4],'timestamp_source':'source_pts_before_sampling'}
            if not stamp.is_file() or json.loads(stamp.read_text())!=provenance:
                # Every page spans 8 samples; multiple pages cover the full
                # duration. Timestamp overlays make gaps explicit.
                # Stamp source PTS before fps changes timestamps. Otherwise a
                # frame selected near t=6 can be falsely labeled t=4, making
                # native-frame follow-up checks target the wrong instant.
                filter_spec=f"drawtext=text='%{{pts\\:hms}}':x=16:y=16:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.7,fps=1/{interval},scale=960:540,tile=2x4"
                subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',filter_spec,
                                '-vsync','vfr',str(folder/'sheet-%03d.jpg')],check=True,timeout=180)
                stamp.write_text(json.dumps(provenance,indent=2))
            sheets=[str(path.relative_to(root)) for path in sorted(folder.glob('sheet-*.jpg'))]
            previous=prior.get(identity,{})
            same_video=previous.get('sha256')==row['video_sha256']
            entries.append({'identity':identity,'case_id':row['case_id'],'convention':row['convention'],
                            'seed':row['seed'],'video':str(video.relative_to(root)),
                            'sha256':row['video_sha256'],'duration_seconds':float(row['video_probe']['format']['duration']),
                            'storyboards':sheets,'status':previous.get('status','pending') if same_video else 'pending',
                            'review_scope':previous.get('review_scope') if same_video else None})
    (output/'index.json').write_text(json.dumps({'sampling_interval_seconds':interval,'entries':entries},indent=2))
    cards=[]
    for entry in entries:
        video='../'+entry['video']
        images=''.join(f'<a href="../{html.escape(sheet)}" target="_blank"><img src="../{html.escape(sheet)}" loading="lazy" alt="Timestamped storyboard"></a>' for sheet in entry['storyboards'])
        cards.append(f'<section><h2>{html.escape(entry["identity"])}</h2><p>{entry["duration_seconds"]:.2f} seconds · {html.escape(entry["status"])}</p><video controls preload="none" src="{html.escape(video)}"></video><details><summary>Whole-timeline sampled storyboards</summary>{images}</details></section>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>OS-ICL video review</title><style>body{font:14px Arial;color:#263840;background:#eef2f3;max-width:1200px;margin:30px auto}section{padding:20px;margin:20px 0;background:white;border:1px solid #ccd8de}video{width:100%;max-width:960px}img{width:100%;height:auto;margin-top:12px}h2{font-size:18px}</style><h1>OS-ICL video review</h1><p>Storyboards sample the complete timeline. They do not prove a visual pass or replace inspection of brief transitions. Verify original/edited data, controls, settings, recovery, output inspection, legibility, geometry and absence of private recorder instructions.</p>'''+''.join(cards)+'</html>'
    (output/'index.html').write_text(page)
    print(f'Prepared {len(entries)} videos for review; all visual dispositions remain pending. {output / "index.html"}',flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--interval',type=float,default=4)
    args=parser.parse_args()
    if args.interval<=0:
        parser.error('Sampling interval must be positive.')
    prepare(args.root,args.interval)


if __name__=='__main__':
    main()

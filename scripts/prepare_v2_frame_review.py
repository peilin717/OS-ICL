#!/usr/bin/env python3
"""Prepare every decoded frame, deduplicating only identical RGB hashes.

Native PNGs are checked against the decoded video frame hashes. The complete
timestamp/frame mapping remains available. Preparation never approves visuals.
"""
import argparse
from fractions import Fraction
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import artifact_provenance


def parse_hashes(raw,width,height):
    frames=[]
    timebase=None
    for line in raw.splitlines():
        match=re.match(r'#tb 0:\s*(\d+/\d+)',line)
        if match:timebase=Fraction(match.group(1))
        if not line.strip() or line.startswith('#'):continue
        fields=[field.strip() for field in line.split(',')]
        if len(fields)!=6 or fields[0]!='0' or timebase is None:
            raise ValueError('Unexpected frame hash record')
        pts=int(fields[2]);size=int(fields[4]);digest=fields[5]
        if size!=width*height*3 or not re.fullmatch(r'[0-9a-f]{64}',digest):
            raise ValueError('Frame is not complete RGB24 with SHA-256')
        seconds=float(pts*timebase)
        if frames and seconds<=frames[-1]['seconds']:
            raise ValueError('Non-monotonic frame timestamps')
        frames.append({'index':len(frames),'seconds':seconds,'sha256':digest})
    if not frames:raise ValueError('No decoded frames')
    return frames


def hashes(path,width,height):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-an',
                                 '-vsync','0','-pix_fmt','rgb24','-c:v','rawvideo',
                                 '-f','framehash','-hash','sha256','-'],text=True,timeout=240)
    return parse_hashes(raw,width,height)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--case',required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rows=[row for row in json.loads(args.results.read_text()) if row['case_id']==args.case and row['seed']==args.seed]
    if len(rows)!=1:parser.error('Choose exactly one completed result row')
    row=rows[0]
    implementation=artifact_provenance.capture()
    if row['implementation_fingerprint']!=implementation['fingerprint']:
        parser.error('Cannot prepare current review from another recording implementation')
    video=Path(row['video_path'])
    video_sha=hashlib.sha256(video.read_bytes()).hexdigest()
    if video_sha!=row['video_sha256']:parser.error('Recorded video checksum mismatch')
    if args.output.exists():parser.error('Refusing to overwrite existing frame review directory')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-count_frames','-show_entries','stream=width,height,nb_read_frames','-of','json',str(video)]))
    stream=probe['streams'][0];width=stream['width'];height=stream['height']
    frames=hashes(video,width,height)
    if len(frames)!=int(stream['nb_read_frames']):raise ValueError('Decoded frame count mismatch')
    unique=[];identities={}
    for frame in frames:
        digest=frame['sha256']
        if digest not in identities:
            identities[digest]=len(unique)+1
            unique.append(frame)
        frame['native_png']=f"frame-{identities[digest]:06d}.png"
    args.output.mkdir(parents=True)
    selection='+'.join(f"eq(n\\,{frame['index']})" for frame in unique)
    subprocess.run(['ffmpeg','-v','error','-i',str(video),'-map','0:v:0','-an',
                    '-vf','select='+selection,'-vsync','0','-pix_fmt','rgb24',
                    str(args.output/'frame-%06d.png')],check=True,timeout=300)
    extracted=hashes(args.output/'frame-%06d.png',width,height)
    if [frame['sha256'] for frame in extracted]!=[frame['sha256'] for frame in unique]:
        raise ValueError('Extracted native PNGs differ from decoded source RGB frames')
    if hashlib.sha256(video.read_bytes()).hexdigest()!=video_sha:
        raise ValueError('Video changed during preparation')
    artifact_provenance.assert_unchanged(implementation)
    manifest={'schema_version':1,'case_id':row['case_id'],'convention':row['convention'],'seed':row['seed'],
              'video_sha256':video_sha,'implementation_fingerprint':implementation['fingerprint'],
              'decoded_frames':len(frames),'unique_native_frames':len(unique),'width':width,'height':height,
              'temporal_sampling':False,'pixel_format':'RGB24','hash_algorithm':'SHA-256',
              'native_png_hashes_verified':True,'visual_review':'pending','frames':frames,
              'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output/'frames.json').write_text(json.dumps(manifest,indent=2))
    cards=''.join(f'<section><h2>First occurrence: frame {frame["index"]} · {frame["seconds"]:.3f}s</h2>'
                  f'<a href="{html.escape(frame["native_png"])}"><img loading="lazy" src="{html.escape(frame["native_png"])}"></a></section>' for frame in unique)
    (args.output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>OS-ICL native frame review</title>'
        '<style>body{font:14px Arial;max-width:1280px;margin:24px auto}img{width:100%;height:auto}section{margin:24px 0}</style>'
        '<h1>Complete decoded-frame review material — pending</h1><p>Every encoded video frame was decoded and mapped in frames.json. '
        'Only SHA-256-identical RGB frames share a native image. Review every unique image and the full temporal mapping; '
        'this preparation is not visual approval. Short transitions are not dropped by temporal sampling.</p>'+cards+'</html>')
    print(json.dumps({key:manifest[key] for key in ['decoded_frames','unique_native_frames','native_png_hashes_verified','visual_review']}),flush=True)


if __name__=='__main__':main()

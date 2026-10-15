#!/usr/bin/env python3
"""Copy a validated video matrix into a public, source-independent dataset folder."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def package(source, destination):
    source = source.resolve()
    manifest = json.loads((source / 'manifest.json').read_text())
    if manifest.get('structural_audit') != 'passed' or len(manifest['entries']) != 108:
        raise ValueError('A complete structurally validated 108-video manifest is required.')
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    for entry in manifest['entries']:
        relative = Path(entry['video'])
        video = (source / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or source not in video.parents:
            raise ValueError('Video path escapes the release root.')
        key = (entry['case_id'], entry['convention'], entry['seed'])
        if key in seen:
            raise ValueError('Duplicate video identity.')
        seen.add(key)
        digest = hashlib.sha256(video.read_bytes()).hexdigest()
        if digest != entry['sha256']:
            raise ValueError('Source checksum mismatch: ' + str(relative))
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError('Refusing to replace different existing video: ' + str(target))
        else:
            shutil.copyfile(video, target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('Copied video checksum mismatch.')
        rows.append({name: entry[name] for name in (
            'case_id', 'convention', 'seed', 'video', 'sha256', 'duration_seconds',
            'width', 'height', 'recording_actor', 'replay_verified')})
        rows[-1]['bytes'] = target.stat().st_size
    expected = {(f'OS-LH-{n:02d}', c, s) for n in range(1, 13)
                for c in range(3) for s in (1001, 1002, 1003)}
    if seen != expected:
        raise ValueError('Incorrect case/context/seed matrix.')
    public = {'benchmark_version': manifest['benchmark_version'],
              'implementation_fingerprint': manifest['implementation']['fingerprint'],
              'video_count': len(rows), 'structural_audit': 'passed',
              'visual_review': 'pending',
              'recording_source': 'oracle-assisted browser interaction replay, not human or VLM',
              'metadata_audience': 'researcher/trusted runner; never mount the complete index for an agent',
              'entries': rows}
    (destination / 'manifest.json').write_text(json.dumps(public, indent=2) + '\n')
    (destination / 'SHA256SUMS').write_text(''.join(
        f"{row['sha256']}  {row['video']}\n" for row in rows))
    lines = ['# Video index', '',
             'Researcher index: context labels are private to the evaluation runner.', '',
             '| Task | Context | Seed | Duration | Video |',
             '|---|---:|---:|---:|---|']
    for row in rows:
        lines.append(f"| {row['case_id']} | {row['convention']} | {row['seed']} | "
                     f"{row['duration_seconds']:.2f}s | [WebM]({row['video']}) |")
    (destination / 'INDEX.md').write_text('\n'.join(lines) + '\n')
    print(f"Packaged and checksum-verified {len(rows)} videos; {sum(r['bytes'] for r in rows)} bytes.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    package(args.source, args.destination)

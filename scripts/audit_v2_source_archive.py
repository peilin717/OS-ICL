#!/usr/bin/env python3
"""Check and execute a development source snapshot, never approve a release.

This executes the archive's test code; use only trusted local source snapshots.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import artifact_provenance

ROOT_FILES = set(artifact_provenance.SOURCES) | {
    'cases.py', '.gitignore', 'CITATION.cff', 'CONTRIBUTING.md',
    'environment.yml', 'INTEGRATION.md', 'LICENSE', 'README.md',
    'SECURITY.md', 'run.sh', 'test.sh',
}
PUBLIC_MANIFEST = 'data/manifests/os-icl-1.0.0.json'
SOURCE_DIRS = {'static', 'scripts', 'tests', 'docs', '.github'}
SUFFIXES = {'.py', '.js', '.css', '.html', '.md', '.yml', '.yaml'}


def validate_members(members):
    seen = set()
    for member in members:
        name = member.name.rstrip('/')
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or
                '\\' in name or ':' in name or path.as_posix() != name):
            raise ValueError('Unsafe archive path: ' + member.name)
        if name in seen or not (member.isdir() or member.isfile()):
            raise ValueError('Duplicate, linked or special archive entry: ' + name)
        seen.add(name)
        if any(p in {'__pycache__', '.pytest_cache', '.git'} for p in path.parts):
            raise ValueError('Runtime/cache/git data in source archive: ' + name)
        allowed = name in ROOT_FILES or name == PUBLIC_MANIFEST
        if member.isdir():
            allowed |= path.parts[0] in SOURCE_DIRS or name in {'data', 'data/manifests'}
        elif path.parts[0] in SOURCE_DIRS:
            allowed |= path.suffix in SUFFIXES
        if not allowed:
            raise ValueError('Unexpected source snapshot entry: ' + name)
    required = ROOT_FILES | {PUBLIC_MANIFEST}
    files = {m.name for m in members if m.isfile()}
    if required - files:
        raise ValueError('Source snapshot lacks required files: ' + str(sorted(required-files)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    implementation = artifact_provenance.capture()
    archive_sha = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    logs = {}
    with tempfile.TemporaryDirectory(prefix='os-icl-source-archive-') as owned_temp:
        task_root = Path(owned_temp)
        checkout = task_root / 'extracted source with spaces'
        checkout.mkdir()
        with tarfile.open(args.archive, 'r:gz') as archive:
            members = archive.getmembers()
            validate_members(members)
            # No links/special files or escaping paths survive the checks;
            # extraction is restricted to this new, task-owned empty directory.
            archive.extractall(checkout, members=members)
        source_hashes = {name: hashlib.sha256((checkout/name).read_bytes()).hexdigest()
                         for name in artifact_provenance.SOURCES}
        if artifact_provenance.digest(source_hashes) != implementation['fingerprint']:
            raise ValueError('Archive runtime does not match the current recording source.')
        env = dict(os.environ, OS_ICL_PYTHON=sys.executable, PYTHONNOUSERSITE='1')
        env.pop('PYTHONPATH', None)
        commands = {
            'full_tests': [str(checkout/'test.sh')],
            'portable_startup': [sys.executable, str(checkout/'scripts/audit_v2_portable_checkout.py'),
                                 '--output', str(task_root/'portable.json')],
        }
        for name, command in commands.items():
            result = subprocess.run(command, cwd=task_root, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
            logs[name] = result.stdout
            if result.returncode:
                raise RuntimeError(name + ' failed:\n' + result.stdout[-6000:])
            print(name + ' passed from extracted archive.', flush=True)
    artifact_provenance.assert_unchanged(implementation)
    report = {'status': 'passed', 'scope': 'development source snapshot only; not benchmark release approval',
              'archive_sha256': archive_sha, 'implementation_fingerprint': implementation['fingerprint'],
              'model_evaluation': False, 'independent_machine': False,
              'source_only': True, 'logs': logs,
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print('Source snapshot audit passed: ' + str(args.output), flush=True)


if __name__ == '__main__':
    main()

# OS-ICL demonstration videos v1.0.0

This directory contains the canonical demonstration set for OS-ICL Bench
1.0.0: 108 independently recorded WebM videos covering all 36 cases under each
of the three temporary hidden rules.

## Contents

- 36 benchmark cases × 3 hidden rules = 108 videos.
- Resolution: 1280×720.
- Codec/container: VP8 WebM.
- Each video is a clean server-side replay of a successful computer-use
  trajectory.
- Recorder instructions, rule identifiers, rule text, expected actions, and
  Studio controls are not rendered into the videos.

The filenames are immutable episode IDs such as
`vos_32cff46ae751d971.webm`. Use the public release manifest at
[`../../data/manifests/os-icl-1.0.0.json`](../../data/manifests/os-icl-1.0.0.json)
to map every filename to its case ID, rule context, seed, duration, byte size,
and SHA-256 checksum. The manifest intentionally contains no rule text or
expected-action oracle.

## Validate the release

From the repository root, install `ffprobe` and run:

```bash
python scripts/validate_release.py \
  --manifest data/manifests/os-icl-1.0.0.json
```

A valid checkout prints:

```text
valid OS-ICL 1.0.0 release: entries=108 videos_checked=108
```

The validator checks coverage, unique case-rule contexts, SHA-256 checksums,
video dimensions, and positive duration.

## Recommended evaluation use

For each query, provide only the demonstration selected for the same case and
hidden rule, followed by the visually novel query episode. The tested agent may
receive video frames or the WebM file plus screenshot and mouse/keyboard access
to the simulator. Do not provide the agent with DOM access, accessibility trees,
semantic action APIs, saved episode JSON, rule identifiers, or authoring briefs.

These videos demonstrate policies in the browser-based Vibe OS simulator. They
do not contain recordings of a real Windows, macOS, or Linux desktop.

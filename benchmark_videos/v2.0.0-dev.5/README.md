# OS-ICL v2 development demonstrations

108 WebM demonstrations: 12 long-horizon tasks × 3 operating conventions ×
3 seeds (1001, 1002, 1003). Total video size is 1,050,740,339 bytes (about 1.05 GB).
Every video is 1280 × 720. This is a development dataset, not a final benchmark
release: structural validation and complete decoding passed; full visual review
and the complete external-runner export audit remain pending.

## Browse and download

- [Complete video index](INDEX.md): one link per task/context/seed.
- [Machine-readable manifest](manifest.json): relative paths, durations, sizes,
  recording provenance and SHA-256 hashes.
- [SHA256SUMS](SHA256SUMS): run `sha256sum -c SHA256SUMS` from this directory.

Folder layout: `context-{0,1,2}/seed-{1001,1002,1003}/OS-LH-{01..12}-{context}.webm`.
Contexts 0/1/2 are Interactive preparation, Reversible preparation and Audited
delivery. They are operating conventions, not difficulty levels. For each
task/context, all three seeds form a demonstration set; use different seeds for
query episodes. The 108 videos are not 108 independent task templates.

GitHub may offer large videos as downloads rather than inline previews. Download
the WebM and open it in a browser or video player. These files use ordinary Git,
not Git LFS. Existing v1 videos in the sibling folder are historical and must
not be substituted for these v2 demonstrations.

## Task list

| ID | Workflow |
|---|---|
| OS-LH-01 | Research handoff |
| OS-LH-02 | Release preparation |
| OS-LH-03 | Backup and recovery |
| OS-LH-04 | Media ingest |
| OS-LH-05 | Print production |
| OS-LH-06 | Offline field kit |
| OS-LH-07 | Workspace migration |
| OS-LH-08 | Failed build recovery |
| OS-LH-09 | Evidence archive |
| OS-LH-10 | Scheduled distribution |
| OS-LH-11 | Storage maintenance |
| OS-LH-12 | Project restoration |

## Provenance and evaluation boundary

These are **oracle-assisted automated browser demonstrations**, not human or
VLM-agent recordings. Actual browser interaction traces are replayed through the
same handlers, with normalized reading dwell; replayed final-state equality is
checked. Duration includes navigation and presentation time and is not a measure
of model difficulty. Media, builds, printers and other desktop services operate
on simulated resources, not the host OS.

This folder is intended for researchers and trusted runners. Do not expose the
full index, manifest, context-labeled paths, source code, private authoring brief
or session traces to the evaluated agent. Select only the appropriate demo set
and serve videos through opaque URLs. The agent receives the videos, query goal
and desktop pixels/actions, and must infer the operating convention.

No private episode JSON, semantic action trace or answer/scoring configuration
is included here. No model evaluation or empirical ICL-gain claim is implied.
See the [benchmark card](../../docs/V2_BENCHMARK_CARD.md) and
[evaluation protocol](../../docs/V2_EVALUATION_PROTOCOL.md).

# OS-ICL Bench

OS-ICL evaluates learning operating rules from video demonstrations and applying them through an English desktop simulator. It contains **36 task families: 12 Easy, 12 Medium and 12 Hard**, with nine functional applications and state-based judges.

| Difficulty | Inference task |
|---|---|
| Easy | Repeatedly apply the demonstrated rule to new objects. |
| Medium | Apply the demonstrated rule as one module of a long workflow. |
| Hard | Complete a long workflow with necessary content or state dependencies across multiple OS interfaces. |

Difficulty describes task execution. Demonstrations show a local, transferable method.

## Run

Use Linux or WSL with Python 3.10 or later:

```bash
./run.sh
```

Open `http://localhost:8790` for the desktop or `http://localhost:8790/studio36` to create task sessions. See the [task catalogue](docs/TASK_CATALOGUE_36.md), [structured specification](docs/TASK_CATALOGUE_36.json) and [API guide](docs/TASK36_API.md).

## Demonstrations

[Download the standard 108-video library](https://github.com/peilin717/OS-ICL/releases/tag/task36-standard108-2026-10-16).

The library contains **36 tasks × three alternative rule conditions (A/B/C) × one video**. Each inference receives **one video matching its rule condition**. Demonstration seed 1001 identifies the example fixture; query examples use a different seed.

- `task36-standard108.tar.gz`: complete video library, HTML player and review sheets. Extract into native WSL storage and open `task36-standard108/index.html`.
- Individual WebM assets: one downloadable file per task/condition, with opaque filenames.
- `standard108-manifest.json`: trusted clip selection, URLs, checksums and provenance.
- `demo108-audit.json` and `standard108-recording-evidence.tar.gz`: validation evidence for reviewers.
- `standard108-source.tar.gz`: source snapshot. `SHA256SUMS` provides asset checksums.

Recordings use coordinate mouse/keyboard interaction and verified browser replay at 1280×720. The recording author knows the rules. The videos are demonstrations for inference input; their success is separate from model evaluation.

## Evaluation and judging

Create an evaluation session through `POST /api/v2/sessions`, then export its model input:

```bash
python scripts/export_v2_episode.py \
  --session osl_ID \
  --manifest docs/STANDARD108_MANIFEST.json \
  --output /path/to/export
```

Give the model `agent-launch.json`, its selected video and query screenshots. The model controls the desktop with mouse and keyboard. Keep `trusted-runner.json`, rule labels, reference plans, episode state and audit evidence on the trusted controller side.

`POST /api/v2/sessions/{id}/judge` scores the persisted session without ending it. Success requires task results, rule compliance and protected-state preservation. The judge rejects caller-supplied states and expected answers. See the [evaluation protocol](docs/V2_EVALUATION_PROTOCOL.md) for controls and reporting.

## Validation

All 108 demonstrations pass their state judges, replay consistency checks and complete video decoding. All 856 authored reading views pass timeline coverage checks. Assistant visual review covers shared inputs and A/B/C checkpoints for all 36 tasks; it is not continuous human viewing. See the [audit evidence](docs/DEMO108_AUDIT.json).

The test suite contains 323 passing tests. Run it with:

```bash
python -m pytest -q tests
```

Engine tests require pytest. Browser recording and video inspection additionally require Playwright, Chromium/Chrome, FFmpeg, OpenCV, NumPy and Pillow. Full-query browser acceptance and independent model evaluation are separate validation activities.

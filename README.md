# OS-ICL Bench — 36 tasks

The active catalogue contains exactly **12 Easy, 12 Medium and 12 Hard** task families. It uses the existing English desktop and nine applications; Hard requires necessary interactions across those existing interfaces.

Run `./run.sh`, then open `http://localhost:8790/studio36` (also `/studio`). `/` opens the same desktop. `GET /api/v2/cases` lists only the current 36 tasks. The old v1 task API returns HTTP 410; old long-horizon task IDs are rejected. Internal resource templates remain private implementation helpers for the current tasks and engine regression tests.

## Tasks and judging

- [36-task catalogue](docs/TASK_CATALOGUE_36.md) and [JSON](docs/TASK_CATALOGUE_36.json)
- [Difficulty standard](docs/DIFFICULTY_STANDARD.md) and [design audit](docs/TASK_DESIGN_AUDIT_36.md)
- [Session and judge API](docs/TASK36_API.md)
- `tasks36.py`: query fixtures and separate local-method demonstration fixtures
- `judge36.py`: persisted-state predicates and source/side-effect protection

`POST /api/v2/sessions/{id}/judge` reads server-owned state without finishing the session. It rejects caller-supplied state or expected answers. Medium/Hard demos show a transferable local method; demo success does not imply full-query completion.

## Videos (remote storage)

[Download standard 108 demos](https://github.com/peilin717/OS-ICL/releases/tag/task36-standard108-2026-10-16).

The standard library contains **108 clips: 36 tasks × A/B/C rule conditions × one video**. Each query receives **one matching video**. Seed 1001 identifies the example fixture; it does not mean three input videos. Query examples must use a different seed. All 108 videos are individually downloadable with opaque filenames; `task36-standard108.tar.gz` also includes the complete library, local HTML player and review sheets.

The [trusted manifest](docs/STANDARD108_MANIFEST.json) selects matching clips. Keep its task/condition labels, the audit evidence and trusted runner state outside agent inputs. Export a query with `python scripts/export_v2_episode.py --session osl_ID --manifest docs/STANDARD108_MANIFEST.json --output /path/to/export`; only `agent-launch.json` goes to the model.

[Audit findings and evidence](docs/DEMO108_AUDIT.json): 108 state judges and replay hashes passed, every video was fully decoded, and all 856 authored reading views passed timeline coverage checks. Assistant review covers the shared input and A/B/C checkpoints for all 36 tasks, not continuous human viewing. Fixes include readable pauses/paging, visible event anchors, protected scope controls, timestamp ties, category ordering, restore layout and actual page-break controls. All 108 query definitions and existing desktop app operations remain unchanged.

Recordings are **oracle-assisted coordinate mouse/keyboard demonstrations**. They are not human recordings or independent model results. Full-query browser acceptance and independent model evaluation remain separate work.

The [earlier 324-clip release](https://github.com/peilin717/OS-ICL/releases/tag/task36-2026-10-16) and raw preservation assets are historical archives, superseded for inference input by standard 108. Published video binaries are remote-only after checksum verification. Download/extract the standard bundle into native WSL storage and open `task36-standard108/index.html`; videos are not stored on C:.

## Tests

Install `pytest`, then run `python -m pytest -q tests`. Browser recording additionally requires Playwright and Chromium/Chrome. Existing engine operations, application UI, privacy boundaries, fixtures and judge regression tests are retained.

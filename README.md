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

[Download the 36-task release](https://github.com/peilin717/OS-ICL/releases/tag/task36-2026-10-16).

`task36-demos-324.tar.gz` contains **324 clips** (36 × A/B/C × seeds 1001/1002/1003), a local HTML index, a manifest and media validation. Every clip passed its state-based judge, replay final-state verification, and full-file decoding. The archived recording source fingerprint is `233380a5f8464a089c3d993655a0ad89565ee451f03dd79bdd3171b4dd8417e8`. The exact recording source is a separate release asset; retiring old task entry points changes the current source fingerprint without changing desktop/app operations.

Recordings are **oracle-assisted coordinate mouse/keyboard local-method demonstrations**, not human recordings or independent model results. Whole-timeline visual approval and full-query browser acceptance remain separate work. The raw preservation archive contains historical/pilot videos as well as current videos; it must not be confused with the 324 accepted current clips.

Published video binaries are remote-only after checksum verification. To view locally, download and extract the formal archive to native WSL storage, then open `demo36/index.html`. Videos are not packaged onto C:.

## Tests

Install `pytest`, then run `python -m pytest -q tests`. Browser recording additionally requires Playwright and Chromium/Chrome. Existing engine operations, application UI, privacy boundaries, fixtures and judge regression tests are retained.

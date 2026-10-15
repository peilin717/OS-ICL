# OS-ICL Bench

The current desktop is the **2.0 development reconstruction**: an English-only,
pale Windows-style workspace with nine applications sharing a deterministic
resource graph. `/` opens the desktop. `/studio` creates sessions for the new
12 long-horizon workflows. The v1 catalogue and videos are historical data.

This is not yet a paper-ready v2 release. The binding release criteria and
remaining verification are in [the reconstruction contract](docs/V2_ACCEPTANCE.md).

### Development snapshot: 2.0.0-dev.5

This checkout contains the twelve new workflows, desktop, recording/export
interfaces, regression tests and audit tools. All 108 demonstration recordings
have been generated locally (12 tasks × 3 conventions × 3 seeds), but complete
visual approval and the full external-export audit remain pending. The new
videos, private session traces and local audit outputs are excluded from Git;
the videos already under `benchmark_videos/v1.0.0/` belong to the historical v1
benchmark and must not be substituted for v2 demonstrations.

## Current v2 workflow

Activate the environment from `environment.yml`, start with `./run.sh`, then
open `http://127.0.0.1:8790/`. The launch scripts use `python3` from the active
environment. Set `OS_ICL_PYTHON` to an explicit interpreter if needed; an
explicit `CONDA_BIN` still supports older deployments (`OS_ICL_CONDA_ENV`
defaults to `data_mining`). No personal Conda installation path is hardcoded.
New deployments can configure `OS_ICL_HOST`, `OS_ICL_PORT`, `OS_ICL_PUBLIC_URL`
and `OS_ICL_RENDER_CONCURRENCY`. Historical `VIBE_*` names remain compatibility
aliases; the `OS_ICL_*` value wins when both are set.
File Explorer, Notepad, Settings, Task Scheduler, Transfer Manager, Task Manager,
Device Manager, Event Viewer and Terminal operate on shared files and configuration.
Task execution produces inspectable artifacts with source provenance. Failed
operations preserve inputs and expose errors; dependent jobs require completed
prerequisites. The default desktop does not show a case catalogue.

Create a resettable episode for an external runner:

```bash
curl http://127.0.0.1:8790/api/v2/sessions \
  -H 'Content-Type: application/json' \
  -d '{"case_id":"OS-LH-08","mode":"evaluation","seed":4201}'
```

Open its `launch_url` at a 1280×720 viewport. A visual agent receives screenshots,
mouse/keyboard access and demonstration videos selected by the trusted external
runner. It must not receive the semantic action API, authoring mode, filesystem
episode files, DOM inspection or hidden convention. The API does not launch a
model or perform a local agent evaluation.

`POST /api/v2/sessions/{id}/reset` restores the initial resource graph.
Stale implementation/schema sessions are visibly blocked before desktop use.
Reset upgrades them while preserving the workflow, seed, convention and selected
demonstration plan, and clears actions, recording and result for that session.
Create a separate session if you need to retain the old session as evidence.
`POST /api/v2/sessions/{id}/finish` exports deterministic scoring evidence.
The external runner can also call `workflows.evaluate` on a saved episode offline.
`external_task_id` and `external_user_id` are accepted during creation.

`scripts/export_v2_episode.py --session ID --output DIRECTORY` creates separate
agent launch metadata and trusted runner evidence. Matching-context export
requires three compatible videos on distinct seeds, excluding the query seed.
`--condition zero-shot` labels the no-demo control in the trusted bundle.
`--condition wrong-demo --wrong-convention N` provides a blinded contradictory
context. Neither experimental label is supplied to the model.
Never expose `trusted-runner.json` to a visual agent. No model runs locally.

Terminal supports `offline-test`, `workspace-open`, `storage-audit` and
`restore-check`; type `help` for syntax. These operations test actual cached
files, migrated paths, cache cleanup and restored schedules. The source and
output bytes are checked; clicking a job with the right label is insufficient.

For human recording, open `/recording-studio.html`; it creates a fixed 1280×720
workspace scaled to your browser, preserving the recorder/replay coordinates.
The standard `/studio` remains available for development at a fixed viewport.
Both authoring forms offer standard, configure-first and reverse-source plans;
these are valid operation-order variants, not different task answers.
Create a demo, read the authoring instructions, then
click **Start demonstration**. Instructions disappear and the ordinary desktop
opens. Finish through Start → Finish recording. The server records interaction
events and replays them against an isolated fresh state to render a WebM without
screen-sharing permission. The replay must match the recorded final state hash.
This is interaction replay, not a direct screen capture; benchmark manifests
must state the source and whether the actions were human or oracle-assisted.

Verify the engine and real browser paths:

```bash
./test.sh
conda run --no-capture-output -n data_mining python scripts/audit_v2_browser.py \
  --all --convention 0 --output data/v2-audit/a
```

Repeat conventions 1 and 2 and independent seeds. The browser audit operates
through visible controls using trusted reference plans; it is a UI test, not a
VLM baseline. `--video` generates inspectable replay videos. Detailed current
limitations are in [the v2 benchmark card](docs/V2_BENCHMARK_CARD.md).

The implementation is `2.0.0-dev.5`. The earlier dev.4 recording batch was
stopped while domain fidelity gaps were addressed; its partial outputs and
dev.3 videos are diagnostic only. The release target remains 108 current-source
videos (12 tasks × 3 procedures × 3 independent seeds), including healthy and
recovery scenarios. Source inspection, original/edited documents and visible
page-break operations are recorded. No current video release is complete until
the full structural manifest and visual audit pass.
See [the external evaluation protocol](docs/V2_EVALUATION_PROTOCOL.md) and
[current evidence/progress](docs/V2_PROGRESS.md).

After the complete current video matrix exists, run
`python scripts/validate_v2_release.py --root RELEASE_DIRECTORY` for structural
validation, and `python scripts/prepare_v2_visual_review.py --root RELEASE_DIRECTORY`
to prepare the separate visual review. Generating storyboards is not a visual pass.
For exhaustive frame material on one completed video, run
`python scripts/prepare_v2_frame_review.py --results CONTEXT_RESULTS.json
--case OS-LH-03 --seed 1001 --output NEW_REVIEW_DIRECTORY`.
It decodes every frame without temporal sampling, retains every timestamp,
deduplicates only SHA-256-identical RGB24 frames, and verifies the resulting
native PNGs against the source pixels. The gallery and `frames.json` remain
pending review; preparation does not certify visual quality. Native-frame
material can occupy hundreds of MB per clip, so prepare/review it deliberately.
Demonstration seeds must cover all three initial scenarios, including a healthy
fixture; distinct seeds alone do not guarantee this. The standard
1001/1002/1003 set satisfies the generation coverage requirement. Raw native
input notifications are retained in the interaction trace; replay reading
pauses apply to changed text, not repeated identical multiline notifications.
`python scripts/audit_v2_visual_approval.py --root RELEASE_DIRECTORY --template
REVIEW_CHECKLIST.json` creates a pending-only review checklist after structural
validation. Only after actual complete-timeline/critical-transition inspection,
record reviewer, notes, coverage and criteria, then validate with `--reviews
REVIEW_CHECKLIST.json`. This validates attestations, not the truth of a review
or video quality automatically. Sampled-only inspection must remain pending.
With the matching service running, `python scripts/audit_v2_external_exports.py
--release-root RELEASE_DIRECTORY --output EXPORT_AUDIT_DIRECTORY` exercises
real artifact routing, reset and blinded control exports without invoking a model.
Its public and trusted bundles must remain separate. Controls share a query
session; the external runner must reset before each trial and never run them
concurrently. The audit refuses incomplete or stale video sets.

For a fresh Python dependency check, run
`python scripts/audit_v2_clean_environment.py --output CLEAN_ENV_REPORT.json`.
It installs pinned pytest/Playwright into a task-owned temporary virtual
environment, copies source and the tracked historical compatibility manifest,
runs the full tests, portable startup and an isolated native-input replay check.
It requires package-download access and does not alter the active interpreter.
Chrome/FFmpeg are still supplied by the host; this is not a second-machine
reproduction or a visual-agent evaluation.

For a trusted source-only audit archive, use
`python scripts/audit_v2_source_archive.py --archive SOURCE_SNAPSHOT.tar.gz
--output SOURCE_AUDIT_REPORT.json`. It checks archive membership before extraction,
rejects runtime state/caches/links and escaping paths, verifies the recording
source fingerprint, and runs full tests and portable startup from an extracted
path with spaces. It executes the archive's test code: do not run this on
untrusted archives. A source snapshot excludes demonstration videos and runtime
episodes, can include uncommitted development files, and is not a versioned Git
release, independent-machine reproduction or completed benchmark acceptance.

## Historical v1.0.0 documentation

The following sections describe the archived 36-case benchmark, available through
`/api/v1/` and `/legacy`. Its videos are not demonstrations for the new tasks.
Version 1.0.0 contains 36 executable cases and 108 hidden case-rule contexts across selection, action mapping, ordering, state machines, recovery, and cross-application transfer.

The simulated files, processes, devices, commands, settings, and failures never touch the host operating system.

## Demonstration videos

The complete canonical video set is committed under
[`benchmark_videos/v1.0.0/`](benchmark_videos/v1.0.0/). It contains 108 WebM
files: one independently recorded demonstration for every case-rule context.
See the [video-set README](benchmark_videos/v1.0.0/README.md) for format,
manifest mapping, checksum validation, and evaluation guidance.

## Start

```bash
git clone https://github.com/peilin717/OS-ICL.git
cd OS-ICL
conda env create -f environment.yml
conda activate data_mining
./run.sh
```

Open `http://127.0.0.1:8790/` for the simulated desktop. Open
`http://127.0.0.1:8790/studio` only for benchmark authoring and recording.
To use another port:

```bash
./run.sh --port 9000
```

`run.sh` uses the Conda environment `data_mining` declared in
`environment.yml`. The HTTP server itself has no third-party runtime
dependency; Playwright and a Chromium-compatible browser are required only for
server-side demonstration rendering.

## Main workflows

### Use the simulated OS

The root URL opens the operating system rather than the case catalogue. It
provides a frontend-only but stateful desktop with overlapping windows, a Start
menu, taskbar, quick settings, notification centre, hierarchical Files app,
multi-level Settings, System Monitor, simulated Terminal, Devices, Jobs,
Transfers, Text Editor, and Calendar. File and setting changes remain in the
current browser session and never touch the host computer.

### Record a demonstration

1. Open `/studio`, choose rule `0`, `1`, or `2`, then click **Record demo**.
2. Read the recorder brief.
3. Click **Start demonstration**. No browser screen-sharing permission is needed.
4. Perform the task in Vibe OS.
5. Click **Finish and build video**.
6. The server validates the trajectory and, when it passes, replays it in an isolated Chrome process to create a clean WebM video. Only successful demonstrations enter the demo library.

When recording starts, the simulator switches to a full 16:9 operating surface. The recorder brief and studio controls are removed from the workspace so computer-use sees the same 1280×720 geometry as the generated replay.

### Build the canonical 108-context release

The canonical release contains one independently recorded demonstration for each
of the three hidden rules of every case. Create the resumable authoring queue:

```bash
conda run --no-capture-output -n data_mining python \
  scripts/prepare_computer_use_queue.py \
  --seed-base 1000000 \
  --output data/recording-queues/os-icl-1.0.0.json
```

Perform the queued actions through the visual interface, then finalize and audit:

```bash
conda run --no-capture-output -n data_mining python \
  scripts/finalize_computer_use_queue.py \
  --queue data/recording-queues/os-icl-1.0.0.json \
  --manifest data/manifests/os-icl-1.0.0.json
```

The finalizer rejects missing, failed, malformed, incorrectly sized, or incomplete
videos and requires exactly 36 entries for each rule. The canonical v1.0.0
videos are published in `benchmark_videos/v1.0.0/` and identified by SHA-256 in
the committed manifest. Working recordings under `data/videos/` remain ignored
so authoring runs cannot accidentally enter Git history.

The brief disappears before the demonstration starts and is never present on the replay-only page. Each recording also stores a structured semantic trajectory and deterministic episode state. The renderer uses the existing `/usr/bin/google-chrome`; install the Python dependency declared in `environment.yml` when setting up a fresh machine.

### Run an evaluation

Open `/studio`, choose a case, and click **Run evaluation**. The server randomly selects a hidden rule and seed. Matching successful demonstration videos are shown when available. Complete the query in the simulator and click **Finish and evaluate**.

## Agent API

Create an episode:

```bash
curl -s http://127.0.0.1:8790/api/v1/sessions \
  -H 'Content-Type: application/json' \
  -d '{"case_id":"OS-SEL-01","mode":"evaluation","seed":42}'
```

Send a semantic action (debug/oracle integrations only):

```bash
curl -s http://127.0.0.1:8790/api/v1/sessions/SESSION_ID/action \
  -H 'Content-Type: application/json' \
  -d '{"verb":"select","target":"item-1"}'
```

Finish and score:

```bash
curl -s -X POST http://127.0.0.1:8790/api/v1/sessions/SESSION_ID/finish \
  -H 'Content-Type: application/json' -d '{}'
```

For strict VLM evaluation, open the returned `launch_url` in a browser at a fixed `1280×720` viewport and allow the agent to use screenshots plus mouse/keyboard coordinates. Do not expose DOM, the semantic action endpoint, or saved episode JSON to the model.

## Existing-platform integration

The simulator is deliberately a separate service. An existing platform can:

1. `POST /api/v1/sessions` with `external_task_id` and `external_user_id`;
2. embed the returned `launch_url` in an iframe or open it directly;
3. listen for completion by polling `GET /api/v1/sessions/{id}`;
4. read the result and artifact URLs from the session payload.

Production deployments should reverse-proxy it under the same origin, for example `/os-sim/`, and add authentication in the parent platform or reverse proxy.

## Repository layout

```text
cases.py           36-case catalogue, generators, hidden policies
server.py          HTTP API, session storage, recording upload, evaluator
static/            English-only simulator and studio UI
static/os-shell.js Stateful desktop, window manager, apps, and frontend stores
static/os-shell.css Desktop and application visual system
tests/             determinism, coverage, privacy, and evaluation tests
data/episodes/     generated session manifests (git-ignored)
data/videos/       uploaded WebM demonstrations (git-ignored)
```

## Test

```bash
./test.sh
```

The test suite validates all 36 cases under all three hidden rules and multiple seeds, including rule-text/oracle agreement, visible ordering tie-breaks, two-step recovery, cross-application navigation, version isolation, and hidden-policy privacy.

See [the benchmark card](docs/BENCHMARK_CARD.md), [integration contract](INTEGRATION.md), and [contribution guide](CONTRIBUTING.md) before publishing results or adding cases.

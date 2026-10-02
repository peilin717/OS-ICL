# OS-ICL Bench

OS-ICL Bench is a deterministic, English-only browser operating-system simulator for recording VideoICL demonstrations and evaluating visual agents. Version 1.0.0 contains 36 executable cases and 108 hidden case-rule contexts across selection, action mapping, ordering, state machines, recovery, and cross-application transfer.

The simulated files, processes, devices, commands, settings, and failures never touch the host operating system.

## Start

```bash
git clone https://github.com/peilin717/OS-ICL.git
cd OS-ICL
conda env create -f environment.yml
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
videos and requires exactly 36 entries for each rule. Release videos are stored
outside Git and are identified by SHA-256 in the committed manifest.

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

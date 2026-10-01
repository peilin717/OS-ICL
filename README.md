# Vibe OS-ICL

Vibe OS-ICL is a deterministic, English-only browser operating-system simulator for recording VideoICL demonstrations and evaluating visual agents. It contains 36 executable cases across selection, action mapping, ordering, state machines, recovery, and cross-application transfer.

The simulated files, processes, devices, commands, settings, and failures never touch the host operating system.

## Start

```bash
cd /root/VideoICL-bench/OS-ICL
./run.sh
```

Open `http://127.0.0.1:8790/`. To use another port:

```bash
./run.sh --port 9000
```

`run.sh` uses the existing Conda environment `data_mining`. The server itself has no third-party runtime dependency.

## Main workflows

### Record a demonstration

1. Choose rule `0`, `1`, or `2` with the **Demo rule** selector, then click **Record demo**.
2. Read the recorder brief.
3. Click **Start demonstration**. No browser screen-sharing permission is needed.
4. Perform the task in Vibe OS.
5. Click **Finish and build video**.
6. The server validates the trajectory and, when it passes, replays it in an isolated Chrome process to create a clean WebM video. Only successful demonstrations enter the demo library.

The brief disappears before the demonstration starts and is never present on the replay-only page. Each recording also stores a structured semantic trajectory and deterministic episode state. The renderer uses the existing `/usr/bin/google-chrome`; install the Python dependency declared in `environment.yml` when setting up a fresh machine.

### Run an evaluation

Choose a case and click **Run evaluation**. The server randomly selects a hidden rule and seed. Matching successful demonstration videos are shown when available. Complete the query in the simulator and click **Finish and evaluate**.

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
tests/             determinism, coverage, privacy, and evaluation tests
data/episodes/     generated session manifests (git-ignored)
data/videos/       uploaded WebM demonstrations (git-ignored)
```

## Test

```bash
./test.sh
```

The test suite validates all 36 cases under all three hidden rules and multiple seeds.

# Integration contract

This document describes how an existing annotation platform or VLM harness integrates Vibe OS-ICL without depending on its implementation.

## Version

- HTTP contract: `v1`
- iframe message contract: `1.0`
- benchmark version: `1.0.0`
- default service URL: `http://127.0.0.1:8790`

## Create an episode

`POST /api/v1/sessions`

```json
{
  "external_task_id": "parent-task-42",
  "external_user_id": "annotator-7",
  "case_id": "OS-REC-01",
  "mode": "demo",
  "rule": 1,
  "seed": 9134
}
```

Fields:

- `case_id` is required for production use.
- `mode` is `demo`, `evaluation`, or `practice`.
- `rule` is required for controlled demo collection. Omit it for a server-random evaluation rule.
- `seed` is optional. Omit it for a server-generated seed.
- `external_task_id` and `external_user_id` are opaque parent-platform identifiers.

The response contains `id` and `launch_url`. Internal rule text and expected actions are never returned for evaluation sessions.
It also contains `benchmark_version`; reject or isolate episodes from a different
version when comparing results. Demonstration lookup automatically excludes
artifacts produced by older benchmark versions.

## Embed

Use the returned URL in an iframe. When the parent and simulator have different origins, append an encoded, exact parent origin:

```text
/?session=vos_123&parent_origin=https%3A%2F%2Fannotation.example.org
```

For production, reverse-proxy Vibe OS under the annotation platform origin when possible.

## iframe messages

The child emits:

```json
{"source":"vibe-os-icl","version":"1.0","type":"VIBE_READY","episodeId":"vos_123"}
{"source":"vibe-os-icl","version":"1.0","type":"RECORDING_STARTED","episodeId":"vos_123"}
{"source":"vibe-os-icl","version":"1.0","type":"RECORDING_STOPPED","episodeId":"vos_123","videoUrl":"/artifacts/vos_123.webm"}
{"source":"vibe-os-icl","version":"1.0","type":"EPISODE_FINISHED","episodeId":"vos_123","result":{"success":true}}
{"source":"vibe-os-icl","version":"1.0","type":"EPISODE_RESET","episodeId":"vos_123"}
```

The parent must verify `event.origin`, `source`, and `version` before consuming a message.

## Polling and artifacts

- `GET /api/v1/sessions/{episode_id}` returns public status and result.
- `GET /api/v1/demos?case_id=OS-REC-01&rule=1` lists successful demonstrations only after their server-rendered videos are ready.
- `GET /artifacts/{name}` streams a recorded WebM artifact.

Demo recording is semantic: the simulator stores the authoritative UI actions, then an isolated server-side Chrome process replays them into a WebM. The annotator never grants browser screen-sharing permission. While generation is in progress, the session response exposes `video_status` as `queued` or `rendering`; completion uses `ready`, and failures use `error` with `video_error`.

Cross-application episodes include observable `open-app` and `inspect` events
before the target operation. Recovery episodes contain two actions per failed
object. These events are part of the scored trajectory and must not be collapsed
by an integration adapter.

## Strict visual-agent mode

The orchestration service creates an evaluation episode and gives the agent only:

- the demonstration videos;
- the `launch_url`;
- screenshots of the browser viewport;
- coordinate mouse and keyboard controls;
- the final public result after the agent calls Finish.

Do not give a tested model filesystem access, episode JSON, DOM access, accessibility trees, semantic action APIs, or the `rule` used to create the episode.

The semantic action endpoint is intended for debugging and trusted adapters, not for a strict visual benchmark.

## Reverse proxy sketch

The existing platform can proxy `/os-sim/` to port `8790`. When mounting under a path prefix, either strip `/os-sim` in the proxy or configure a dedicated subdomain; the current frontend uses root-relative `/api`, `/styles.css`, and `/app.js` URLs.

## Authentication boundary

The development server intentionally contains no user database. Production access should be protected by the existing platform or reverse proxy. Never expose episode JSON under `data/episodes` as static files.

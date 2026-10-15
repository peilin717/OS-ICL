# Integration contract

## Current v2 desktop integration

The default service is OS-ICL's twelve-task long-horizon development desktop,
currently `2.0.0-dev.5`, resource schema 5. The contract below describes implemented
behavior, not an already-validated production deployment. Recording and external
evaluation use the same desktop; only trusted authoring sees recorder instructions.

### Create and launch

The trusted parent calls `POST /api/v2/sessions`:

```json
{
  "case_id": "OS-LH-09",
  "mode": "evaluation",
  "convention": 2,
  "seed": 4201,
  "external_task_id": "parent-task-42",
  "external_user_id": "annotator-7"
}
```

`mode` is `demo`, `evaluation` or `practice`. Convention selection belongs to
the trusted runner, not the visual agent; conventions are 0/1/2. Parent identifiers
must be opaque and must not encode a hidden convention or control condition.
The response includes an `osl_...` ID, relative `launch_url`, version, compatibility
flag and public state/status. Evaluation responses omit the reference, convention,
required pipeline and authoring brief. A strict visual agent must still not receive
these JSON responses or arbitrary HTTP/DOM access; it receives pixels and controls.

Open `launch_url` on the service origin at a 1280×720 viewport. For human recording,
use `/recording.html?session=ID`; it scales a canonical 1280×720 inner desktop to
the outer browser. `/recording-studio.html` and `/studio` are trusted authoring
entry points, not evaluation surfaces. `plan_variant` optionally selects
`standard`, `configure-first` or `reverse-sources` authoring action orders without
changing the visible initial query or desired output.

### Lifecycle, recording and artifacts

- `GET /api/v2/cases`: twelve public task descriptions; no private pipeline.
- `GET /api/v2/sessions/{id}`: public status, compatibility, result and video status.
- `POST /api/v2/sessions/{id}/reset`: reset state/actions/trace/result. Stale sessions
  are regenerated, preserving task, seed, convention and authoring plan. Export old
  evidence first or create a separate session if it must be retained.
- `POST /api/v2/sessions/{id}/finish`: deterministic outcome evaluation; successful
  demos with a trace are queued for rendering. Failed attempts remain inspectable.
- `GET /artifacts/{name}`: serve the canonical ready WebM copied into `data/videos`.

There is no implemented v2 `/demos` lookup endpoint. The trusted runner uses
`scripts/export_v2_episode.py` to select three compatible, query-disjoint videos
and separate agent launch metadata from trusted evidence. Matching, zero-shot and
wrong-demo controls are labeled only in the trusted bundle. Never give
`trusted-runner.json` to a tested model.

The ordinary desktop records UI events without `getDisplayMedia`. Replay runs the
same handlers from fresh initial state, checks the final state hash, and renders
1280×720 WebM. Timing is normalized for readability; manifests distinguish
oracle-assisted browser audits from human actions. The platform does not invoke
a model or perform local visual-agent evaluation. Demo status can be `queued`,
`rendering`, `ready`, `error` or `interrupted`; inspect `video_error` on failure.
Restarted services mark previously active render work interrupted rather than
claiming it is ready. Source-fingerprint mismatches block unsafe continuation.

### Hash conventions

Virtual resource/provenance hashes produced by `workflows.digest` are SHA-256
of Python's canonical JSON encoding, not necessarily SHA-256 of raw text bytes:

```python
import hashlib, json

def resource_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
```

The default `ensure_ascii=True` is part of this encoding. For a text resource,
`value` is its content string, so JSON quotes and escaped newlines are included.
This applies to file Properties content hashes, media catalogue source/preview
hashes, provenance resource hashes, engine state hashes and recording trace
hashes (the trace value is the UI-event list). Recompute a content
hash from the actual stored string, not from reparsed or reformatted JSON text.
Media preview files describe virtual correspondence and dimensions; they are
not encoded video streams.

By contrast, release `video_sha256` and implementation source-file hashes use
their respective raw file bytes. The implementation
fingerprint hashes the canonical JSON map of source-file hashes. The virtual
signing authority uses HMAC over raw build-content bytes; it is synthetic and
public, not a production credential. Do not use these different hash conventions
interchangeably when checking exported resources and actual WebM artifacts.

### iframe messages and origins

Current v2 emits only these informational messages:

```json
{"source":"os-icl","type":"OS_ICL_READY","episodeId":"osl_123"}
{"source":"os-icl","type":"OS_ICL_FINISHED","episodeId":"osl_123"}
```

They contain no result or version field. READY means the session page is loaded,
not that the author clicked Start demonstration. FINISHED means the desktop
finished the session, not that asynchronous video rendering is complete. Poll
the trusted session API for final results and ready video URLs. There is no v2
recording-start message or inbound parent command protocol implemented yet.

Messages target the simulator's own origin. The v1 `parent_origin` query parameter
does **not** enable cross-origin messaging in v2. A same-origin parent must check
`event.origin`, `event.source === iframe.contentWindow`, `data.source`, expected
episode ID and the allowed type before accepting messages. The recording host
relays its inner desktop's messages only to a same-origin parent.

Cross-origin iframes can display the desktop, but the parent must use trusted
server-side status polling rather than expecting those messages. For deployment,
serve the simulator at the root of a dedicated origin, or explicitly map all
root-relative routes/assets on a common origin. Merely stripping an `/os-sim/`
prefix does not fix root-relative `/api/v2`, `/desktop.js`, `/desktop.css`,
`/recording.html`, `/recording-studio.html` and `/artifacts` requests, or the
recording host's root desktop iframe. No production proxy configuration has been
tested here.

### Access boundary and verification

This local authoring server has no production authentication. The existing
platform/reverse proxy must supply access control and separate trusted adapters
from visual agents. Do not expose `/studio`, demo creation, semantic `/action`,
`/ui-event`, `/replay`, saved episode files, source code or trusted export bundles
as model tools. Browser-internal requests may run; the agent itself must be
limited to screenshots and coordinate mouse/keyboard controls.

After all current videos exist, `scripts/audit_v2_external_exports.py` validates
the real artifact/query/reset/export interfaces. Passing unit checks or documenting
this contract is not evidence of a working parent-platform production integration.
Shared query sessions must be reset between experimental conditions and never
run concurrently. See `docs/V2_EVALUATION_PROTOCOL.md` for evaluation ownership.

## Historical v1 integration

The remaining sections describe the archived 36-case Vibe OS-ICL interface.
They are not the current v2 desktop or its demonstration protocol.

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

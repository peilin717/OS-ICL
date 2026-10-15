# External visual-agent evaluation protocol

The simulator supplies a desktop, reproducible resources, demonstration videos
and scoring evidence. Model execution belongs to the external runner. Reference
browser audits are trusted UI tests and are not visual-agent baseline results.

## Dataset unit and splits

One context is a task plus demonstrated operating procedure. The 12 tasks each
have three procedures: interactive preparation, reversible preparation, and
audited delivery. Their steps and configuration differ, not just folder names.
For a fixed task/query seed, all contexts begin with identical visible resources.

The canonical demonstration seeds are 1001, 1002 and 1003. They include healthy
and recovery-triggering resource states. Reserved query seeds are 42, 173 and
4201. Query seeds must not also occur in the selected demonstrations. This
produces 108 query episodes over 12 tasks × 3 contexts × 3 query seeds.

Episode reuse must match schema version, benchmark version and implementation
fingerprint. A version string alone does not establish artifact compatibility.
The working release is developmental until its complete manifest and visual
review pass. Examples from earlier development fingerprints are diagnostic data.

## Agent-facing inputs

Give the model the business task text, the selected demonstration videos and
screenshots of the launched query desktop. Use the 1280×720 evaluation viewport.
Allow mouse movement/clicks, keyboard input, scrolling and window manipulation.

Keep the convention ID, reference plan, full episode JSON, scoring predicates,
semantic action endpoint, DOM inspection and authoring Studio outside the model's
input and tools. A controller may use the API for session setup/reset/finish,
but the model performs task actions through the same UI as people.

The terminal is a virtual desktop application. Its documented workspace commands
are valid UI actions. It cannot run host shell commands or arbitrary JavaScript.
The signing authority, media resources and network devices are simulated and
declared as such in the benchmark card.

## Experimental controls

Use identical query initial states and declared budgets across paired controls:

- Matching: three same-task, same-context, query-disjoint demonstration videos.
- Zero-shot: the same task and query state with no demonstration videos.
- Wrong-demo: three same-task videos from a different context. Balance the two
  possible alternative contexts in the study.
- Temporal ablation: a separately identified transformation of matching videos,
  with its frame permutation/removal and source checksums saved by the runner.

`scripts/export_v2_episode.py` supports matching, zero-shot and wrong-demo launch
bundles. Experimental labels belong in `trusted-runner.json`; the agent launch
metadata does not tell the model that its demonstrations are contradictory.
Do not describe control conditions in the model's task prompt.

Temporal transformations are not canonical demonstrations. Do not upload them
to the matching-context demo library, and do not claim this development version
already contains a temporal-ablation experiment or measured video gain.

## Session lifecycle

1. Create a query using `/api/v2/sessions`, with mode `evaluation`, task/context
   chosen by the trusted runner, and a held-out query seed.
2. Export the launch bundle. Matching/wrong-demo export refuses missing or
   incompatible video contexts instead of quietly running a no-demo query.
3. Launch the URL and execute the agent with its declared observation/action
   limits. Record model, prompt, video handling, frame sampling, budgets, errors
   and all controller actions in the external study manifest.
4. Finish through the UI or the trusted finish endpoint. Preserve the complete
   state/interaction evidence separately from the model input.
5. Reset the resource graph before another trial. A reset of an obsolete
   development episode upgrades it, so it is not a same-version comparison.

## Reporting

Report strict success, learned-procedure compliance, side-effect freedom,
partial credit, action count and timeout/error rates per template and context.
Strict success requires all current task predicates, rather than only creating
a file with the expected name or clicking a task with the right operation label.

Give every template equal weight in the primary aggregate and show the episode
counts. Use paired matching/zero-shot and matching/wrong-demo contrasts on the
same query states. Document the uncertainty method and its sampling unit;
multiple seeds from the same template are not independent task templates.

Publish representative successes and failures, including uncorrected agent
mistakes. Browser reference success proves UI reachability, not that a model
inferred a rule or that the benchmark has an established ICL effect. Such claims
require the external study results, which are not produced by this repository's
local oracle tests.

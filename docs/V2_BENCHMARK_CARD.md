# OS-ICL 2.0 development benchmark card

## Intended measurement

Infer demonstrated operating conventions and execute long desktop workflows on
new project resources. Query goals describe the business outcome, not directory
names, renaming conventions, scheduler configuration or verification depth.
For a fixed task/seed, all three contexts begin with identical visible state;
successful outputs differ with the demonstrated convention. Counterfactual
tests reject a solution learned from the wrong convention.

## Implemented environment

Nine ordinary applications, shared resource state, nested project folders,
movable/resizable overlapping windows, Start/taskbar, file copying and moving,
editing, configuration forms, devices, transfers, process locks, task dependencies,
inspectable outputs and error logs. Source files use CSV/JSON/code/text formats.
Media, printing, builds and archives are virtual resources; no host OS processes,
real network transfers, actual printer jobs or media codecs are invoked.

The 12 task templates cover research handoff, release, backup/recovery, media
ingest, print production, offline kits, migration, build recovery, evidence
archiving, distribution, storage maintenance and restoration. Reference plans
currently involve at least 25 state-changing successful actions, with additional
navigation and visible recovery attempts. Empty clicks and no-op settings do
not count toward this threshold.

Domain-specific operations now include approved-source folders and historical
revisions, caption-to-take correspondence, actual page-break layout, disconnected
cache access, manifest path rewriting and launch tests, time-window log filtering
with an edited timeline, scheduled rather than immediate distribution, verified
backup before cache deletion with byte accounting, and restored task schedules.
These additions still need richer branch-balanced contexts and independent
benchmark validation; they do not by themselves establish paper-level quality.

## Contexts and splits

Three conventions vary working/delivery directories, copy prefixes, archive
format, verification mode, scheduler trigger, retention and the actual procedure.
Reversible preparation checkpoints before processing; audited delivery records
the verified dependency trail. Interactive preparation uses the core workflow.
They are bounded organizational procedures; empirical ICL gains are unmeasured.
Demo and query seeds must be disjoint, project names/values change per seed,
and a released context must include at least three successful demonstration
seeds. Seeds alone do not constitute held-out task templates.

## Measured reference structure

`scripts/audit_v2_complexity.py` measured 216 engine reference paths: twelve
tasks × three conventions × six seeds (demo 1001/1002/1003 and query 42/173/4201).
The following are observed min–max ranges at implementation fingerprint
`625d90035280d3364cbebcc2a7a57ea074165e2fc80276f57281333477bbfe7c`.
Meaningful mutations exclude rejected attempts, failed outcomes, property reads
and unchanged state. Dependency depth counts jobs in the longest actual job
chain, not mouse clicks, file/process dependencies or elapsed video time.

| Task | Meaningful mutations | Job dependency depth |
|---|---:|---:|
| 01 Research handoff | 25–33 | 6–7 |
| 02 Release preparation | 28–44 | 7–8 |
| 03 Backup and recovery | 25–44 | 6–7 |
| 04 Media ingest | 26–43 | 6–7 |
| 05 Print production | 27–45 | 6–7 |
| 06 Offline field kit | 28–42 | 6–7 |
| 07 Workspace migration | 28–37 | 6–7 |
| 08 Failed build recovery | 27–52 | 7–8 |
| 09 Evidence archive | 27–43 | 6–7 |
| 10 Scheduled distribution | 27–35 | 7–8 |
| 11 Storage maintenance | 33–41 | 7–8 |
| 12 Project restoration | 29–43 | 6–7 |

Report: `data/v2-audit/rc4-structural-complexity/report.json`. These measurements
describe the reference scaffold, not empirical agent difficulty or measured
ICL gains. Successful references cannot substitute for external agent controls,
video inspection or a review of task-specific causal behavior.

## Scoring

Final state predicates check staged copies, preserved originals, an edited index,
completed dependency chains, configured conventions, output locations, immutable
provenance, materialized restoration data and verification receipts. Harmless
navigation, inspections and independent configuration order do not reduce success.
Scores expose goal success, rule compliance, side-effect freedom and partial
credit to the trusted runner. Exact mouse trajectory is not a success predicate.
Delivered resource membership, captions, layout pages, offline probes, migrated
references, event scope/redaction, pending distribution and restored schedules
also receive explicit checks. Probe receipts are invalidated by changed files.

## Recording provenance

Interaction events include selectors, input values, coordinates, keyboard
modifiers, scrolling and window geometry. Replay invokes the same handlers in
a fresh state and verifies the final hash before accepting the video. The video
is a rendered replay, and its timing is normalized for readability. Browser
audit videos are oracle-assisted automation, not human or VLM demonstrations.
Public datasets must include these distinctions and hashes, with source traces
kept separate from agent-facing video distributions.

## Trust boundary

This is a local authoring service without production authentication. The strict
visual runner must restrict the model to pixels and coordinates; it must not
give it arbitrary HTTP access, DOM, `/studio`, demo creation, semantic actions,
saved state or trusted Python references. Evaluation session responses omit
convention, reference plan and required pipeline. Authoring endpoints are not
a security boundary by themselves. Parent production deployment supplies auth
and access separation.

## Still required for release

- Stronger task-specific workflows and context variation beyond the common
  staging/index/configuration/job scaffold.
- Condition-balanced demo/query episodes and observed branch coverage.
- Full three-demo-per-context video set, manifests, visual inspection and an
  independent reproducibility run.
- Broader desktop usability testing: edit/retry, clipboard, context menus,
  keyboard, resizing, viewport boundaries and recording edge cases.
- External visual-agent baselines, zero-shot and wrong-demo controls, temporal
  ablations, confidence intervals and template-level reporting.

Passing reference engine tests and browser tests does not satisfy these gates.
The current resource schema is 5 and development version is `2.0.0-dev.5`.
Earlier development episodes must be reset/recreated before new mutations.
Compatibility also requires an identical implementation fingerprint. Dev.3
recordings are diagnostic data because printing lacked a human-accessible
page-break control. Current recording uses that control and source inspection.

Build testing is virtual: a dedicated task compares exported source metadata
with configured expectations and materializes a result anchored to the build
hash. It does not execute JavaScript in a host runtime. Rendered test-result
inspection, failed-assertion diagnostics and repaired stages are workflow
evidence, not proof of real compiler/runtime behavior.

Evidence privacy practices differ by demonstration context: mask values, remove
personal fields, or replace them with stable synthetic pseudonyms. All methods
are usable in every context; runtime errors never select the hidden convention.
The evaluator checks actual output records, not merely a settings switch.
Pseudonyms are deterministic truncated hashes for synthetic data and are not
secure anonymization: they are dictionary-attackable and linkable. This platform
must not be used to process real personal information.

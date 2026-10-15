# Completion audit — 2026-10-15

The objective is not complete. This audit separates implemented behavior from
the full task design in V2_TASK_DESIGN.md. Video production is provisional and
does not override missing design requirements.

## Latest current-source evidence

Current recording observation: 108/108 videos completed (A/B/C: 36/36/36),
all with successful results, replay equality and zero browser errors in the
recording result rows. Full release validation and visual approval remain
separate gates; generated result rows alone do not satisfy them.
Task-12/context C/seed
1001 now has all six sampled storyboard pages inspected, plus native incomplete-
snapshot and restore-check frames and an independent persisted-state check of
local-edit preservation, existing-task identity/configuration repair and missing-
task creation. These are scoped observations, not full visual approval. The
runtime fingerprint is unchanged. V2_PROGRESS.md records the precise evidence.

Latest follow-up: the repaired release/context B/seed 1001 preflight completed
successfully at 1280×720, 176.56 seconds, with replay equality and zero browser
errors. Complete decoding passed; six sampled storyboard pages and native
follow-up frames were inspected. The previous clip's 263.44-second presentation
and this clip have the same final state hash and 51 semantic agent steps.
Fresh current-source held-out reproducibility, portable startup, editor safety,
property dwell, nine-app geometry and scaled recording-host checks passed.
Three full rc4 workers are now live, with unchanged fingerprint sources.
This is not a full 108-video matrix or complete visual/export approval.
Earlier paragraphs below document their state at the time of those observations.

Latest regression: 213 tests passed in 78.43 seconds, including public-query
boundary, source-archive membership, citation and static-containment checks.
This is source/test evidence, not a
complete video-quality or external-export acceptance result.
After twelve source-archive membership tests were added, an actual source-only
development archive passed all 200 tests in 51.36 seconds and portable startup
from its extracted directory. Its runtime hashes match the recording fingerprint.
This is a verified audit snapshot, not a committed version or final release.
Fresh dependency/source-copy follow-up also passed all 179 tests in 49.95 seconds,
portable startup and native-input replay after both copy helpers included the
public citation file. Existing host Chrome/FFmpeg are still used; independent-
machine reproduction remains unproved.

Update: rc3 was stopped after a reproduced multiline-input replay defect.
Fifteen videos (five per context) remain diagnostics, not a release. Repeated
native input notifications no longer cause repeated reading pauses; the authentic
trace is retained. Isolated real-browser presentation replay and full regression
(163 tests in 60.95 seconds) passed. A release/context B video preflight at the new fingerprint
`625d90035280d3364cbebcc2a7a57ea074165e2fc80276f57281333477bbfe7c`
is still running. The rc3 evidence in the following paragraphs is historical,
not evidence of a current complete video matrix. Details are in V2_PROGRESS.md.

The frozen rc3 implementation is
`ea90b4c13a68f1b94f32fc1010191c7197c798798cdfdc65de8bda4dcc828070`.
Current-source full regression passed 158 tests. Cross-process reproducibility
passed 108 held-out engine paths per process at query seeds 42/173/4201 in two
fresh processes with matching initial/reference/event/final hashes; report
`data/v2-audit/rc3-held-out-reproducibility/report.json`. Portable-checkout
startup/query/reset and fourteen wrapper tests also passed at this fingerprint;
report `data/v2-audit/rc3-portable-checkout/report.json`. Neither establishes a
fresh dependency installation, a second-machine run or a model baseline.

Three recording workers are live. The checked progress snapshot contains nine
completed videos (tasks 01–03, all three contexts, seed 1001), each with successful
scoring, verified replay hash and zero browser page errors. All three task-03
videos passed complete FFmpeg decoding. Current video/run evidence is
`data/v2-release/2.0.0-dev.5/rc3/context-*/results.json`; earlier rc1/rc2/dev.4
references below are explicitly historical evidence, not current release demos.

Task-03/context B/seed 1001: all six four-second storyboard pages were inspected.
Native 1280×720 frames over 148–162 seconds additionally show the missing-note
diagnostic, Include text documents changing Off→On, and the upstream reset
sequence; the frame at 179 seconds shows all seven jobs Completed with delivery
to Handoff. Sampled inspection also shows the earlier restore collision and
separate recovery destination, retained backup versions and regenerated note
content. These observations support specific recovery/readability behavior,
not whole-timeline/critical-transition approval. Visual dispositions remain
pending and the 108-video matrix/full export audit remain incomplete.

## System requirements

Latest session/recording preflight: 122 tests passed in 58.28 seconds. Real
browser checks passed stale-session upgrade/reset, preservation of authoring
plans, authoring plan selectors, settings wheel replay, nine applications at
three desktop viewports, and three scaled recording-host viewports. Recording
pages are now part of the source fingerprint. Earlier browser/video results
remain regression evidence at their recorded fingerprints. A rendered privacy
preflight completed (148.72 seconds, 1280×720, verified replay). Its five
four-second storyboard pages were inspected, not all short transitions. A
subsequent persistent-scroll repair changed the source fingerprint, so that
video remains historical diagnostic evidence, not current release approval.
The repair passed full UI replay and all 122 tests; full 108-video production
was launched under `data/v2-release/2.0.0-dev.5/rc1` at fingerprint
`cf1e1f0f76aab25ec841695784b47919e9775be404ed3799ba7d45942d466d5c`.
It was deliberately stopped after visual review found property panels visible
for only roughly 350 ms. Three first-task videos completed, but they are not
approved release demos. All three parent processes exited after their exact
render children were terminated; files were retained. Properties now dwell
2.5 seconds, changed settings 1.2 seconds, and opened outputs/terminal results
2 seconds. A real browser measured 2856.5 ms property visibility with approval
metadata within the panel and verified replay. Full tests passed 136/136 in
57.62 seconds. The readable-properties preflight then completed: 236.04 seconds,
1280×720, successful final state and replay. Eight full-timeline storyboard
pages and a native metadata frame were inspected; this is scoped readability
evidence, not complete video approval. Full regression passed 144/144 in
57.88 seconds. The subsequent 108-video production ran under rc2 at fingerprint
`34f2cb5ff55904be128743875d94ff1daf4bd3c0e22638a61f8433fb3b481683`.
The complete matrix, full visual approval and real external-export audit remain
incomplete.

rc2 was stopped after a real editor regression reproduced silent loss of an
unsaved draft when opening a different file. All three workers are terminal;
17 completed videos (6/5/6 by context) remain diagnostic artifacts. No files
were removed. The Open flow now uses Save/Discard/Cancel, same-file opening
retains drafts, and rejected locked saves preserve both draft and saved bytes.
Ordinary owner pause/retry works. Browser checks cover all these paths with
mouse/keyboard document selection and fresh-fixture replay hash equality.
The fixture replay transport is isolated testing, not a completed benchmark.
Full regression passed 144 tests in 58.67 seconds; separate whole-workflow and
close-usability replay evidence is recorded in the progress log. Current-source
videos must be produced again after this functional repair.

Final keyboard follow-up fixed Escape cancellation when an input has focus.
Document navigation/locked-save retries, native keyboard selection, clipboard
focus isolation, readable properties and replay checks passed. Full tests passed
144 in 57.83 seconds. Complete OS-LH-07/context C and OS-LH-08/context B workflows
also passed usability/fresh replay at the final fingerprint. New full rc3 batches
are active at
`ea90b4c13a68f1b94f32fc1010191c7197c798798cdfdc65de8bda4dcc828070`.
They are not a completed matrix or a video/export approval.

Visual-review record validation now requires matching implementation/video
hashes, explicit whole-timeline/critical-transition scope, complete finite
coverage, reviewer and specific notes, and all visual criteria. Pending templates
cannot approve themselves; sampled-only records are rejected. Fourteen synthetic
record-gate tests passed (36 with structural/export-privacy controls). This
validates attestations, not actual visual quality or reviewer truthfulness.
rc3's first three research/seed-1001 videos completed; source-PTS storyboards
were generated. Only the first/last pages of context A were inspected this
follow-up, so none received whole-video approval.

Portable launch evidence: a source-only temporary checkout in a path with spaces
was launched from outside its directory using the selected active interpreter.
CLI help, twelve-task HTTP catalogue, evaluation-query privacy/reset and fourteen
wrapper tests passed with the same recording fingerprint. Launchers no longer
require a personal Conda path. This does not prove a clean dependency installation
or independent-machine reproduction. rc2's first three videos completed; the
first storyboard page of each context was inspected with source PTS labels,
confirming visible version/approval/owner metadata and lock diagnostics in those
sampled scenes. The remaining timeline and short-transition review is pending.

| Requirement | Current evidence | Disposition |
|---|---|---|
| Default OS desktop, twelve new tasks | `static/desktop.js`, `/api/v2/cases`, HTTP tests | Implemented |
| Pale English Windows-style UI | rendered desktop/geometry checks, recording screenshots | Implemented; broader usability review pending |
| Shared persistent resources and real dependencies | reducers in `workflows.py`, domain negative tests | Implemented |
| Procedural ICL rather than arbitrary symbols | `protocols.py`, identical-query and wrong-procedure tests | Implemented; external model effects unmeasured |
| Long tasks across at least three apps | current browser trajectories, meaningful-mutation threshold | Implemented in reference paths; full matrix pending |
| Recording without display capture | UI-event capture, real-handler replay/hash validation | Implemented |
| Human-accessible recording actions | page-break repair, scaled recording host tests | Implemented for observed paths; full usability review pending |
| Complete three-demo-per-context matrix | current rc4 contains all 108 recording result rows; historical stopped batches excluded | Generation complete; full structural validation and visual approval pending |
| Full visual quality audit | progressive storyboard index and sampled inspections | In progress, not a visual pass |
| External evaluation interface | launch/export bundles, resets, blinded controls | Implemented; held-out full-video export check pending |

## Task-design fidelity gaps

The user requested high-complexity long workflows. The detailed design also
promised the following domain-specific features. These must be addressed or
explicitly reviewed before declaring the full designed benchmark delivered.
Passing the current reference plan cannot prove a missing feature.

| Task | Verified domain behavior | Remaining design-specific evidence |
|---|---|---|
| 01 Research | nested inputs and approved updates, metadata-based latest approved selection with variable IDs, higher-numbered excluded draft, revision-bearing index, real owner lock/pause/retry/resume, exact delivered scope | current full browser/video matrix and visual review |
| 02 Release | stage-specific compiler/signing-provider failures, component repair, missing-entry diagnosis and revalidation, version-matched source/config/notes/build, signed output and previous archive preservation | full current browser/video matrix and visual review |
| 03 Backup | real scope/text controls, omitted-note comparison failure and backup/recovery rebuild, versioned history retention, snapshot tamper rejection, atomic restore collisions and actual restored-byte comparison | full current browser/video matrix and visual review |
| 04 Media | camera prerequisite, session organization, sidecar recovery, source/caption/preview correspondence, demonstrated output-size profiles, dimension-bound catalogue and delivered preview bytes | full current browser/video matrix and visual review |
| 05 Print | capability fallback, proof-driven pagination repair, demonstrated forward/reverse order bound to layout/proof/queue, queued document bytes, visible controls and reset guards | full current browser/video matrix and visual review |
| 06 Offline | transfer recovery, cache-scope repair, cache build before disconnection, offline local-byte tests and necessary rebuild | full current browser/video matrix and visual review |
| 07 Migration | seed-varying nested source/config/profile/assets paths, valid initial manifest, application-setting rewrites, launch probe, atomic collision recovery and local-edit preservation | full current browser/video matrix and visual review |
| 08 Build recovery | varying locked source/config and owner, build-config repair, second-stage project/revision assertions, independent test result, actual tested-build/results delivery, upstream reruns and all-owner restoration | full current browser/video matrix and visual review |
| 09 Evidence | incident notification and interval export, variable personal fields, scope-repair gate, materialized masked/field-removed/stably-pseudonymized copies, context-independent tool acceptance and context-specific delivered-byte checks, event/time/message preservation | full current browser/video matrix and visual review |
| 10 Distribution | varying recipient/share, visible access controls, failed read-only dry-run and repair, receipt-bound destination/payload, exact membership, persisted schedule without dispatch | full current browser/video matrix and visual review |
| 11 Storage | verified backup, variable nested cache paths/sizes/owners, property-based scope, preserved non-rebuildable neighbor, prior service-state restoration, exact byte accounting, real zlib artifact and live storage UI | full current browser/video matrix and visual review |
| 12 Restoration | latest-complete snapshot selection, atomic collision and user-edit preservation, varying saved-task names/triggers, missing-task creation and stale-task repair preserving ID, output-directory validation | full current browser/video matrix and visual review |

Authoritative implementation: `workflows.py`, `domain_checks.py`, `protocols.py`.
Alternative-plan engine evidence covers twelve tasks × three contexts ×
two seeds × two nonstandard plans (144 paths), including configure-first and
reverse-sources. Initial query/public payloads remain unchanged. Browser-only
alternative-plan coverage completed: 24/24 paths (all twelve tasks under
configure-first/context B/seed 1001 and reverse-sources/context C/seed 1002),
with successful process exit and replay hash checks. These runs used fingerprint
`821d066f3480c847772dad52a1be32e6c5d201132b2b416be34c9b15a6e581f7`, before
the subsequent scroll-recording repair; they are regression evidence, not a
current-fingerprint video approval. A current-source follow-up independently
passed all 24 browser-only alternative paths at fingerprint
`625d90035280d3364cbebcc2a7a57ea074165e2fc80276f57281333477bbfe7c`:
`data/v2-audit/rc4-alternative-configure-first/results.json` and
`data/v2-audit/rc4-alternative-reverse-sources/results.json` each contain twelve
successful rows with replay equality and zero browser errors. These runs have
no videos and therefore do not establish visual approval. Do not interpret
implemented clauses as a complete task-design or release-video approval.
Authoritative video/run evidence: `data/v2-release/2.0.0-dev.4/context-*/results.json`.
The dev.4 batch has been stopped; its files are provisional historical regression
evidence, not proof of the dev.5 implementation. Do not resume into its output
directory with changed source fingerprints.

## Recording presentation regression

Evidence privacy follow-up: all nine browser-only paths (three contexts ×
three seeds 1001/1002/1003) passed complete final-state and fresh replay hash
checks at fingerprint
`59c19b07ba207f472ef243362689a221fd5b2310513e5ee836329b74034f8d2a`.
All three processes exited successfully. Full tests passed 116/116 in 61.01
seconds. Results are in `data/v2-audit/evidence-conventions-current-r3`.
Earlier failed harness assertions and the mask-only r2 completion are historical
diagnostic data. No rendered privacy-video approval is inferred from these runs.

An ordinary wheel gesture in a resized Storage & backup window moved the
settings panel to 112 pixels but produced no recorded scroll event. This was
reproduced by `scripts/audit_v2_scroll_ui.py`. Scrollable settings/detail/dialog
and navigation panels now receive stable trace IDs; scroll events capture both
axes at event time and replay restores both axes. The same real-browser test
now records and replays the settings panel at exactly 112 pixels.

This is an isolated client presentation test: a test-only replay response uses
a fresh real initial session because an unfinished navigation-only workflow
cannot pass the production successful-demo gate. It does not establish workflow
success or release-video quality. Full workflow replay regression is separate.
The repaired-source regression passed all 97 tests and one complete browser
workflow (OS-LH-09/context C/seed 1002), including final-state and replay-hash
checks, at fingerprint
`260416d74cf18268394ed560daa4e5bf2b3806e0119837c831318717d95f142b`.
It is not evidence that the full current browser/video matrix has passed.

## Visual inspection performed so far

OS-LH-01/context A/seed 1001: inspected all four timestamped storyboard pages
covering the full sampled timeline at 4-second spacing. Directory creation,
source metadata, copy/rename, index editing, configuration and the six dependent
tasks were visible. No private recorder instructions or Vibe branding appeared
in these sampled frames. Brief transitions and output-artifact inspection still
need review; this is not a full visual pass.

The revised print proof was separately inspected at the native frame showing
the Go-to-line and Insert-page-break controls plus two-page status. This proves
the repaired interaction was represented, not that all print-context videos
have already passed complete inspection.

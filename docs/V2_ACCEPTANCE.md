# OS-ICL 2.0 reconstruction contract

Status: implementation in progress. These are release gates, not claims of completion.

## Superseding task-design instruction — 2026-10-15

The user now requires **36 independent tasks: 12 low, 12 medium and 12 high**.
Read [the current difficulty contract](DIFFICULTY_STANDARD.md) for definitions,
demo/inference separation and quota checks. It supersedes the twelve-only scope
in item 1, the all-task three-app/25-mutation gate in item 2, and the old
twelve-task matrix cardinality in item 12 below. These numbered clauses and the
inventory record the earlier twelve-task reconstruction. They do not prove the
new 36-task design is implemented. Other quality, privacy and evidence gates
remain applicable. Do not mechanically relabel the current twelve candidates
or historical v1 tasks to satisfy the new distribution.

## Non-negotiable requirements

1. The default catalogue contains exactly 12 new long-horizon tasks. The 36 v1
   tasks and their videos remain versioned historical resources, never v2 demos.
2. Every task crosses at least three functional applications and requires at
   least 25 meaningful state mutations in its reference demonstration. Repeated
   clicks, navigation, artificial waits and confirmations do not count.
3. Difficulty comes from real dependencies: inspect inputs, arrange working
   files, configure tools, create and execute jobs, verify outputs, recover
   errors, and deliver artifacts. No arbitrary color/parity/symbol puzzles.
4. Three coherent operating conventions per task must produce different valid
   outputs for the same visible query. Demonstrations identify the convention;
   query instructions do not name it. Each convention has at least three demo
   seeds and independent query seeds. One video per context is insufficient.
5. A default English desktop with pale neutral surfaces, taskbar, Start, movable
   and resizable overlapping windows, nested navigation, dialogs, context menus,
   search, editable forms and keyboard support. No Vibe branding in current UI.
6. Tasks execute in the same desktop used for free exploration. No task-specific
   answer cards, exposed checklist, auto-solve button, or separate toy task UI.
7. File, configuration, process, device, transfer and scheduler applications use
   one authoritative resource graph. Backend enforces prerequisites. Failed
   operations leave inspectable errors and do not silently mutate output.
8. Score final state, output provenance, required dependency invariants and
   prohibited side effects. Allow harmless navigation and equivalent valid
   action orders; do not score exact mouse paths as task success.
9. Evaluation surfaces omit policy, reference actions, scoring predicates and
   future branch answers. Trusted authoring/export is separate. Check payload,
   DOM, recordings and artifact endpoints, not just top-level JSON keys.
10. Recording captures actual browser interaction with timestamps, input values,
    window/page changes and dialogs, without getDisplayMedia. A replay must
    reproduce state hashes; synthetic semantic animation is not a human demo.
11. External runner owns evaluation. Export resettable episodes, initial/final
    state, action events, scores and video provenance; no public leaderboard or
    online model API is required. Parent integration remains documented.
12. Release requires all 12 × 3 conventions tested over multiple seeds, negative
    and counterfactual controls, browser-only reference demonstrations, full
    video inspection, fixed landscape viewport checks, and an honest benchmark
    card with limitations. No claim of paper-ready quality before these gates.

## Task inventory

| ID | Workflow | Shared dependencies |
|---|---|---|
| OS-LH-01 | Research handoff | Files, Editor, Scheduler, Event Viewer |
| OS-LH-02 | Release preparation | Files, Settings, Scheduler, Event Viewer |
| OS-LH-03 | Backup and recovery | Files, Settings, Scheduler, Transfers |
| OS-LH-04 | Media ingest | Devices, Transfers, Files, Scheduler |
| OS-LH-05 | Print production | Files, Editor, Devices, Scheduler |
| OS-LH-06 | Offline field kit | Transfers, Settings, Files, Scheduler |
| OS-LH-07 | Workspace migration | Files, Settings, Editor, Scheduler |
| OS-LH-08 | Failed build recovery | Monitor, Files, Settings, Scheduler |
| OS-LH-09 | Evidence archive | Event Viewer, Files, Editor, Scheduler |
| OS-LH-10 | Scheduled distribution | Files, Devices, Settings, Scheduler |
| OS-LH-11 | Storage maintenance | Monitor, Files, Settings, Scheduler |
| OS-LH-12 | Project restoration | Transfers, Files, Editor, Scheduler |

## Completion evidence

Each gate needs a committed test or inspectable artifact, command/result, and
scope statement. A passing engine oracle proves engine reachability only.
Browser interactions prove UI reachability. Neither substitutes for video QA
or independent agent baselines. Missing evidence leaves the release incomplete.

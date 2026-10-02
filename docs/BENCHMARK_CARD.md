# OS-ICL Bench 1.0 benchmark card

## Purpose

OS-ICL measures whether a visual agent can infer a temporary operating policy
from video demonstrations and apply it to a deterministic but visually novel
query. It is not a test of memorised Windows shortcuts or host-computer access.

## Scope

- 36 cases and 108 case-rule contexts.
- Seven families: selection, selection set, mapping, ordering, state machine,
  recovery, and cross-application workflow.
- English-only 1280×720 simulated operating environment.
- Three hidden rules per case and seed-controlled counterfactual queries.

## Evaluation protocol

The tested model receives demonstration videos, a query launch URL, screenshots,
and coordinate mouse/keyboard control. It must not receive DOM, accessibility
trees, semantic action APIs, episode files, rule IDs, or rule text. A run is
successful only when its semantic trajectory matches the hidden oracle.

Report goal success, rule compliance, trajectory compliance, side-effect count,
and agent steps. Pin the benchmark version, case ID, rule-independent seed, model
version, viewport, and maximum step budget.

## Design guarantees

- The same case and seed produce identical visible query state for all rules.
- Hidden rules produce three distinct expected trajectories.
- Sorting tie-breaks use visible Index or Layer fields.
- Recovery policies use observable two-step actions.
- Cross-application cases require source inspection and application switching.
- Successful actions produce visible state feedback.
- Evaluation API responses exclude the hidden rule and expected actions.

## Limitations

The environment is a safe browser simulation. It does not execute shell commands,
access user files, connect real devices, or reproduce every timing property of a
desktop OS. Results should be described as simulated OS policy induction, not as
general real-computer autonomy.

## Licensing and artifacts

Source code is MIT licensed. Generated videos are deterministic benchmark
artifacts; distribute them with the release manifest and checksums. Confirm the
license of any future third-party media before adding it.

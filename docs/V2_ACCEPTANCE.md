# OS-ICL acceptance requirements

1. Exactly 36 independent task families, with 12 Easy, 12 Medium and 12 Hard, following `DIFFICULTY_STANDARD.md`.
2. Demonstrations show local transferable rules. The library contains one video per task/condition, 108 total; each query receives one matching video on a disjoint example.
3. A/B/C share visible query starting resources but require different rule-dependent results. Difficulty follows inference dependencies.
4. Tasks use the ordinary English desktop and its nine applications. Hard workflows require actual content or state transfer across interfaces.
5. Judges read authoritative persisted state and validate results, provenance, dependencies and prohibited side effects. Equivalent valid action orders are allowed.
6. Visual agents receive videos/screenshots and use mouse/keyboard. Hidden rules, references, semantic endpoints, DOM inspection and scoring evidence remain trusted-side only.
7. Recordings preserve actual interaction, readable inputs/actions/results and timestamps. Browser replay must reproduce final-state hashes. Recording authorship must be explicit.
8. Video publication requires complete quota, matching source provenance, successful judges, replay checks, full decoding and reading-view coverage. State test success is separate from visual review.
9. Reports distinguish local-demo validation, full-query browser acceptance and independent model evaluation. Keyframe review is described with its actual scope.
10. Release assets carry SHA256 checksums. Generated episodes and videos are distributed separately from source control.

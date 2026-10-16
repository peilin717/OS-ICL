# Task design instructions

For task design, difficulty labeling, catalogue changes or benchmark acceptance,
read `docs/DIFFICULTY_STANDARD.md` in full before acting. The user requires exactly
36 independent task families: 12 low, 12 medium and 12 high. Do not change this
quota without explicit user instruction, count A/B/C or seeds as separate tasks,
or fill quotas by relabeling duplicate tasks. Difficulty follows necessary
business dependencies, not clicks, video duration or arbitrary hidden rules.

Use the user's exact definitions: Easy repeatedly applies the same demonstrated
rule during inference; Medium embeds that rule as one module of a long-horizon
inference workflow; Hard is Medium plus necessary interactions across existing OS functional
interfaces, per the user's latest clarification. Do not require new external
platforms or new system features. Difficulty is primarily inference execution,
not demonstration-rule complexity. Opening additional windows alone is not
sufficient: interfaces must consume each other's content or state.
See docs/TASK_CATALOGUE_36.md for task design and implementation scope. Query fixtures, persisted-state
judges and separate local-method demos are implemented in tasks36.py/judge36.py.
The 36-task catalogue is exposed at /studio and /studio36. Private resource templates support shared engine regression tests.
Do not equate local-demo success with full-query browser acceptance or independent
model evaluation. Recording provenance must remain explicit.

Current acceptance and privacy requirements are in docs/V2_ACCEPTANCE.md.
The standard library has one video per task/rule condition, 108 total.
Each query receives one matching video on a query-disjoint example.

# Contributing

OS-ICL Bench accepts bug fixes, new deterministic cases, evaluator tests, and
accessibility improvements. Every case change must preserve the benchmark's
privacy boundary and be accompanied by tests.

## Development checks

1. Create or update the `data_mining` environment from `environment.yml`.
2. Run `./test.sh`.
3. Run `python scripts/validate_release.py --manifest <manifest>` for release data.
4. Verify the interface at a fixed 1280×720 viewport without DOM or accessibility
   access available to the tested model.

New policies must have three distinct rule signatures, deterministic generation,
visible decision attributes, explicit tie-breaking, and at least one counterfactual
seed test. Never expose `rule`, `rule_text`, or `expected` in evaluation responses.

Generated episodes and videos must not be committed directly. Publish release
artifacts separately and commit only their checksummed manifest.

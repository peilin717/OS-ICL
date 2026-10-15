# Contributing

OS-ICL Bench accepts bug fixes, new deterministic cases, evaluator tests, and
accessibility improvements. Every case change must preserve the benchmark's
privacy boundary and be accompanied by tests.

## Development checks

1. Create/update and activate the `data_mining` environment from `environment.yml`.
2. Run `./test.sh`.
3. For v2, run `python scripts/validate_v2_release.py --root <release-directory>`.
   `scripts/validate_release.py` is for historical v1 manifests only.
4. Verify the interface at a fixed 1280×720 viewport without DOM or accessibility
   access available to the tested model.

For v2, follow `docs/V2_ACCEPTANCE.md` and `docs/V2_TASK_DESIGN.md`: three coherent
operating procedures must yield distinct valid outputs for an identical query,
with real dependencies, meaningful long-horizon actions and recoverable errors.
Do not add arbitrary symbol puzzles to inflate difficulty. Include deterministic
generation, equivalent-plan tests, negative/counterfactual controls, UI checks
and version-bound video provenance. Never expose policies, references or scoring
predicates to visual agents. Historical v1 rules remain in their namespace.

Linux/WSL with Python 3.10 is the currently verified server/recording environment.
Browser audits require Playwright 1.63.0, Google Chrome at `/usr/bin/google-chrome`
and `ffmpeg`/`ffprobe` on PATH. Engine tests need pytest but no browser or model
API. `OS_ICL_PYTHON` can select an interpreter; `CONDA_BIN` is an optional explicit
compatibility path, not a required personal installation location.

Generated episodes and videos must not be committed directly. Publish release
artifacts separately and commit only their checksummed manifest.

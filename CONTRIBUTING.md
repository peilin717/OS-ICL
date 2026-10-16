# Contributing

OS-ICL Bench accepts bug fixes, new deterministic cases, evaluator tests, and
accessibility improvements. Every case change must preserve the benchmark's
privacy boundary and be accompanied by tests.

## Development checks

1. Create/update and activate the `data_mining` environment from `environment.yml`.
2. Run `./test.sh`.
3. Follow `docs/DIFFICULTY_STANDARD.md` and `docs/V2_ACCEPTANCE.md` for task design, privacy and validation.
4. Verify browser interaction at 1280×720. Evaluated models use screenshots and mouse/keyboard; trusted references and DOM access stay outside their tools.

Include deterministic generation, equivalent-plan tests, negative/counterfactual controls and source-bound video provenance for task changes. The catalogue contains 36 independent task families; each task/condition has one demonstration video.

Linux/WSL with Python 3.10 is the currently verified server/recording environment.
Browser audits require Playwright 1.63.0, Google Chrome at `/usr/bin/google-chrome`
and `ffmpeg`/`ffprobe` on PATH. Engine tests need pytest but no browser or model
API. `OS_ICL_PYTHON` can select an interpreter; `CONDA_BIN` is an optional explicit
compatibility path, not a required personal installation location.

Generated episodes and videos must not be committed directly. Publish release
artifacts separately and commit only their checksummed manifest.

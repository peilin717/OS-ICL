#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_BIN="${CONDA_BIN:-/root/miniconda3/bin/conda}"

exec "$CONDA_BIN" run --no-capture-output -n data_mining \
  python -m pytest -q "$ROOT_DIR/tests"

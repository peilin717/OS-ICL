#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_BIN="${CONDA_BIN:-/root/miniconda3/bin/conda}"

if [[ ! -x "$CONDA_BIN" ]]; then
  echo "Conda was not found at $CONDA_BIN" >&2
  exit 1
fi

exec "$CONDA_BIN" run --no-capture-output -n data_mining \
  python "$ROOT_DIR/server.py" "$@"

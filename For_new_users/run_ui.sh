#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -n "${QOL_PYTHON:-}" ]]; then
  PYTHON="$QOL_PYTHON"
elif [[ -x "$SCRIPT_DIR/../.venv/bin/python" ]]; then
  PYTHON="$SCRIPT_DIR/../.venv/bin/python"
elif [[ -x /opt/anaconda3/bin/python ]]; then
  PYTHON=/opt/anaconda3/bin/python
else
  PYTHON=python3
fi
exec "$PYTHON" "$SCRIPT_DIR/launch.py"

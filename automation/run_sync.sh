#!/bin/bash
# Wrapper used by launchd. Loads env from automation/.env if present.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$HERE/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$HERE/.env"
  set +a
fi

exec "${PYTHON_BIN:-python3}" "$HERE/sync_scroll_mile.py"

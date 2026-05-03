#!/bin/bash
# Wrapper used by launchd. Loads env from automation/.env if present.
set -euo pipefail

# launchd has a minimal PATH; prefer the framework Python where Playwright is usually installed.
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
DEFAULT_PY="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
if [ ! -x "$DEFAULT_PY" ]; then
  DEFAULT_PY="$(command -v python3 || true)"
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$HERE/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$HERE/.env"
  set +a
fi

PY="${PYTHON_BIN:-$DEFAULT_PY}"
exec "$PY" "$HERE/sync_scroll_mile.py"

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

# Playwright cannot use the real ~/Library/.../Google/Chrome dir (Chrome blocks it with
# remote debugging). Optionally copy Scroll Mile storage from your real Default profile
# into USER_DATA_DIR before launch. Requires Chrome fully quit so files are consistent.
if [ "${MIRROR_SCROLL_MILE_FROM_CHROME:-0}" = "1" ]; then
  if pgrep -x "Google Chrome" >/dev/null 2>&1; then
    echo "Quit Google Chrome completely, then run this script again (mirroring needs the profile files idle)." >&2
    exit 5
  fi
  SRC_ROOT="${CHROME_USER_DATA_FOR_MIRROR:-$HOME/Library/Application Support/Google/Chrome}/Default"
  DST_ROOT="${USER_DATA_DIR:?USER_DATA_DIR must be set}/Default"
  EXT_ID="${EXTENSION_ID_FOR_MIRROR:-kdeibhcngffpofgiaglnbhfpiocffihh}"
  mkdir -p "$DST_ROOT/Extensions" "$DST_ROOT/IndexedDB" "$DST_ROOT/Local Extension Settings"
  for rel in \
    "Extensions/${EXT_ID}" \
    "IndexedDB/chrome-extension_${EXT_ID}_0.indexeddb.leveldb" \
    "Local Extension Settings/${EXT_ID}"; do
    if [ -e "$SRC_ROOT/$rel" ]; then
      mkdir -p "$(dirname "$DST_ROOT/$rel")"
      rsync -a --delete "$SRC_ROOT/$rel/" "$DST_ROOT/$rel/"
    fi
  done
fi

PY="${PYTHON_BIN:-$DEFAULT_PY}"
exec "$PY" "$HERE/sync_scroll_mile.py"

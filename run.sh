#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

REQ_SIG="$(cksum requirements.txt)"
STAMP_FILE=".venv/.requirements.cksum"

if [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE")" != "$REQ_SIG" ]; then
  python -m pip install --upgrade pip --quiet
  python -m pip install -r requirements.txt --quiet
  printf '%s' "$REQ_SIG" > "$STAMP_FILE"
fi

exec python -m vrchat_clipper

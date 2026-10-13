#!/usr/bin/env bash
# End-to-end smoke run over the local photo archive.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"

# Never touch the real database: run against a throwaway copy so a smoke run
# cannot overwrite the owner's recommendations or profile.
SMOKE_DIR="$(mktemp -d)"
trap 'rm -rf "$SMOKE_DIR"' EXIT
if [ -f data/wanderlens.sqlite3 ]; then
  cp data/wanderlens.sqlite3 "$SMOKE_DIR/wl.sqlite3"
fi
export WANDERLENS_DB="$SMOKE_DIR/wl.sqlite3"
# Ignore any local config.yaml so the smoke run stays hermetic (no API key/calls).
export WANDERLENS_CONFIG="$SMOKE_DIR/none.yaml"

echo "== ingest =="
$PY -m wanderlens ingest

echo "== profile show =="
$PY -m wanderlens profile show | tee /tmp/wl_profile.txt
grep -q "Taste Profile" /tmp/wl_profile.txt
grep -q "Visited geography" /tmp/wl_profile.txt

echo "== recommend =="
$PY -m wanderlens recommend --count 3 | tee /tmp/wl_rec.txt
grep -qE '^[0-9]+\.' /tmp/wl_rec.txt

echo "== eval =="
$PY -m wanderlens eval | tee /tmp/wl_eval.txt

echo "smoke OK"

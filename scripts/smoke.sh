#!/usr/bin/env bash
# End-to-end smoke run over the local photo archive.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"

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

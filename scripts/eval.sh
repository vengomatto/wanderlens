#!/usr/bin/env bash
# Leave-one-trip-out evaluation with a regression gate against docs/eval-baseline.json.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"
BASE_FILE="docs/eval-baseline.json"

OUT="$($PY -m wanderlens eval --loto)"
echo "$OUT"

if [ ! -f "$BASE_FILE" ]; then
  echo "No baseline at $BASE_FILE; writing one."
  "$PY" - "$OUT" "$BASE_FILE" <<'PY'
import json, sys, ast
metrics = ast.literal_eval(sys.argv[1])
metrics["margin"] = 0.05
with open(sys.argv[2], "w") as fh:
    json.dump(metrics, fh, indent=2)
PY
  exit 0
fi

"$PY" - "$OUT" "$BASE_FILE" <<'PY'
import ast, json, sys
from wanderlens.core.evaluate import check_regression

metrics = ast.literal_eval(sys.argv[1])
baseline = json.load(open(sys.argv[2]))
margin = baseline.get("margin", 0.05)
print(f"MRR {metrics['mrr']} vs baseline {baseline.get('mrr')} (margin {margin})")
if not check_regression(metrics["mrr"], baseline.get("mrr", 0.0), margin):
    print("REGRESSION: MRR dropped beyond the margin", file=sys.stderr)
    sys.exit(1)
print("eval OK")
PY

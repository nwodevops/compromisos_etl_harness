#!/usr/bin/env bash
# Copia environments/<env>.json -> project-config.json (estructura Hop).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
ENV="${1:-local}"
SRC="$ROOT/environments/${ENV}.json"
DST="$ROOT/project-config.json"
if [[ ! -f "$SRC" ]]; then
  echo "No existe: $SRC" >&2
  exit 1
fi
python3 - "$SRC" "$DST" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
data = json.load(open(src, encoding="utf-8"))
vars_ = data.get("variables") or data.get("config", {}).get("variables") or []
out = {
    "metadataBaseFolder": "${PROJECT_HOME}/metadata",
    "unitTestsBasePath": "${PROJECT_HOME}",
    "dataSetsCsvFolder": "${PROJECT_HOME}/datasets",
    "enforcingExecutionInHome": True,
    "parentProjectName": "default",
    "config": {"variables": vars_},
}
json.dump(out, open(dst, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"OK: {src} -> {dst}")
PY

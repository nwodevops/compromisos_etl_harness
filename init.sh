#!/usr/bin/env bash
# Harness — smoke demo del arquetipo (H2 + Python, sin staging externo).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

fail() { echo -e "${RED}FAIL:${NC} $*" >&2; exit 1; }
warn() { echo -e "${YELLOW}AVISO:${NC} $*"; }
step() { echo -e "${GREEN}==>${NC} $*"; }

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

step "Validando feature_list.json"
"$PY" - <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path("feature_list.json").read_text(encoding="utf-8"))
active = [f for f in data.get("features", []) if f.get("status") == "in_progress"]
if len(active) > 1:
    sys.exit(f"más de una in_progress: {', '.join(f['id'] for f in active)}")
print(f"features: {len(data.get('features', []))}, in_progress: {len(active)}")
PY

step "Prerrequisitos"
command -v java >/dev/null 2>&1 || fail "java no está en PATH"
[ -f h2/lib/h2-2.4.240.jar ] || fail "jar H2 no encontrado"
if [ ! -x .venv/bin/python ]; then
  fail "venv ausente o roto. Desde el repo padre: ./scripts/nuevo_etl.sh lo crea. A mano: python3 -m venv .venv && .venv/bin/python -m pip install -r python/requirements.txt"
fi
"$PY" -c "import yaml, pandas, jaydebeapi" 2>/dev/null \
  || fail "el .venv no tiene dependencias (¿venv sin pip?). .venv/bin/python -m pip install -r python/requirements.txt"
if [ ! -f project-config.json ]; then
  step "Generando project-config.json (switch-env local)"
  ./switch-env.sh local
fi

step "Reset H2 + DDL"
./h2/scripts/reset_and_create.sh

step "Python create STG"
"$PY" python/create_stg.py

step "Python main (demo)"
set +e
"$PY" python/main.py 2>&1 | tee "$LOG"
MAIN_RC=${PIPESTATUS[0]}
set -e
[ "$MAIN_RC" -eq 0 ] || fail "python/main.py terminó con código $MAIN_RC"

step "Comprobando salidas"
grep -q "Salida RESULTADO" "$LOG" || fail "no hay Salida RESULTADO en el log"
grep -q "Excel:" "$LOG" || warn "no se escribió Excel (opcional si falla openpyxl)"
if grep -q '\${[A-Za-z0-9_]\+}' "$LOG"; then
  fail "log contiene variables Hop sin resolver"
fi

echo ""
echo -e "${GREEN}HARNESS OK${NC} — ver CHECKPOINTS.md"
exit 0

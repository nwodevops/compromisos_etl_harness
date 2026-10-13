#!/usr/bin/env bash
# Reconstruye la rama release desde HEAD de master: solo el ETL.
# Esta skill y este script no viajan a release (.agents/ se borra).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" != "master" && "$branch" != "main" ]]; then
  echo "Hay que estar en master o main (ahora: $branch)" >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "El árbol de master tiene cambios sin commit. Commitéalos antes de cortar release." >&2
  exit 1
fi

WT="$(mktemp -d)"
cleanup() { git worktree remove --force "$WT" >/dev/null 2>&1 || true; }
trap cleanup EXIT

git worktree add --detach "$WT" HEAD
cd "$WT"

git rm -rf --ignore-unmatch \
  feature_list.json \
  CHECKPOINTS.md \
  progress \
  docs/harness \
  docs/verification.md \
  AGENTS.md \
  .agents \
  ESTRUCTURA.md \
  input/notas.txt \
  python/plantilla_logica.py \
  pipelines/pl_demo.hpl

python3 - <<'PY'
from pathlib import Path

sh = Path("init.sh")
text = sh.read_text(encoding="utf-8")
start = text.find('step "Validando feature_list.json"\n')
end = text.find('step "Prerrequisitos"\n')
if start < 0 or end < 0 or end <= start:
    raise SystemExit("init.sh: no encontré el bloque de feature_list")
sh.write_text(text[:start] + text[end:], encoding="utf-8")

bat = Path("init.bat")
text = bat.read_text(encoding="utf-8")
start = text.find("echo ==^> Validando feature_list.json\r\n")
if start < 0:
    start = text.find("echo ==^> Validando feature_list.json\n")
end = text.find("echo ==^> Prerrequisitos\r\n")
if end < 0:
    end = text.find("echo ==^> Prerrequisitos\n")
if start < 0:
    start = text.find("call :step Validando feature_list.json\r\n")
if start < 0:
    start = text.find("call :step Validando feature_list.json\n")
if end < 0:
    end = text.find("call :step Prerrequisitos\r\n")
if end < 0:
    end = text.find("call :step Prerrequisitos\n")
if start < 0 or end < 0 or end <= start:
    raise SystemExit("init.bat: no encontré el bloque de feature_list")
bat.write_text(text[:start] + text[end:], encoding="utf-8")
PY

git add -u init.sh init.bat
tree="$(git write-tree)"
commit="$(git commit-tree "$tree" -m "$(cat <<'EOF'
Corte release: solo el ETL.

Sin arnés, agente ni skills. init.sh e init.bat no leen feature_list.json.
EOF
)")"

cd "$ROOT"
git update-ref refs/heads/release "$commit"
echo "release -> $commit"
git ls-tree -r --name-only release

#!/usr/bin/env bash
# Genera un cascarón Hop + H2 + Python. No copia acuerdos, secretos ni la carga.
# Uso: ./scripts/nuevo_etl.sh /ruta/mi_etl --input excel|oracle|sheets
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST=""
INPUT=""

usage() {
  echo "Uso: ./scripts/nuevo_etl.sh /ruta/mi_etl --input excel|oracle|sheets" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --input)
      INPUT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [ -n "$DEST" ]; then
        usage
      fi
      DEST="$1"
      shift
      ;;
  esac
done

[ -n "$DEST" ] && [ -n "$INPUT" ] || usage
case "$INPUT" in
  excel|oracle|sheets) ;;
  *) echo "FAIL: --input debe ser excel, oracle o sheets" >&2; exit 2 ;;
esac

DEST="$(mkdir -p "$DEST" && cd "$DEST" && pwd)"
if [ -n "$(find "$DEST" -mindepth 1 -print -quit)" ]; then
  echo "FAIL: $DEST ya existe y no está vacío" >&2
  exit 1
fi

NAME="$(basename "$DEST")"

copy_rel() {
  local rel="$1"
  mkdir -p "$DEST/$(dirname "$rel")"
  cp -a "$ROOT/$rel" "$DEST/$rel"
}

ARCHIVOS=(
  .gitignore
  AGENTS.md
  init.sh
  init.bat
  switch-env.sh
  switch-env.ps1
  run_wf_main.bat
  docs/arquitectura.md
  docs/harness/platform.md
  docs/harness/workflow.md
  .agents/skills/hop-python-etl/SKILL.md
  .agents/skills/hop-python-etl/reference.md
  .agents/skills/hop-python-etl/inputs.example.yaml
  h2/sql/00_reset.sql
  h2/sql/01_schema.sql
  h2/lib/h2-2.4.240.jar
  metadata/pipeline-run-configuration/local.json
  metadata/workflow-run-configuration/local.json
  metadata/rdbms/h2.json
  metadata/rdbms/mysql_dw.json
  metadata/rdbms/oracle_dw.json
  metadata/rdbms/oracle_repocsep.json
  metadata/rdbms/oracle_sisud.json
  workflows/wf_main.hwf
  workflows/wf_create_stg.hwf
  workflows/wf_main_windows.hwf
  pipelines/pl_demo.hpl
  python/create_stg.py
  python/config.py
  python/h2_conn.py
  python/main.py
  python/plantilla_logica.py
  python/requirements.txt
  python/introspect/__init__.py
  python/introspect/excel.py
  python/introspect/h2_ddl.py
  python/introspect/oracle.py
  python/introspect/sheets.py
  python/io/escribir_excel.py
  python/io/leer_h2.py
  scripts/tee_step.sh
  scripts/control_datos.py
  input/input_excel/README.md
  logica/LEEME.md
)

for rel in "${ARCHIVOS[@]}"; do
  copy_rel "$rel"
done

for script in "$ROOT"/h2/scripts/*; do
  base="$(basename "$script")"
  case "$base" in
    *.log) continue ;;
  esac
  copy_rel "h2/scripts/$base"
done

mkdir -p "$DEST/environments"
cp -a "$ROOT/environments/remote.json" "$DEST/environments/remote.json"
cp -a "$ROOT/environments/remote.json" "$DEST/environments/local.json"
mkdir -p "$DEST/log" "$DEST/progress" "$DEST/output"
: > "$DEST/log/.gitkeep"
cp -a "$ROOT/python/plantilla_logica.py" "$DEST/logica/demo.py"

python3 - "$DEST" "$NAME" "$INPUT" <<'PY'
import json
import sys
from pathlib import Path

dest, name, kind = Path(sys.argv[1]), sys.argv[2], sys.argv[3]

def write(rel, text):
    path = dest / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

inputs = {
    "excel": """# Fuente Excel. create_stg.py crea el DDL; Hop extrae las filas.
sources:
  - stg_table: STG_XLS_EJEMPLO
    type: excel
    path: input/input_excel/ejemplo.xlsx
    worksheet: "Datos"
    header_row: 1
    types: varchar
""",
    "oracle": """# Fuente Oracle. create_stg.py crea el DDL; Hop extrae las filas.
sources:
  - stg_table: STG_ORA_EJEMPLO
    type: oracle
    connection: oracle_sisud
    object: OWNER.VW_EJEMPLO
""",
    "sheets": """# Una hoja de Google Sheets. Sin catálogo de varios libros.
sources:
  - stg_table: STG_GS1_EJEMPLO
    type: sheets
    spreadsheet_key: ${SPREADSHEET_KEY_GS1}
    worksheet: "Hoja 1"
    types: varchar
""",
}
write("inputs.yaml", inputs[kind])

feature = {
    "project": name,
    "reglas": {
        "una_feature_activa": "Como máximo un item con status in_progress",
        "verificacion": "./init.sh debe terminar en HARNESS OK",
        "trazabilidad": "Implementador escribe progress/impl_<id>.md",
    },
    "features": [
        {
            "id": "fase-1-entorno",
            "title": "Hop + H2 + Python + harness",
            "status": "pending",
            "criterio": "CHECKPOINTS.md#fase-1",
            "doc": "README.md",
        },
        {
            "id": "fase-2-fuentes-stg",
            "title": "inputs.yaml + pl_stage_* en Hop",
            "status": "pending",
            "criterio": "CHECKPOINTS.md#fase-2",
            "doc": ".agents/skills/hop-python-etl/inputs.example.yaml",
        },
        {
            "id": "fase-3-logica",
            "title": "logica/ + salida Excel",
            "status": "pending",
            "criterio": "CHECKPOINTS.md#fase-3",
            "doc": "python/CONTRATO.md",
        },
    ],
}
write("feature_list.json", json.dumps(feature, indent=2, ensure_ascii=False) + "\n")

write("progress/current.md", "# Sesión\n\nPendiente fase-1.\n")
write("progress/history.md", "# Historia\n")

write(
    "CHECKPOINTS.md",
    """# CHECKPOINTS — arquetipo

Verificación de humo: [`./init.sh`](init.sh) (`HARNESS OK`).
Verificación de datos: [`scripts/control_datos.py`](scripts/control_datos.py). No resetea H2.
`HARNESS OK` no cierra las fases 2 ni 3.

## Global

- [ ] `./init.sh` termina con **`HARNESS OK`**.
- [ ] Sin passwords reales en `project-config.json` / `environments/`.
- [ ] Log sin literales `${VAR}`.
- [ ] Un solo `.py` en `logica/`.
- [ ] Máximo **una** feature `in_progress`.

## Fase 1 — Entorno {#fase-1}

- [ ] H2 levanta en puerto 9092 (`reset_and_create.sh`).
- [ ] `python/create_stg.py` OK.
- [ ] `python/main.py` OK con `logica/demo.py`.
- [ ] `wf_main.hwf` ejecutable en Hop GUI.

## Fase 2 — Fuentes STG {#fase-2}

- [ ] Al menos una fuente en `inputs.yaml`.
- [ ] Tabla `STG_*` creada en H2.
- [ ] Pipeline `pl_stage_*.hpl` cableado en `wf_main.hwf` después de create STG.
- [ ] Hop carga filas en STG (conteo > 0 en log).
- [ ] `progress/impl_fase-2-fuentes-stg.md` trae conteos y libros o tablas que fallaron. `HARNESS OK` solo no cierra esta fase.

## Fase 3 — Lógica {#fase-3}

- [ ] Claves STG en `python/io/leer_h2.py`.
- [ ] `logica/<tu_logica>.py` produce `RESULTADO` con filas > 0.
- [ ] `output/resultado.xlsx` generado.
- [ ] `progress/impl_fase-3-logica.md` describe la salida.
- [ ] Si hay destino en dos bases, `scripts/control_datos.py` compara los conteos. Sin catálogo de Sheets termina en aviso y código 0.

Linux = entorno `local`. Windows = entorno `remote`.
""",
)

write(
    "docs/verification.md",
    """# Verificación

## Humo

```bash
./switch-env.sh local
INIT_FORCE=1 ./init.sh   # HARNESS OK. Borra mem:csep.
```

`./init.sh` sin `INIT_FORCE=1` no resetea si ya hay filas `STG_*`.

## Datos

```bash
.venv/bin/python scripts/control_datos.py
```

No resetea H2. Sin catálogo de Sheets imprime un aviso y termina en 0.

## Hop

Linux: `wf_main.hwf` con entorno `local`.
Windows: `wf_main_windows.hwf` con entorno `remote`.
El paso de stage del cascarón solo avisa: cablea ahí el `pl_stage_*` de la fuente.
""",
)

write(
    "python/CONTRATO.md",
    """# Contrato logica/

```
python/main.py
  → io/leer_h2.py
  → logica/*.py
  → io/escribir_excel.py
```

## Entrada

`LECTURAS` en `python/io/leer_h2.py`. El cascarón trae `DEMO` → `DEMO_TABLA_EJEMPLO`.
Al añadir una fuente, suma la clave de la tabla `STG_*`.

## Salida

Un DataFrame `RESULTADO`. `pandas` llega inyectado como `pd`.

## Reglas

- Un solo `.py` en `logica/`.
- Sin conexiones ni drivers en `logica/`.
""",
)

write(
    "python/LEEME.md",
    """# python/

| Capa | Entry | Hace |
|---|---|---|
| DDL | `create_stg.py` | `CREATE TABLE STG_*` desde `inputs.yaml` |
| Post-staging | `main.py` | Lee H2, corre `logica/`, escribe Excel |

`config.py` y `h2_conn.py` leen las variables Hop y abren H2.
`logica/` no abre conexiones.
""",
)

write(
    "ESTRUCTURA.md",
    f"""# Estructura — {name}

```
{name}/
├── inputs.yaml          # tipo de esta copia: {kind}
├── init.sh              # humo; no borra STG si ya hay filas
├── scripts/control_datos.py
├── python/create_stg.py
├── python/main.py
├── python/io/leer_h2.py # DEMO hasta que cablees la STG
├── logica/demo.py
├── workflows/wf_main.hwf
├── workflows/wf_main_windows.hwf
└── pipelines/pl_demo.hpl
```

Linux: `./switch-env.sh local`. Windows: `.\\switch-env.ps1 remote`.
H2 es `mem:csep` en el puerto 9092. No lo compartas con otra corrida: el reset hace `DROP ALL OBJECTS`.
""",
)

write(
    "README.md",
    f"""# {name}

Cascarón Hop + H2 + Python. Entrada de esta copia: **{kind}**.

```bash
./switch-env.sh local          # Linux
./init.sh                      # humo; INIT_FORCE=1 si hay que vaciar H2
.venv/bin/python scripts/control_datos.py
```

Windows: `.\\switch-env.ps1 remote` y `wf_main_windows.hwf`.

1. Completa `inputs.yaml` (ahora es un ejemplo {kind}).
2. Cablea `pl_stage_*.hpl` en `wf_main.hwf` en el paso de stage.
3. Apunta `python/io/leer_h2.py` a la `STG_*`.
4. Sustituye `logica/demo.py` por una sola lógica. Parte de `python/plantilla_logica.py`.

`environments/local.json` y `remote.json` traen placeholders. No guardes contraseñas en git.
""",
)

leer = (dest / "python/io/leer_h2.py").read_text(encoding="utf-8")
inicio = leer.index("LECTURAS:")
fin = leer.index("\n\n", inicio)
nuevo = (
    'LECTURAS: dict[str, str] = {\n'
    '    "DEMO": "SELECT * FROM PUBLIC.DEMO_TABLA_EJEMPLO",\n'
    "}"
)
(dest / "python/io/leer_h2.py").write_text(leer[:inicio] + nuevo + leer[fin:], encoding="utf-8")

for rel in ("workflows/wf_main.hwf", "workflows/wf_main_windows.hwf"):
    path = dest / rel
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        './scripts/tee_step.sh log/wf_main.log "$PY" python/stage/stage_sheets.py',
        'echo "AVISO: cablea pl_stage en Fase 2"',
    )
    text = text.replace(
        '"%PY%" python\\stage\\stage_sheets.py',
        'echo AVISO: cablea pl_stage en Fase 2',
    )
    text = text.replace("Excel + DW_ACU_*", "Excel")
    text = text.replace(
        "pl_stage_*.hpl vía python/stage/stage_sheets.py — 6 STG de acuerdos",
        "Cablea aquí el pl_stage de la fuente (Fase 2)",
    )
    text = text.replace(
        "Google Sheets → STG vía hop-run",
        "Stage de la fuente (Fase 2)",
    )
    text = text.replace("compromisos_etl_harness", name)
    path.write_text(text, encoding="utf-8")

for rel in (
    "AGENTS.md",
    "init.bat",
    "run_wf_main.bat",
    "docs/harness/platform.md",
):
    path = dest / rel
    path.write_text(
        path.read_text(encoding="utf-8").replace("compromisos_etl_harness", name),
        encoding="utf-8",
    )
PY

chmod +x "$DEST/init.sh" "$DEST/switch-env.sh" "$DEST/scripts/"*.sh "$DEST/h2/scripts/"*.sh

if ! "$DEST/.venv/bin/python" -c "import pip" >/dev/null 2>&1; then
  rm -rf "$DEST/.venv"
  if ! python3 -m venv "$DEST/.venv" >/dev/null 2>&1; then
    python3 -m venv --without-pip "$DEST/.venv"
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | "$DEST/.venv/bin/python"
  fi
  "$DEST/.venv/bin/python" -m pip install -q -r "$DEST/python/requirements.txt"
fi

echo "OK: $DEST (--input $INPUT)"
echo "Linux: cd $DEST && ./switch-env.sh local"
echo "No corras ./init.sh si otro ETL usa el H2 mem:csep de este puerto."

# Arquetipo Apache Hop + H2 in-memory + Python

Cascarón **mínimo** para un ETL nuevo. Sin fuentes ni lógica de negocio: demo `DEMO_TABLA_EJEMPLO` → Excel.

Desde el repo padre:

```bash
./scripts/nuevo_etl.sh ~/workspace/mi_etl
cd ~/workspace/mi_etl
```

O regenerar y copiar a mano:

```bash
./scripts/sync_archetype.sh
cp -r archetype/ ~/workspace/mi_etl/
```

## Bootstrap

`nuevo_etl.sh` crea el `.venv` con pip. Si copiás `archetype/` a mano en Ubuntu sin `python3-venv`:

```bash
# usar python3-venv (ensurepip) O el helper del repo padre:
#   ./scripts/nuevo_etl.sh ~/workspace/mi_etl
# A mano en Ubuntu sin ensurepip:
python3 -m venv --without-pip .venv
# después: copiar pip del .venv del repo multa, o get-pip.py, y:
.venv/bin/python -m pip install -r python/requirements.txt
chmod +x init.sh switch-env.sh h2/scripts/*.sh
./switch-env.sh local
./init.sh
```

## Qué trae

- **H2** in-memory `mem:csep` (reset cada corrida)
- **Hop:** `wf_create_stg.hwf` (diseño STG), `wf_main.hwf` (demo)
- **Python:** `create_stg.py` (DDL), `main.py` + `logica/demo.py` → `output/resultado.xlsx`
- **Harness:** `feature_list.json`, `CHECKPOINTS.md`, `init.sh`, `progress/`
- **Skill:** `.agents/skills/hop-python-etl/`

No incluye `logica/dwh/`, `cargar_dw.py` ni planillas OEFA. Eso se copia después si el proyecto es un DW.

## Cómo extender (otros inputs, otra lógica)

| Paso | Dónde |
|---|---|
| 1. Fuentes | `inputs.yaml` (ver `.agents/skills/hop-python-etl/inputs.example.yaml`) |
| 2. Staging Hop | `wf_create_stg.hwf` → `pipelines/pl_stage_*.hpl` → cablear en `wf_main.hwf` **después** de create STG |
| 3. Lecturas | claves en `python/io/leer_h2.py` (`LECTURAS`) |
| 4. Lógica | un solo `.py` en `logica/` (borrar `demo.py`; partir de `python/plantilla_logica.py`) |
| 5. Destino | por defecto Excel (`escribir_excel.py`). Oracle DW: copiar `cargar_dw.py` desde el repo multa |

Contrato: [`python/CONTRATO.md`](python/CONTRATO.md). Verificación: [`docs/verification.md`](docs/verification.md).

## Credenciales

`environments/local.json` / `remote.json` tienen placeholders `<HOST>`, `<PASSWORD>`.  
`./switch-env.sh local|remote` escribe `project-config.json` (gitignored).

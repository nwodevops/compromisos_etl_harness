# Sesión activa

| Campo | Valor |
|---|---|
| ID | *(ninguna — fase-1, fase-2 y fase-3 en `done`)* |
| Criterio | [`CHECKPOINTS.md`](../CHECKPOINTS.md) |

## Plan

Las tres features del plan 2 quedaron cerradas. La carga vive en `output/resultado.xlsx`. H2 in-memory se vacía con `./init.sh`; para volver a llenarlo:

```bash
./h2/scripts/reset_and_create.sh
.venv/bin/python python/create_stg.py
.venv/bin/python python/stage/stage_sheets.py
.venv/bin/python python/main.py
```

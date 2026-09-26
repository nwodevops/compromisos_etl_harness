---
name: hop-python-etl
description: >-
  Arquetipo Apache Hop + H2 in-memory STG_* + Python post-staging.
  inputs.yaml, create_stg.py, wf_create_stg/wf_main, logica/ aislada,
  project-config.json. Usar al clonar el cascarón, añadir fuentes STG,
  cablear workflows o depurar Hop/H2/Python.
---

# Hop + H2 + Python ETL

## Arquitectura (no mezclar capas)

```
Fuentes (Excel / Sheets / Oracle / lo que declare inputs.yaml)
  → inputs.yaml          (declara STG_*)
  → Python create_stg    (DDL H2; no extrae filas)
  → Hop extract          (TableInput → TableOutput H2, truncate)
  → H2 mem:csep          (landing efímero, reset cada corrida)
  → Python logica/       (un .py; reglas)
  → Destino demo         (Excel output/resultado.xlsx)
```

| Capa | Hace | No hace |
|---|---|---|
| `inputs.yaml` | Manifiesto de fuentes | Extraer filas |
| `python/create_stg.py` | Introspect + `CREATE TABLE STG_*` | Negocio |
| Hop | Extract → H2 | UNION multi-fuente ni KPIs |
| `logica/` | Negocio en memoria | Conexiones ni drivers |
| `python/io/` | Leer H2, escribir destino | Reglas de negocio |

**Contrato:** `python/CONTRATO.md`. **Staging:** [reference.md](reference.md).

## Cuándo Hop solo vs Python

- **Hop solo:** 1 fuente → 1 destino, mapeo 1:1.
- **Python:** homologación, calidad, joins, dimensional, indicadores.

Un solo `.py` en `logica/` (auto-descubierto por `python/main.py`). Entrada = claves de `LECTURAS` en `python/io/leer_h2.py`. Salida = DataFrame `RESULTADO`.

## Workflows

**Diseño** (`wf_create_stg.hwf`): Reset H2 → Python create STG → Success (H2 vivo en 9092 para mapear pipelines).

**Corrida** (`wf_main.hwf`): Reset H2 → create STG → `pl_stage_*` / `pl_demo` → Run Python → Success.

Smoke sin Hop:

```bash
./h2/scripts/reset_and_create.sh
.venv/bin/python python/create_stg.py
.venv/bin/python python/main.py
```

## Extender una fuente (checklist)

1. Entrada en `inputs.yaml` ([inputs.example.yaml](inputs.example.yaml)).
2. Play `wf_create_stg` → crear `pipelines/pl_stage_*.hpl`.
3. Cablear en `wf_main.hwf` **después** de Python create STG.
4. Clave en `python/io/leer_h2.py` → `LECTURAS`.
5. Lógica en `logica/` (no conexiones). Borrar `demo.py` al pasar a lógica real.
6. Actualizar `python/CONTRATO.md` y `AGENTS.md`.

## Variables y conexiones

Fuente única: `project-config.json` → `config.variables`. Entorno: `./switch-env.sh local|remote`.

- `DB_H2_*` — staging TCP `localhost:9092/mem:csep`
- `DB_ORA_*` — placeholders hasta que haya Oracle

`${VAR}` literal en log = variable no definida o proyecto Hop equivocado.

**Secretos:** no commitear passwords reales en `project-config.json` / `environments/`.

## Gotchas

| Síntoma | Causa |
|---|---|
| Workflow colgado en Reset H2 | `start_h2.sh` sin `nohup` + redirección al log |
| H2 vacío tras reinicio | in-memory se pierde al parar el server |
| `import io` falla | colisión con stdlib; cargar módulos por ruta en `main.py` |
| `#N/A` tumba pipeline | Sheets/Excel → VARCHAR en STG |
| Hop sobrescribe variables | `hop-conf.sh --project-create` sin `--project-keep-config-file` |

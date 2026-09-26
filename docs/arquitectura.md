# Arquitectura — arquetipo mínimo

ETL **Apache Hop + H2 in-memory + Python**. Demo: `DEMO_TABLA_EJEMPLO` → `logica/demo.py` → Excel.

## Vista general

```mermaid
flowchart TB
  subgraph fuentes [Fuentes opcionales]
    EX["Excel / Oracle / Sheets"]
  end

  YAML["inputs.yaml"]
  PYDDL["python/create_stg.py"]
  HOP["Apache Hop pl_stage_*"]
  H2["H2 mem:csep STG_* + DEMO"]
  PY["python/main.py + logica/"]
  OUT["output/resultado.xlsx"]

  EX --> YAML
  YAML --> PYDDL --> H2
  EX --> HOP --> H2
  H2 --> PY --> OUT
```

| Capa | Responsabilidad |
|---|---|
| `inputs.yaml` | Declara fuentes → tablas `STG_*` |
| `create_stg.py` | DDL H2 (sin filas) |
| Hop | Extract → H2 |
| `logica/` | Reglas de negocio (un `.py`) |
| H2 | Staging efímero (reset cada corrida) |

## Workflows

| Workflow | Uso |
|---|---|
| `wf_create_stg.hwf` | Diseño: deja H2 vivo para mapear pipelines |
| `wf_main.hwf` | Corrida demo: Reset → STG → pl_demo → Python |

## Extender

Ver [`README.md`](../README.md) y skill [`.agents/skills/hop-python-etl/`](../.agents/skills/hop-python-etl/SKILL.md).

Para un DW Oracle (dims/facts): copiar `cargar_dw.py` y, si aplica, `logica/dwh/` desde el repo de referencia (multa).

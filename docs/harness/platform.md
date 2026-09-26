# Plataforma y ejecución (cascarón)

Divulgación progresiva desde [`AGENTS.md`](../../AGENTS.md).

## Linux

- Apache Hop en `~/apps/hop` (GUI: `~/apps/hop/hop-gui.sh`).
- Java en PATH (H2).
- Python: `.venv/` + `python/requirements.txt`.

## Workflows

| Workflow | Uso |
|---|---|
| `workflows/wf_create_stg.hwf` | Diseño: Reset H2 → Python STG → H2 vivo en 9092 |
| `workflows/wf_main.hwf` | Corrida: Reset → STG → `pl_demo` → Python |

Smoke sin Hop:

```bash
./switch-env.sh local
./h2/scripts/reset_and_create.sh && .venv/bin/python python/create_stg.py && .venv/bin/python python/main.py
```

## Capa de lógica

- Un solo `.py` en `logica/` (demo: `demo.py`).
- Entrada: DataFrames `LECTURAS` (`python/io/leer_h2.py`).
- Contrato: [`python/CONTRATO.md`](../../python/CONTRATO.md).

## H2

- BD in-memory `mem:csep`, TCP `9092`, modo Oracle.
- Reset: `h2/scripts/reset_and_create.sh` → `00_reset.sql` + `01_schema.sql`.
- **Gotcha:** `start_h2.sh` debe usar `nohup` y redirigir stdout; si no, Hop se queda colgado en Reset.

## Variables

- Fuente única: `project-config.json` → `config.variables`.
- Entorno: `./switch-env.sh local|remote` (copia `environments/*.json`).
- `${VAR}` literal en log = variable no definida o proyecto Hop equivocado.

## Secretos

No commitear `project-config.json` ni `client_secret.json`. En `environments/` solo placeholders `<...>`.

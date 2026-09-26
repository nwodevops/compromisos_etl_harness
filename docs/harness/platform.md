# Plataforma y ejecución (cascarón)

Divulgación progresiva desde [`AGENTS.md`](../../AGENTS.md).

## Linux

- Apache Hop en `~/apps/hop` (GUI: `~/apps/hop/hop-gui.sh`).
- Java en PATH (H2).
- Python: `.venv/` + `python/requirements.txt`.

## Windows

Misma máquina y el mismo `hop-run.bat` que `etl_informes_harness` (`D:\Eder\hop` o `%USERPROFILE%\apps\hop`). El repo va al lado, no dentro del de informes. Registrar el proyecto Hop `compromisos_etl_harness`.

```powershell
.\switch-env.ps1 remote
.\init.bat
# Programador de tareas → run_wf_main.bat   (no cambia el entorno; log en logs\wf_main_YYYYMMDD.log)
# Hop GUI → wf_main_windows.hwf
```

`init.bat [local|remote]` aplica `switch-env.ps1` en cada arranque (default `remote`). `--runconfig=local` es el motor de Hop, no el entorno de datos.

H2 compartido: puerto `9092`, base `mem:csep`, tarea `H2_SERVICE_MEM_CSEP`. Si el puerto ya escucha, no se levanta otro server. No solapar la corrida con informes.

## Workflows

| Workflow | Uso |
|---|---|
| `workflows/wf_create_stg.hwf` | Diseño (Linux): Reset H2 → Python STG → H2 vivo en 9092 |
| `workflows/wf_main.hwf` | Corrida Linux: Reset → STG → Sheets → Python |
| `workflows/wf_main_windows.hwf` | Corrida Windows (`cmd`): los mismos cuatro pasos |

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
- Entorno: `./switch-env.sh local|remote` o `.\switch-env.ps1 local|remote`. Si la plantilla trae `<...>`, el `.ps1` conserva el valor real ya escrito en `project-config.json`.
- `${VAR}` literal en log = variable no definida o proyecto Hop equivocado.

## Secretos

No commitear `project-config.json` ni `client_secret.json`. En `environments/` solo placeholders `<...>`.

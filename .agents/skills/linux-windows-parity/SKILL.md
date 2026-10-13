---
name: linux-windows-parity
description: >-
  Mantiene en paralelo la corrida Linux (desarrollo, entorno local) y la
  corrida Windows (entorno remote) de un ETL del arquetipo. Usar al cambiar
  init.sh, init.bat, run_wf_main.bat, wf_main.hwf, wf_main_windows.hwf,
  switch-env, un paso SHELL, el esquema Oracle, inputs.yaml o logica/; al
  portar a Windows; o cuando el usuario menciona Ubuntu, Windows, remote,
  init.bat, Programador de tareas, run_wf_main o HARNESS OK.
---

# Paridad Linux / Windows

Linux desarrolla. Windows ejecuta lo mismo contra otro Oracle. Un solo Python de negocio. Dos orquestadores.

| | Linux (este Ubuntu) | Windows (el otro agente) |
|---|---|---|
| Rol | desarrollo | corrida |
| Entorno | `local` | `remote` (default de `init.bat`) |
| Oracle y esquema | `environments/local.json` | `environments/remote.json` |
| Verificación | `./init.sh` → `HARNESS OK` | `init.bat remote` → `HARNESS OK` |
| Hop | `~/apps/hop`, `workflows/wf_main.hwf` | `D:\Eder\hop`, `workflows/wf_main_windows.hwf` |
| Config | `./switch-env.sh local` | `switch-env.ps1 remote` |

Credenciales solo en `docs/credenciales/<env>.txt` (gitignored). `switch-env.sh` y `switch-env.ps1` las sobreponen en `project-config.json`. No hardcodear host, password ni esquema.

## Al cambiar la corrida en Linux

El paso nuevo o modificado entra en los tres sitios Windows. La definición del comando vive una sola vez, en `scripts/step_<nombre>.bat`. `init.bat` y el SHELL de `wf_main_windows.hwf` llaman a ese `.bat`. No copies el `python …` dentro del `.hwf` ni lo dupliques en `init.bat`.

El cascarón trae tres pasos. Cada paso nuevo de `init.sh` gana su `scripts/step_<nombre>.bat`; no dejes el comando solo en el workflow.

1. `scripts/step_reset_h2.bat` → `h2/scripts/reset_and_create.bat`
2. `scripts/step_create_stg.bat` → `python/create_stg.py`
3. `scripts/step_main.bat` → `python/main.py`

Si `init.sh` gana un grep de conteo, `init.bat` gana el mismo grep. El log de ambos debe poder decir `HARNESS OK` con las mismas tablas. Los dos escriben en `logs/` (skill `etl-run-logs`). Un temporal que se borra al salir no cuenta.

## Programador de tareas: `run_wf_main.bat`

Al dejar el espejo Windows, crea `run_wf_main.bat` en la raíz si no existe. Es lo que se declara en el Programador de tareas. No lleva los pasos del ETL: solo lanza `workflows\wf_main_windows.hwf`. Los pasos siguen en `scripts\step_*.bat`, llamados por `init.bat` y por el workflow.

No edites `datawarehouse_multa_etl/run_wf_main.bat` ni `etl_informes_harness/run_wf_main.bat`. Esos dos están probados. Multa es la excepción: proyecto Hop `multa_informes_etl`, workflow `wf_main_win.hwf`, y llama `start_h2_svc.bat` antes de Hop. Un ETL nuevo no copia esa excepción.

Para el arquetipo:

- El proyecto Hop (`--project`) es el nombre de la carpeta del repo.
- El workflow es `workflows\wf_main_windows.hwf`.
- No llama a `switch-env`. Usa el `project-config.json` que ya dejó `switch-env.ps1 remote`.
- `--runconfig=local` es el motor de Hop, no el entorno de datos.
- No levanta H2. El primer paso del workflow (`step_reset_h2.bat` → `reset_and_create.bat`) comprueba el puerto `9092`. La base `mem:csep` y la tarea `H2_SERVICE_MEM_CSEP` se comparten; no solapar corridas.
- `cd /d "%~dp0"` para que el Programador pueda arrancar desde la carpeta padre. Directorio de inicio de la tarea: la carpeta del repo.
- Log: `logs\wf_main_YYYYMMDD.log`. Si ese archivo ya existe, se borra y se reescribe. No se borra al salir. `*.log` está en `.gitignore`.

Sustituye solo `<CARPETA>` por el nombre de la carpeta:

```bat
@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM Corrida headless de wf_main_windows (Programador de tareas Windows).
REM Override: set HOP_RUN=D:\ruta\a\hop\hop-run.bat

REM --- Log por fecha ---
set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "STAMP=%%a"
set "LOGFILE=%LOGDIR%\wf_main_%STAMP%.log"
if exist "%LOGFILE%" del "%LOGFILE%" >nul 2>&1

call :log Inicio: %date% %time%

REM Resolver hop-run.bat: override HOP_RUN > HOP_HOME > D:\Eder\hop > %USERPROFILE%\apps\hop > PATH
if not defined HOP_RUN (
  if defined HOP_HOME if exist "%HOP_HOME%\hop-run.bat" (
    set "HOP_RUN=%HOP_HOME%\hop-run.bat"
  ) else if exist "D:\Eder\hop\hop-run.bat" (
    set "HOP_RUN=D:\Eder\hop\hop-run.bat"
  ) else if exist "%USERPROFILE%\apps\hop\hop-run.bat" (
    set "HOP_RUN=%USERPROFILE%\apps\hop\hop-run.bat"
  ) else if exist "%USERPROFILE%\apps\hop\hop-run.cmd" (
    set "HOP_RUN=%USERPROFILE%\apps\hop\hop-run.cmd"
  ) else (
    set "HOP_RUN=hop-run"
  )
)

set "PROJECT_HOME=%CD%"
set "PROJECT_NAME=<CARPETA>"
set "WF=%PROJECT_HOME%\workflows\wf_main_windows.hwf"

call :log HOP_RUN=%HOP_RUN%
call :log PROJECT_HOME=%PROJECT_HOME%
call :log Ejecutando %WF%

if /I "%HOP_RUN%"=="hop-run" (
  where hop-run >nul 2>&1
  if errorlevel 1 (
    call :log ERROR: No se encuentra hop-run en PATH. Define HOP_RUN.
    exit /b 1
  )
) else if not exist "%HOP_RUN%" (
  call :log ERROR: No se encuentra %HOP_RUN%. Define HOP_RUN o instala Hop.
  exit /b 1
)

call "%HOP_RUN%" ^
  --project=%PROJECT_NAME% ^
  --file="%WF%" ^
  --level=Basic ^
  --runconfig=local >> "%LOGFILE%" 2>&1

set "RC=%ERRORLEVEL%"
call :log Fin wf_main_windows exit=%RC%
exit /b %RC%

:log
echo [%date% %time%] %*>> "%LOGFILE%"
exit /b 0
```

## Qué no se bifurca

- `inputs.yaml`, `logica/*.py`, `python/io/`, `python/create_stg.py`, `python/main.py`.
- Esquema destino: `DB_ORA_DW_SCHEMA` vía `config.require_live_conn`. Nunca un literal `APP` en el SQL.
- Intérprete Windows: `scripts/_py.bat` (`.venv\Scripts\python.exe`, si no `python`). En Windows no existe `python3` ni `.venv/bin/python`.

## Qué hace cada agente

- Agente Linux: implementa, corre `./init.sh`, deja el espejo Windows escrito (`scripts\step_*.bat`, `init.bat`, `wf_main_windows.hwf` y `run_wf_main.bat`). No ejecuta `init.bat`. En `progress/impl_<id>.md` anota qué debe comprobar Windows.
- Agente Windows: no reescribe la lógica. Corre `init.bat remote` y, si tocó el workflow, `hop-run.bat` sobre `wf_main_windows.hwf`. La tarea programada apunta a `run_wf_main.bat`. Si el espejo falta, lo añade siguiendo esta skill. No des por cerrada una feature solo con el `HARNESS OK` de Linux.

Gotchas que ya costaron una corrida (esquema fijo, quoting de `for /f`, `goto` dentro de `call`, H2 compartido): [reference.md](reference.md).

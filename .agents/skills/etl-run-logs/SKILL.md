---
name: etl-run-logs
description: >-
  Obliga a que cada corrida de un ETL deje bitácora en logs/ en la raíz del
  repo. Usar al crear o tocar init.sh, init.bat, run_wf_main, un workflow Hop,
  el harness o cuando el usuario mencione logs, bitácora de corrida o que el
  ETL no guarda lo que imprimió.
---

# Logs de corrida

Cada ETL escribe la corrida en `logs/` (raíz del repo). `progress/` es la bitácora de features del harness. No la reemplaza. `h2/h2_server.log` es solo el proceso H2.

El patrón ya usado en `etl_informes_harness/run_wf_main.bat`: carpeta `logs/`, archivo por fecha, el proceso no lo borra al salir.

## Archivo

- `logs/.gitkeep` va en git. El contenido `*.log` no: ya está en `.gitignore`.
- Nombre: `logs/<origen>_YYYYMMDD.log`
  - `init` — `./init.sh` o `init.bat`
  - `wf_main` — Hop o `run_wf_main.sh` / `run_wf_main.bat`
- Misma ruta relativa en Linux y en Windows. No se borra al terminar.
- `init`: si el día ya tiene archivo, se le agrega.
- `run_wf_main.bat`: al empezar borra `logs/wf_main_YYYYMMDD.log` y lo reescribe. Queda la última corrida programada de ese día. Es el comportamiento de los `.bat` ya probados; no lo cambies a append.

## Qué queda escrito

Entorno (`local` o `remote`), esquema Oracle, cada paso, conteos de las `STG_*` y de las tablas destino, y el código de salida. Si falla, el traceback completo queda en ese archivo. La consola puede mostrar lo mismo. La consola sola no cuenta.

## Qué no es un log de corrida

- `print` solo a stdout.
- El temporal de `init.sh` (`mktemp`, se borra con `trap`) o el de `init.bat` (`%TEMP%`, se borra al salir).
- `progress/impl_*.md`.

## Al tocar la corrida

`init.sh` e `init.bat` redirigen la corrida a `logs/init_YYYYMMDD.log`. La corrida Hop programada redirige a `logs/wf_main_YYYYMMDD.log`. Los dos sistemas escriben. Un solo lado no cumple.

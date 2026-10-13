# Referencia — paridad Linux / Windows

Gotchas del arquetipo. No redescubrirlos en cada proyecto.

## Esquema Oracle

No escribas el esquema en el SQL. El de `local` no es el de `remote`, y un literal del entorno de desarrollo falla en el otro con `ORA-01918` (el usuario no existe). El esquema sale de `DB_ORA_DW_SCHEMA`. Si falta, `require_live_conn` usa el usuario en mayúsculas.

## switch-env

Los dos scripts deben crear `project-config.json` si no existe y sobreponer `DB_ORA_DW_*` desde `docs/credenciales/<env>.txt`. No pisar un valor real con un placeholder `<...>`. No copiar `SysPassword`.

## cmd.exe

- No incrustar `python -c` dentro de ``for /f `...` ``. El quoting se come la variable y puede dejar la ruta del intérprete. Leer JSON con `scripts/get_var.ps1`.
- `call :sub` + `goto :fail` no corta el `for` que invocó la subrutina. El `errorlevel` del `for` es el de la última vuelta y el script puede imprimir `HARNESS OK` tras varios `FAIL`. Acumular un flag `FAILED` en el mismo bloque.
- Cada `scripts/step_*.bat` termina con `exit /b %errorlevel%`. Hop marca la acción en falso solo si el `.bat` devuelve distinto de 0.

## H2

`mem:csep` en `localhost:9092` lo comparten los ETL de la misma máquina Windows. Todos hacen `DROP ALL OBJECTS`. No solapar corridas. `init.bat` encadena los pasos en un proceso para acortar esa ventana. No es aislamiento.

En Windows el server es la tarea `H2_SERVICE_MEM_CSEP`. `reset_and_create.bat` no lo mata: comprueba el puerto y reaplica `00_reset.sql` + `01_schema.sql`. En Linux `reset_and_create.sh` sí hace stop + start, y `start_h2.sh` necesita `nohup` o Hop se queda colgado.

La base sigue siendo `mem:csep` en los `.sh` y `.bat` de `h2/scripts/`. Otra base es decisión del proyecto, no del arquetipo.

## Hop Windows

```bat
D:\Eder\hop\hop-run.bat -j <carpeta> -r local -f <repo>\workflows\wf_main_windows.hwf -l BASIC
```

El Programador de tareas no pega ese comando: ejecuta `run_wf_main.bat` (plantilla en esta skill). `--runconfig=local` es el motor Hop, no el entorno `remote`.

`HOP_HOME` y `%USERPROFILE%\apps\hop` pueden no existir; el `.bat` igual los prueba, y cae en `D:\Eder\hop`. El proyecto Hop se llama como la carpeta. Excepción ya en producción, no copiarla: `datawarehouse_multa_etl` se registra como `multa_informes_etl` y su workflow es `wf_main_win.hwf`.

## Red y pandas

`sheets.googleapis.com` puede dar `getaddrinfo failed` de forma intermitente. Fallan juntos `create_stg.py` (introspección) y la carga de hojas. Reintentar la corrida. No fijar otra versión de pandas sin mirar el venv de Linux.

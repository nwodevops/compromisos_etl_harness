@echo off
REM ===========================================================================
REM start_h2_svc.bat — Levanta el server H2 (mem:csep, TCP 9092) como tarea
REM programada INDEPENDIENTE del workflow / init. El proceso java lo lanza la
REM tarea (no el batch), por lo que no hereda la consola de Hop ni recibe el
REM Ctrl-C que hacia colgar a reset_and_create.bat (prompt "^C Terminar el
REM trabajo por lotes (S/N)?" sin respuesta en entorno no interactivo).
REM
REM La tarea ejecuta h2_server.bat (despues se limpia sola al terminar la
REM corrida). Si el puerto ya escucha, no hace nada.
REM
REM Uso: start_h2_svc.bat        o se invoca automaticamente desde
REM       reset_and_create.bat.
REM ===========================================================================
setlocal
cd /d "%~dp0\.."

set H2_PORT=9092
set "TASKID=H2_SERVICE_MEM_CSEP"

REM Si ya escucha, no hacer nada.
netstat -an | findstr ":%H2_PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
  echo H2 ya esta arriba en puerto %H2_PORT%
  exit /b 0
)

REM Comando de la tarea: wrapper batch (sin espacios internos entre comillas).
set "WRAPPER=%CD%\scripts\h2_server.bat"
set "H2CMD=%WRAPPER% %H2_PORT%"

REM Crear la tarea (si existe, se sobrescribe con /f). "/st" se pone en el
REM futuro cercano para evitar la advertencia de hora pasada.
for /f "tokens=1-2 delims=:." %%a in ("%time%") do set "HH=%%a" & set "MM=%%b"
schtasks /create /tn "%TASKID%" /tr "%H2CMD%" /sc once /st %HH%:%MM% /f >nul 2>&1
if errorlevel 1 (
  echo FAIL: no se pudo crear la tarea %TASKID%. Ejecuta como tu usuario ^(sin admin system^).
  exit /b 1
)

REM Ejecutarla.
schtasks /run /tn "%TASKID%" >nul 2>&1

REM Esperar el puerto.
set /a _i=0
:wait_loop
netstat -an | findstr ":%H2_PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
  echo H2 OK puerto %H2_PORT% ^(tarea %TASKID%^)
  exit /b 0
)
set /a _i+=1
if %_i% GEQ 30 (
  echo FAIL: H2 no abrio puerto %H2_PORT%. Revisa h2_server.log
  exit /b 1
)
ping -n 2 127.0.0.1 >nul
goto wait_loop
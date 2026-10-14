@echo off
REM ===========================================================================
REM h2_server.bat — Accion de la tarea programada H2_SERVICE_MEM_CSEP
REM (start_h2_svc.bat). Proceso de larga vida: al heredar la consola de la
REM tarea del Programador, el java NO recibe Ctrl-C y queda desacoplado del
REM workflow / init (no cuelga el batch en el prompt "^C Terminar el trabajo
REM por lotes (S/N)?" en entorno no interactivo).
REM
REM Uso: h2_server.bat [puerto]   (default 9092). Web console: puerto 8082.
REM Log de salida: %~dp0..\h2_server.log
REM ===========================================================================
setlocal
cd /d "%~dp0\.."

set "H2_PORT=%~1"
if "%H2_PORT%"=="" set H2_PORT=9092

set H2_JAR=lib\h2-2.4.240.jar
if not exist "%H2_JAR%" set H2_JAR=h2-2.4.240.jar
if not exist "%H2_JAR%" (
  echo FAIL: no se encontro el jar de H2 ^(%H2_JAR%^)
  exit /b 1
)

java -cp "%H2_JAR%" org.h2.tools.Server -tcp -web -webPort 8082 -tcpPort %H2_PORT% -ifNotExists > h2_server.log 2>&1
exit /b %errorlevel%
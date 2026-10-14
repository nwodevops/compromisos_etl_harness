@echo off
setlocal
cd /d "%~dp0\.."

set H2_JAR=lib\h2-2.4.240.jar
if not exist "%H2_JAR%" set H2_JAR=h2-2.4.240.jar
set H2_PORT=9092
set "H2_LOG=h2_server.log"

REM Si ya escucha, OK
netstat -an | findstr ":%H2_PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
  echo H2 ya esta arriba en puerto %H2_PORT%
  exit /b 0
)

echo Levantando H2 TCP+WEB...
REM Desacoplar el server java del pipe de stdout con el que Hop detecta el fin
REM del paso. Si el java hereda ese pipe, hop-run espera el EOF para siempre
REM (paso colgado). El "& exit" hace que el cmd /c hijo cierre su copia del
REM pipe justo despues de lanzar java.
start "H2-Server" /MIN cmd /c "java -cp ""%H2_JAR%"" org.h2.tools.Server -tcp -web -webPort 8082 -tcpPort %H2_PORT% -ifNotExists > %H2_LOG% 2>&1 & exit"

set /a _i=0
:wait_loop
netstat -an | findstr ":%H2_PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
  echo H2 OK puerto %H2_PORT%
  exit /b 0
)
set /a _i+=1
if %_i% GEQ 30 (
  echo FAIL: H2 no abrio puerto %H2_PORT%. Revisa %H2_LOG%
  exit /b 1
)
ping -n 2 127.0.0.1 >nul
goto wait_loop
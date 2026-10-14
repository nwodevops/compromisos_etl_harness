@echo off
setlocal
cd /d "%~dp0\.."

set H2_JAR=lib\h2-2.4.240.jar
if not exist "%H2_JAR%" set H2_JAR=h2-2.4.240.jar
set "DB_H2_URL=jdbc:h2:tcp://localhost:9092/mem:csep;DB_CLOSE_DELAY=-1;MODE=Oracle;DATABASE_TO_UPPER=TRUE;DEFAULT_NULL_ORDERING=HIGH;AUTO_RECONNECT=TRUE"

REM H2 corre como tarea programada INDEPENDIENTE del workflow / init
REM (start_h2_svc.bat, tarea H2_SERVICE_MEM_CSEP). NO se para/reinicia el
REM server desde este batch: lanzarlo aqui hereda la consola de Hop y un
REM Ctrl-C lo deja colgado en el prompt "^C Terminar el trabajo por lotes
REM (S/N)?" en entornos no interactivos (Programador de tareas).
REM Aqui SOLO se asegura que el puerto escuche (start_h2_svc.bat es
REM idempotente) y se re-aplica el DDL. El reset de memoria es "DROP ALL
REM OBJECTS" (00_reset.sql), asi que no hace falta parar/levantar el server
REM entre corridas.

echo === Verificar/levantar H2 TCP (mem:csep) en puerto 9092 ===
call scripts\start_h2_svc.bat
if errorlevel 1 (
  echo FAIL: H2 no levanto. Revisa h2_server.log.
  exit /b 1
)

echo === Aplicar DDL (sql\00_reset.sql) ===
java -cp "%H2_JAR%" org.h2.tools.RunScript -url "%DB_H2_URL%" -user sa -password csep -script "sql\00_reset.sql"
if errorlevel 1 (
  echo FAIL reset
  exit /b 1
)

echo === Aplicar DDL (sql\01_schema.sql) ===
java -cp "%H2_JAR%" org.h2.tools.RunScript -url "%DB_H2_URL%" -user sa -password csep -script "sql\01_schema.sql"
if errorlevel 1 (
  echo FAIL schema
  exit /b 1
)

echo === Reset+Create OK ===
echo Pipelines / R usan: %DB_H2_URL%
endlocal
exit /b 0
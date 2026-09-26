@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM Corrida headless de wf_main_windows (Programador de tareas Windows).
REM No cambia el entorno: usa el project-config.json de switch-env.ps1 remote.
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
set "PROJECT_NAME=compromisos_etl_harness"
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

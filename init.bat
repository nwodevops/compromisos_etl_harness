@echo off
REM ===========================================================================
REM init.bat — Harness Windows: Reset H2 + STG + Sheets + logica (hop-run).
REM Uso: init.bat [local|remote]    (default: remote)
REM Proyecto Hop: compromisos_etl_harness (junto a etl_informes_harness).
REM ===========================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "HOP_PROJECT=compromisos_etl_harness"
if not "%HOP_PROJECT_OVERRIDE%"=="" set "HOP_PROJECT=%HOP_PROJECT_OVERRIDE%"
set "HOP_RUNCONFIG=local"

set "ENV=%~1"
if "%ENV%"=="" set "ENV=remote"
echo ==^> Harness Windows: entorno %ENV%

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

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

if /I "%HOP_RUN%"=="hop-run" (
  where hop-run >nul 2>&1
  if errorlevel 1 (
    echo FAIL: hop-run.bat no encontrado ^(HOP_RUN, HOP_HOME, D:\Eder\hop o %%USERPROFILE%%\apps\hop^)
    exit /b 1
  )
) else if not exist "%HOP_RUN%" (
  echo FAIL: no se encuentra %HOP_RUN%
  exit /b 1
)

echo ==^> Validando feature_list.json
"%PY%" -c "import json,sys;d=json.load(open('feature_list.json',encoding='utf-8'));act=[f for f in d.get('features',[]) if f.get('status')=='in_progress'];print('features: '+str(len(d.get('features',[])))+', in_progress: '+str(len(act)));sys.exit(1 if len(act)>1 else 0)"
if errorlevel 1 (
  echo FAIL: mas de una in_progress en feature_list.json
  exit /b 1
)

echo ==^> Prerrequisitos
java -version >nul 2>&1
if errorlevel 1 (
  echo FAIL: java no esta en PATH
  exit /b 1
)

echo ==^> switch-env %ENV%
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0switch-env.ps1" %ENV%
if errorlevel 1 (
  echo FAIL: switch-env %ENV%
  exit /b 1
)

echo ==^> hop-run wf_main_windows.hwf
call "%HOP_RUN%" -j %HOP_PROJECT% -r %HOP_RUNCONFIG% -f "%~dp0workflows\wf_main_windows.hwf" -l Basic
if errorlevel 1 (
  echo FAIL: hop-run wf_main_windows.hwf
  exit /b 1
)

echo.
echo HARNESS OK — Windows ^(remote por defecto^). H2 compartido con informes: 9092 / mem:csep.
exit /b 0

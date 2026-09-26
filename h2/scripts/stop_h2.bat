@echo off
setlocal
echo Deteniendo H2 Server si existe...

REM Mata procesos Java cuyo comando incluye org.h2.tools.Server
REM (wmic ya no existe en Windows recientes; se usa powershell).
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | Where-Object { $_.CommandLine -like '*org.h2.tools.Server*' } | ForEach-Object { taskkill /F /PID $_.ProcessId *> $null }"

ping -n 3 127.0.0.1 >nul
echo Stop H2 listo
endlocal
exit /b 0
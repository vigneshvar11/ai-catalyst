@echo off
setlocal EnableDelayedExpansion
REM ============================================================================
REM   EMBRACE AI  -  HOST *WITHOUT* IIS  (direct Node.js, non-disruptive)
REM ----------------------------------------------------------------------------
REM   Use this when the server team confirms EMBRACE AI may listen on its own
REM   dedicated port directly, WITHOUT going through IIS.
REM
REM   WHAT THIS DOES (and does NOT do):
REM     * Node.js (the EmbraceAI Windows service) listens directly on a
REM       dedicated public port -> the browser talks to Node with no proxy.
REM     * It NEVER stops or disables IIS (W3SVC/WAS). Teamcenter and every
REM       existing IIS site keep running exactly as before.
REM     * Because IIS already owns port 80 for other apps, we deliberately use
REM       a SEPARATE dedicated port so there is ZERO conflict.
REM
REM   RUN AS ADMINISTRATOR.
REM ============================================================================

REM ---- CONFIG (edit these if needed) -----------------------------------------
set "SERVICE_NAME=EmbraceAI"
set "APP_DIR=C:\apps\embrace-ai"
set "NSSM=C:\tools\nssm\nssm.exe"
REM  Dedicated public port for EMBRACE AI. 8080 is a common, safe choice.
REM  The script checks it is free before using it.
set "PUBLIC_PORT=8080"
REM ----------------------------------------------------------------------------

echo.
echo  ============================================================
echo   EMBRACE AI  -  Host WITHOUT IIS (direct Node on port %PUBLIC_PORT%)
echo  ============================================================
echo.

REM ---- 0. Require administrator -----------------------------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo  [X] Please run this file as Administrator ^(right-click ^> Run as administrator^).
  echo.
  pause
  exit /b 1
)

REM ---- 1. Sanity checks -------------------------------------------------------
echo  [1/6] Checking prerequisites...
if not exist "%APP_DIR%\server.js" (
  echo       [X] server.js not found in %APP_DIR%. Clone the repo there first.
  pause & exit /b 1
)
if not exist "%NSSM%" (
  echo       [X] NSSM not found at %NSSM%. Run setup-server.ps1 first.
  pause & exit /b 1
)
echo       OK.

REM ---- 2. Make sure the chosen port is FREE ----------------------------------
echo  [2/6] Checking that port %PUBLIC_PORT% is free...
set "PORT_BUSY="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%PUBLIC_PORT% .*LISTENING"') do set "PORT_BUSY=%%p"
if defined PORT_BUSY (
  echo       [X] Port %PUBLIC_PORT% is already in use by PID %PORT_BUSY%.
  echo           Pick another free port: edit PUBLIC_PORT at the top of this file.
  echo           Tip - list busy ports with:  netstat -ano ^| findstr LISTENING
  pause & exit /b 1
)
echo       Port %PUBLIC_PORT% is free.

REM ---- 3. Point the Node service at the dedicated public port ----------------
echo  [3/6] Setting the EmbraceAI service to listen on port %PUBLIC_PORT%...
"%NSSM%" stop %SERVICE_NAME% >nul 2>&1
timeout /t 2 /nobreak >nul
"%NSSM%" set %SERVICE_NAME% AppEnvironmentExtra "NODE_ENV=production" "PORT=%PUBLIC_PORT%" >nul 2>&1
echo       Environment updated.

REM ---- 4. Ensure the service auto-restarts on failure/reboot -----------------
echo  [4/6] Ensuring auto-start + auto-restart...
"%NSSM%" set %SERVICE_NAME% Start SERVICE_AUTO_START >nul 2>&1
"%NSSM%" set %SERVICE_NAME% AppExit Default Restart >nul 2>&1
"%NSSM%" set %SERVICE_NAME% AppRestartDelay 5000 >nul 2>&1
sc failure %SERVICE_NAME% reset= 86400 actions= restart/5000/restart/5000/restart/5000 >nul 2>&1
echo       Configured.

REM ---- 5. Start the service + open the firewall ------------------------------
echo  [5/6] Starting service and opening firewall...
"%NSSM%" start %SERVICE_NAME% >nul 2>&1
timeout /t 4 /nobreak >nul
netsh advfirewall firewall add rule name="EmbraceAI HTTP %PUBLIC_PORT%" dir=in action=allow protocol=TCP localport=%PUBLIC_PORT% >nul 2>&1
echo       Service started, firewall rule added.

REM ---- 6. Verify -------------------------------------------------------------
echo  [6/6] Verifying...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:%PUBLIC_PORT%/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host ('       [OK] Node on port %PUBLIC_PORT% -> HTTP ' + $r.StatusCode) -ForegroundColor Green } catch { Write-Host '       [X] Port %PUBLIC_PORT% test failed. Check logs:' -ForegroundColor Red; Write-Host '           Get-Content %APP_DIR%\logs\embrace-ai-stderr.log -Tail 20' -ForegroundColor Yellow }"

echo.
echo  ============================================================
echo   DONE.  Architecture:
echo     Browser  ->  Node ^(port %PUBLIC_PORT%^)  ->  db.json
echo.
echo   URL:  http://SN1W7220.AD001.SIEMENS.NET:%PUBLIC_PORT%
echo.
echo   IIS, Teamcenter and all existing sites were NOT modified.
echo  ============================================================
echo.
pause
endlocal

@echo off
setlocal EnableDelayedExpansion
REM ============================================================================
REM   EMBRACE AI  -  HOST *WITH* IIS  (reverse proxy, non-disruptive)
REM ----------------------------------------------------------------------------
REM   Use this when the server team wants EMBRACE AI to sit BEHIND IIS, exactly
REM   like the other applications (Teamcenter, etc.) on SN1W7220.
REM
REM   WHAT THIS DOES (and does NOT do):
REM     * Node.js runs privately on 127.0.0.1:3000 (not exposed directly).
REM     * A NEW, SEPARATE IIS site ("EmbraceAI") is created on a dedicated port
REM       and reverse-proxies every request (including WebSockets) to Node.
REM     * It NEVER stops/disables IIS (W3SVC/WAS) and NEVER touches the
REM       Default Web Site or any existing site -> Teamcenter stays untouched.
REM
REM   PREREQUISITES (installed once on the server):
REM     * IIS with the "WebSocket Protocol" role feature
REM     * URL Rewrite Module  -> https://www.iis.net/downloads/microsoft/url-rewrite
REM     * Application Request Routing (ARR) -> https://www.iis.net/downloads/microsoft/application-request-routing
REM
REM   RUN AS ADMINISTRATOR.
REM ============================================================================

REM ---- CONFIG (edit these if needed) -----------------------------------------
set "SERVICE_NAME=EmbraceAI"
set "APP_DIR=C:\apps\embrace-ai"
set "IIS_ROOT=C:\inetpub\embrace-ai"
set "NSSM=C:\tools\nssm\nssm.exe"
set "SITE_NAME=EmbraceAI"
set "NODE_PORT=3000"
set "PUBLIC_PORT=8080"
REM  Optional: set a host header for a clean URL (needs a DNS record). Leave blank
REM  to serve on the dedicated port instead, e.g. http://SN1W7220...:8080
set "HOST_HEADER="
REM ----------------------------------------------------------------------------

echo.
echo  ============================================================
echo   EMBRACE AI  -  Host WITH IIS (reverse proxy to Node:%NODE_PORT%)
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
echo  [1/8] Checking prerequisites...
if not exist "%APP_DIR%\server.js" (
  echo       [X] server.js not found in %APP_DIR%. Clone the repo there first.
  pause & exit /b 1
)
if not exist "%NSSM%" (
  echo       [X] NSSM not found at %NSSM%. Run setup-server.ps1 first.
  pause & exit /b 1
)
where appcmd >nul 2>&1
if %errorlevel% neq 0 set "APPCMD=%windir%\system32\inetsrv\appcmd.exe"
if not defined APPCMD set "APPCMD=appcmd"
echo       OK.

REM ---- 2. Enable IIS WebSocket feature (safe, idempotent) --------------------
echo  [2/8] Ensuring IIS WebSocket feature is enabled...
dism /online /enable-feature /featurename:IIS-WebSockets /all /norestart >nul 2>&1
echo       Done.

REM ---- 3. Verify ARR + URL Rewrite are present -------------------------------
echo  [3/8] Checking ARR + URL Rewrite modules...
"%APPCMD%" list module /name:ApplicationRequestRouting >nul 2>&1
if %errorlevel% neq 0 (
  echo       [!] Application Request Routing ^(ARR^) not detected.
  echo           Install it: https://www.iis.net/downloads/microsoft/application-request-routing
)
reg query "HKLM\SOFTWARE\Microsoft\IIS Extensions\URL Rewrite" >nul 2>&1
if %errorlevel% neq 0 (
  echo       [!] URL Rewrite module not detected.
  echo           Install it: https://www.iis.net/downloads/microsoft/url-rewrite
)
echo       Check complete ^(warnings above must be resolved for the proxy to work^).

REM ---- 4. Enable ARR proxy at the server level ------------------------------
echo  [4/8] Enabling ARR reverse-proxy at server level...
"%APPCMD%" set config -section:system.webServer/proxy /enabled:"True" /commit:apphost >nul 2>&1
echo       Done.

REM ---- 5. Point the Node service at the PRIVATE port 3000 --------------------
echo  [5/8] Configuring Node service to listen on 127.0.0.1:%NODE_PORT%...
"%NSSM%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM%" set %SERVICE_NAME% AppEnvironmentExtra "NODE_ENV=production" "PORT=%NODE_PORT%" >nul 2>&1
"%NSSM%" start %SERVICE_NAME% >nul 2>&1
timeout /t 3 /nobreak >nul
echo       Node service restarted on port %NODE_PORT%.

REM ---- 6. Prepare IIS site folder + web.config ------------------------------
echo  [6/8] Preparing IIS site folder + web.config...
if not exist "%IIS_ROOT%" mkdir "%IIS_ROOT%"
if exist "%APP_DIR%\deploy\iis\web.config" (
  copy /y "%APP_DIR%\deploy\iis\web.config" "%IIS_ROOT%\web.config" >nul
  echo       web.config copied to %IIS_ROOT%.
) else (
  echo       [!] web.config not found at %APP_DIR%\deploy\iis\web.config
)

REM ---- 7. Create/refresh the DEDICATED IIS site (no other site touched) ------
echo  [7/8] Creating IIS site "%SITE_NAME%" on port %PUBLIC_PORT%...
"%APPCMD%" delete site "%SITE_NAME%" >nul 2>&1
if defined HOST_HEADER (
  "%APPCMD%" add site /name:"%SITE_NAME%" /physicalPath:"%IIS_ROOT%" /bindings:"http/*:%PUBLIC_PORT%:%HOST_HEADER%" >nul 2>&1
) else (
  "%APPCMD%" add site /name:"%SITE_NAME%" /physicalPath:"%IIS_ROOT%" /bindings:"http/*:%PUBLIC_PORT%:" >nul 2>&1
)
"%APPCMD%" start site "%SITE_NAME%" >nul 2>&1
echo       Site created and started.

REM ---- 8. Firewall + verify --------------------------------------------------
echo  [8/8] Opening firewall for port %PUBLIC_PORT% and verifying...
netsh advfirewall firewall add rule name="EmbraceAI HTTP %PUBLIC_PORT%" dir=in action=allow protocol=TCP localport=%PUBLIC_PORT% >nul 2>&1
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:%PUBLIC_PORT%/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host ('       [OK] Reachable via IIS -> HTTP ' + $r.StatusCode) -ForegroundColor Green } catch { Write-Host '       [X] Not reachable via IIS yet. Check ARR/URL Rewrite install and Node service.' -ForegroundColor Yellow }"

echo.
echo  ============================================================
echo   DONE.  Architecture:
echo     Browser  ->  IIS ^(port %PUBLIC_PORT%^)  ->  Node ^(127.0.0.1:%NODE_PORT%^)  ->  db.json
echo.
if defined HOST_HEADER (
  echo   URL:  http://%HOST_HEADER%
) else (
  echo   URL:  http://SN1W7220.AD001.SIEMENS.NET:%PUBLIC_PORT%
)
echo.
echo   IIS, Teamcenter and all existing sites were NOT modified.
echo  ============================================================
echo.
pause
endlocal

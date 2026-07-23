@echo off
REM ═══════════════════════════════════════════════════════════
REM  EMBRACE AI — Step 9: Service + IIS Setup
REM  Run as Administrator on SN1W7220.AD001.SIEMENS.NET
REM  Prerequisites: Steps 1-8 already completed (full-setup.bat)
REM ═══════════════════════════════════════════════════════════

echo.
echo  === Creating Windows Service + IIS Site ===
echo.

REM ─── Remove existing service if any ───
C:\tools\nssm\nssm.exe stop EmbraceAI 2>nul
C:\tools\nssm\nssm.exe remove EmbraceAI confirm 2>nul

REM ─── Create logs directory ───
if not exist "C:\apps\embrace-ai\logs" mkdir "C:\apps\embrace-ai\logs"

REM ─── Install the service ───
echo [1/6] Installing Windows Service...
C:\tools\nssm\nssm.exe install EmbraceAI "C:\Program Files\nodejs\node.exe" "C:\apps\embrace-ai\server.js"
C:\tools\nssm\nssm.exe set EmbraceAI AppDirectory "C:\apps\embrace-ai"
C:\tools\nssm\nssm.exe set EmbraceAI DisplayName "EMBRACE AI Dashboard"
C:\tools\nssm\nssm.exe set EmbraceAI Description "EMBRACE AI — Engineering Systems Initiative Dashboard"
C:\tools\nssm\nssm.exe set EmbraceAI Start SERVICE_AUTO_START
C:\tools\nssm\nssm.exe set EmbraceAI AppStdout "C:\apps\embrace-ai\logs\stdout.log"
C:\tools\nssm\nssm.exe set EmbraceAI AppStderr "C:\apps\embrace-ai\logs\stderr.log"
C:\tools\nssm\nssm.exe set EmbraceAI AppStdoutCreationDisposition 4
C:\tools\nssm\nssm.exe set EmbraceAI AppStderrCreationDisposition 4
C:\tools\nssm\nssm.exe set EmbraceAI AppRotateFiles 1
C:\tools\nssm\nssm.exe set EmbraceAI AppRotateBytes 5242880
C:\tools\nssm\nssm.exe set EmbraceAI AppExit Default Restart
C:\tools\nssm\nssm.exe set EmbraceAI AppRestartDelay 5000
C:\tools\nssm\nssm.exe set EmbraceAI AppEnvironmentExtra "NODE_ENV=production"
echo       Service installed.

REM ─── Start the service ───
echo [2/6] Starting service...
C:\tools\nssm\nssm.exe start EmbraceAI
timeout /t 4 /nobreak >nul
C:\tools\nssm\nssm.exe status EmbraceAI

REM ─── Verify Node is running on port 3000 ───
echo [3/6] Testing Node.js on port 3000...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:3000/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host '      Node.js API: OK (Status' $r.StatusCode')' -ForegroundColor Green } catch { Write-Host '      Node.js API: FAILED - check logs at C:\apps\embrace-ai\logs\stderr.log' -ForegroundColor Red; Get-Content 'C:\apps\embrace-ai\logs\stderr.log' -Tail 10 -ErrorAction SilentlyContinue }"

REM ─── Copy IIS web.config ───
echo [4/6] Configuring IIS reverse proxy...
copy /y "C:\apps\embrace-ai\deploy\iis\web.config" "C:\inetpub\embrace-ai\web.config"

REM ─── Create IIS site ───
echo [5/6] Creating IIS site on port 80...
powershell -Command "Import-Module WebAdministration; Stop-Website -Name 'Default Web Site' -ErrorAction SilentlyContinue; Remove-Website -Name 'EmbraceAI' -ErrorAction SilentlyContinue; New-Website -Name 'EmbraceAI' -PhysicalPath 'C:\inetpub\embrace-ai' -Port 80 -Force | Out-Null; Start-Website -Name 'EmbraceAI'; Write-Host '      IIS site created and started.' -ForegroundColor Green"

REM ─── Open firewall ───
echo [6/6] Opening firewall port 80...
netsh advfirewall firewall add rule name="EmbraceAI HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
echo       Firewall rule added.

echo.
echo  === Final Verification ===
echo.
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host '  IIS Reverse Proxy: OK (Status' $r.StatusCode')' -ForegroundColor Green } catch { Write-Host '  IIS Reverse Proxy: FAILED' -ForegroundColor Red; Write-Host '  Possible fixes:' -ForegroundColor Yellow; Write-Host '    1. Check ARR is enabled: IIS Manager > Server > Application Request Routing > Enable proxy' -ForegroundColor Yellow; Write-Host '    2. Check service: C:\tools\nssm\nssm.exe status EmbraceAI' -ForegroundColor Yellow; Write-Host '    3. Check logs: Get-Content C:\apps\embrace-ai\logs\stderr.log -Tail 20' -ForegroundColor Yellow }"

echo.
echo  Open in browser: http://SN1W7220.AD001.SIEMENS.NET
echo.
pause

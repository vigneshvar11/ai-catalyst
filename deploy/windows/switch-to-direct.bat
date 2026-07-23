@echo off
REM ═══════════════════════════════════════════════════════
REM  EMBRACE AI — Direct Node.js on Port 80 (skip IIS)
REM  Run as Administrator on SN1W7220.AD001.SIEMENS.NET
REM ═══════════════════════════════════════════════════════

echo.
echo  === Switching to Node.js direct on port 80 ===
echo.

REM ─── Stop IIS services so they release port 80 ───
echo [1/5] Disabling IIS services...
sc stop W3SVC >nul 2>&1
sc stop WAS >nul 2>&1
sc config W3SVC start= disabled >nul 2>&1
sc config WAS start= disabled >nul 2>&1
iisreset /stop >nul 2>&1
echo       IIS stopped and disabled.

REM ─── Stop existing service ───
echo [2/5] Stopping EmbraceAI service...
C:\tools\nssm\nssm.exe stop EmbraceAI 2>nul
timeout /t 2 /nobreak >nul

REM ─── Reconfigure service to use PORT=80 ───
echo [3/5] Setting PORT=80 in service config...
C:\tools\nssm\nssm.exe set EmbraceAI AppEnvironmentExtra "NODE_ENV=production" "PORT=80"
echo       Environment updated.

REM ─── Start service ───
echo [4/5] Starting service on port 80...
C:\tools\nssm\nssm.exe start EmbraceAI
timeout /t 4 /nobreak >nul
C:\tools\nssm\nssm.exe status EmbraceAI

REM ─── Open firewall for HTTP ───
echo       Ensuring firewall allows port 80...
netsh advfirewall firewall add rule name="EmbraceAI HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1

REM ─── Verify ───
echo [5/5] Verifying...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host '  Node.js on port 80: OK (Status' $r.StatusCode')' -ForegroundColor Green; Write-Host ''; Write-Host '  SUCCESS! Open http://SN1W7220.AD001.SIEMENS.NET' -ForegroundColor Green } catch { Write-Host '  Port 80 test failed. Checking port 3000...' -ForegroundColor Yellow; try { $r2 = Invoke-WebRequest -Uri 'http://localhost:3000/api/members' -UseBasicParsing -TimeoutSec 5; Write-Host '  Port 3000 works but port 80 does not.' -ForegroundColor Yellow; Write-Host '  Something else is using port 80. Run: netstat -ano | findstr :80' -ForegroundColor Yellow } catch { Write-Host '  Neither port works. Check logs:' -ForegroundColor Red; Write-Host '  Get-Content C:\apps\embrace-ai\logs\stderr.log -Tail 20' -ForegroundColor Red } }"

echo.
pause

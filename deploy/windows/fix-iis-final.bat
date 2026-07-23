@echo off
REM ═══════════════════════════════════════════════════════
REM  EMBRACE AI — IIS Reverse Proxy Final Fix
REM  Run as Administrator on SN1W7220.AD001.SIEMENS.NET
REM
REM  Assumes:
REM   - ARR installed and "Enable proxy" checkbox ticked
REM   - Node.js service "EmbraceAI" running on port 3000
REM   - URL Rewrite module installed
REM ═══════════════════════════════════════════════════════

echo.
echo  === IIS Reverse Proxy — Final Fix ===
echo.

REM ─── Step 1: Make sure Node.js is on port 3000 (undo switch-to-direct if ran) ───
echo [1/7] Ensuring Node.js service uses port 3000...
C:\tools\nssm\nssm.exe stop EmbraceAI 2>nul
timeout /t 2 /nobreak >nul
C:\tools\nssm\nssm.exe set EmbraceAI AppEnvironmentExtra "NODE_ENV=production" "PORT=3000"
C:\tools\nssm\nssm.exe start EmbraceAI
timeout /t 4 /nobreak >nul
echo       Checking port 3000...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:3000/api/members' -UseBasicParsing -TimeoutSec 5; Write-Host '      Port 3000: OK' -ForegroundColor Green } catch { Write-Host '      Port 3000: FAILED — service not running' -ForegroundColor Red; exit 1 }"
echo.

REM ─── Step 2: Start IIS service ───
echo [2/7] Starting IIS...
net start W3SVC 2>nul
echo       IIS service started.
echo.

REM ─── Step 3: Copy simplified web.config ───
echo [3/7] Deploying simplified web.config...
copy /y "C:\apps\embrace-ai\deploy\iis\web.config" "C:\inetpub\embrace-ai\web.config"
echo       web.config copied.
echo.

REM ─── Step 4: Recreate IIS site ───
echo [4/7] Recreating IIS site...
powershell -Command "Import-Module WebAdministration; Remove-Website -Name 'EmbraceAI' -ErrorAction SilentlyContinue; Remove-Website -Name 'Default Web Site' -ErrorAction SilentlyContinue; New-Website -Name 'EmbraceAI' -PhysicalPath 'C:\inetpub\embrace-ai' -Port 80 -Force | Out-Null; Start-Website -Name 'EmbraceAI'; Write-Host '      IIS site EmbraceAI on port 80: Created' -ForegroundColor Green"
echo.

REM ─── Step 5: Verify ARR proxy is enabled at server level ───
echo [5/7] Verifying ARR proxy setting...
powershell -Command "$ahc = Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config'; $content = Get-Content $ahc -Raw; if ($content -match '<proxy\s+enabled=""true""') { Write-Host '      ARR proxy: ENABLED in applicationHost.config' -ForegroundColor Green } else { Write-Host '      ARR proxy: NOT found in config — adding it...' -ForegroundColor Yellow; $content = $content -replace '</system.webServer>', '    <proxy enabled=""true"" preserveHostHeader=""true"" />`r`n    </system.webServer>'; Set-Content $ahc $content -Encoding UTF8; Write-Host '      ARR proxy: Added to config' -ForegroundColor Green }"
echo.

REM ─── Step 6: Reset IIS ───
echo [6/7] Resetting IIS...
iisreset /restart
timeout /t 4 /nobreak >nul
echo.

REM ─── Step 7: Final test ───
echo [7/7] Final verification...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host ''; Write-Host '  ============================================' -ForegroundColor Green; Write-Host '  SUCCESS! IIS reverse proxy is working!' -ForegroundColor Green; Write-Host '  Status:' $r.StatusCode -ForegroundColor Green; Write-Host ''; Write-Host '  Open: http://SN1W7220.AD001.SIEMENS.NET' -ForegroundColor Green; Write-Host '  ============================================' -ForegroundColor Green } catch { Write-Host ''; Write-Host '  STILL FAILING. Debug info:' -ForegroundColor Red; Write-Host ''; netstat -ano | findstr ':80 '; Write-Host ''; Write-Host '  Verify manually:' -ForegroundColor Yellow; Write-Host '    1. IIS Manager > server name > double-click Application Request Routing' -ForegroundColor Yellow; Write-Host '    2. Click Server Proxy Settings (right panel)' -ForegroundColor Yellow; Write-Host '    3. Tick Enable proxy > Apply' -ForegroundColor Yellow; Write-Host '    4. IIS Manager > Sites > EmbraceAI > double-click URL Rewrite' -ForegroundColor Yellow; Write-Host '    5. You should see rule ReverseProxyToNode > test it by browsing to http://localhost' -ForegroundColor Yellow }"
echo.
pause

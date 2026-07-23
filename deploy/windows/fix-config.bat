@echo off
REM ═══════════════════════════════════════════════════════
REM  EMBRACE AI — Fix corrupted applicationHost.config
REM  Run as Administrator on SN1W7220.AD001.SIEMENS.NET
REM ═══════════════════════════════════════════════════════

echo.
echo  === Fixing corrupted applicationHost.config ===
echo.

REM ─── Step 1: Remove the malformed proxy line we injected ───
echo [1/4] Removing bad proxy line from applicationHost.config...
powershell -Command "$ahc = Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config'; $lines = Get-Content $ahc; $fixed = $lines | Where-Object { $_ -notmatch 'proxy enabled' }; Set-Content $ahc $fixed -Encoding UTF8; Write-Host '      Removed malformed proxy line.' -ForegroundColor Green"

REM ─── Step 2: Restart IIS ───
echo [2/4] Restarting IIS...
iisreset /restart
timeout /t 3 /nobreak >nul
powershell -Command "if ((Get-Service W3SVC).Status -eq 'Running') { Write-Host '      IIS is running.' -ForegroundColor Green } else { Write-Host '      IIS failed to start — check Event Viewer.' -ForegroundColor Red; pause; exit 1 }"
echo.

REM ─── Step 3: Enable ARR proxy properly via appcmd ───
echo [3/4] Enabling ARR proxy via appcmd...
"%windir%\system32\inetsrv\appcmd.exe" set config -section:system.webServer/proxy /enabled:true /preserveHostHeader:true /commit:apphost
if %ERRORLEVEL% EQU 0 (
    echo       ARR proxy enabled.
) else (
    echo       appcmd failed. Trying manual XML insert...
    powershell -Command "$ahc = Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config'; [xml]$xml = Get-Content $ahc; $ws = $xml.configuration.'system.webServer'; if (-not $ws) { $ws = $xml.CreateElement('system.webServer'); $xml.configuration.AppendChild($ws) | Out-Null }; $existing = $ws.SelectSingleNode('proxy'); if ($existing) { $ws.RemoveChild($existing) | Out-Null }; $proxy = $xml.CreateElement('proxy'); $proxy.SetAttribute('enabled','true'); $proxy.SetAttribute('preserveHostHeader','true'); $ws.AppendChild($proxy) | Out-Null; $xml.Save($ahc); Write-Host '      Proxy added via XML API.' -ForegroundColor Green"
    iisreset /restart
    timeout /t 3 /nobreak >nul
)
echo.

REM ─── Step 4: Recreate site and verify ───
echo [4/4] Recreating IIS site and testing...
powershell -Command "Import-Module WebAdministration; Remove-Website -Name 'EmbraceAI' -ErrorAction SilentlyContinue; New-Website -Name 'EmbraceAI' -PhysicalPath 'C:\inetpub\embrace-ai' -Port 80 -Force | Out-Null; Start-Website -Name 'EmbraceAI'; Write-Host '      IIS site recreated on port 80.' -ForegroundColor Green"

timeout /t 2 /nobreak >nul

powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host ''; Write-Host '  ============================================' -ForegroundColor Green; Write-Host '  SUCCESS! IIS -> Node.js proxy working!' -ForegroundColor Green; Write-Host '  Open: http://SN1W7220.AD001.SIEMENS.NET' -ForegroundColor Green; Write-Host '  ============================================' -ForegroundColor Green } catch { Write-Host ''; Write-Host '  Port 80 still not proxying. Try the GUI approach:' -ForegroundColor Yellow; Write-Host '    IIS Manager > server > Application Request Routing > Server Proxy Settings > Enable proxy > Apply' -ForegroundColor Yellow; Write-Host '    Then browse http://localhost and it should work.' -ForegroundColor Yellow }"
echo.
pause

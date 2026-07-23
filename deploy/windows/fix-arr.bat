@echo off
REM ═══════════════════════════════════════════════════════
REM  Fix ARR Proxy for EMBRACE AI
REM  Run as Administrator on the server
REM ═══════════════════════════════════════════════════════

echo.
echo  === Fixing IIS Application Request Routing ===
echo.

REM ─── Step 1: Enable ARR proxy at server level ───
echo [1/4] Enabling ARR proxy...
powershell -Command ^
  "$adminMgr = New-Object -ComObject 'Microsoft.ApplicationHost.WritableAdminManager';" ^
  "$adminMgr.CommitPath = 'MACHINE/WEBROOT/APPHOST';" ^
  "$proxy = $adminMgr.GetAdminSection('system.webServer/proxy', 'MACHINE/WEBROOT/APPHOST');" ^
  "$proxy.Properties.Item('enabled').Value = $true;" ^
  "$proxy.Properties.Item('preserveHostHeader').Value = $true;" ^
  "$proxy.Properties.Item('reverseRewriteHostInResponseHeaders').Value = $false;" ^
  "$adminMgr.CommitChanges();" ^
  "Write-Host '      ARR proxy enabled via COM.' -ForegroundColor Green"

REM ─── Step 2: Ensure WebSocket module is loaded ───
echo [2/4] Checking WebSocket module...
powershell -Command "if ((Get-WindowsFeature Web-WebSockets).Installed) { Write-Host '      WebSocket: OK' -ForegroundColor Green } else { Install-WindowsFeature Web-WebSockets; Write-Host '      WebSocket: Installed' -ForegroundColor Yellow }"

REM ─── Step 3: Reset IIS to load new config ───
echo [3/4] Restarting IIS...
iisreset /restart

timeout /t 3 /nobreak >nul

REM ─── Step 4: Verify ───
echo [4/4] Verifying...
powershell -Command ^
  "try {" ^
  "  $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10;" ^
  "  Write-Host '      IIS Reverse Proxy: OK (Status' $r.StatusCode')' -ForegroundColor Green;" ^
  "  Write-Host '';" ^
  "  Write-Host '  SUCCESS! Open http://SN1W7220.AD001.SIEMENS.NET in your browser.' -ForegroundColor Green;" ^
  "} catch {" ^
  "  Write-Host '      Still failing. Trying direct applicationHost.config edit...' -ForegroundColor Yellow;" ^
  "  $ahc = [System.Environment]::ExpandEnvironmentVariables('%%windir%%\system32\inetsrv\config\applicationHost.config');" ^
  "  $xml = [xml](Get-Content $ahc);" ^
  "  $ws = $xml.SelectSingleNode('//system.webServer');" ^
  "  if (-not $ws) { $ws = $xml.CreateElement('system.webServer'); $xml.configuration.AppendChild($ws) | Out-Null };" ^
  "  $proxy = $ws.SelectSingleNode('proxy');" ^
  "  if (-not $proxy) { $proxy = $xml.CreateElement('proxy'); $ws.AppendChild($proxy) | Out-Null };" ^
  "  $proxy.SetAttribute('enabled', 'true');" ^
  "  $proxy.SetAttribute('preserveHostHeader', 'true');" ^
  "  $xml.Save($ahc);" ^
  "  Write-Host '      Wrote proxy config directly. Running iisreset...' -ForegroundColor Yellow;" ^
  "  iisreset /restart;" ^
  "  Start-Sleep -Seconds 3;" ^
  "  try { $r2 = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host '      IIS Reverse Proxy: OK (Status' $r2.StatusCode')' -ForegroundColor Green } catch { Write-Host '      STILL FAILED. Open IIS Manager > click server name > Application Request Routing > Server Proxy Settings > Enable proxy checkbox > Apply.' -ForegroundColor Red };" ^
  "}"

echo.
pause

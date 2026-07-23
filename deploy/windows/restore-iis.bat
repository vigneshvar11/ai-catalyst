@echo off
REM ═══════════════════════════════════════════════════════
REM  EMBRACE AI — Restore applicationHost.config from backup
REM  Run as Administrator on SN1W7220.AD001.SIEMENS.NET
REM ═══════════════════════════════════════════════════════

echo.
echo  === Restoring IIS Configuration ===
echo.

REM ─── Step 1: Find and restore from IIS config history ───
echo [1/5] Looking for IIS config backups...
powershell -Command ^
  "$historyDir = Join-Path $env:windir 'system32\inetsrv\config\configHistory';" ^
  "$backupDirs = Get-ChildItem $historyDir -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending;" ^
  "if ($backupDirs.Count -eq 0) {" ^
  "  Write-Host '      No config history found. Trying schema backup...' -ForegroundColor Yellow;" ^
  "  $schemaBackup = Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config.bak';" ^
  "  if (Test-Path $schemaBackup) { Copy-Item $schemaBackup (Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config') -Force; Write-Host '      Restored from .bak' -ForegroundColor Green }" ^
  "  else { Write-Host '      NO BACKUP FOUND. Will try to fix manually.' -ForegroundColor Red }" ^
  "} else {" ^
  "  foreach ($dir in $backupDirs) {" ^
  "    $candidate = Join-Path $dir.FullName 'applicationHost.config';" ^
  "    if (Test-Path $candidate) {" ^
  "      try {" ^
  "        [xml]$test = Get-Content $candidate;" ^
  "        Write-Host ('      Found valid backup: ' + $dir.Name) -ForegroundColor Green;" ^
  "        $target = Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config';" ^
  "        Copy-Item $candidate $target -Force;" ^
  "        Write-Host '      Restored applicationHost.config from backup.' -ForegroundColor Green;" ^
  "        break;" ^
  "      } catch { continue }" ^
  "    }" ^
  "  }" ^
  "}"
echo.

REM ─── Step 2: Verify the config is valid XML ───
echo [2/5] Validating restored config...
powershell -Command ^
  "$ahc = Join-Path $env:windir 'system32\inetsrv\config\applicationHost.config';" ^
  "try { [xml]$xml = Get-Content $ahc; Write-Host '      Config is valid XML.' -ForegroundColor Green }" ^
  "catch { Write-Host '      Config still broken! Error:' $_.Exception.Message -ForegroundColor Red; exit 1 }"
echo.

REM ─── Step 3: Restart IIS ───
echo [3/5] Restarting IIS...
iisreset /restart
timeout /t 3 /nobreak >nul
powershell -Command "if ((Get-Service W3SVC).Status -eq 'Running') { Write-Host '      IIS is RUNNING.' -ForegroundColor Green } else { Write-Host '      IIS still not starting. Try: net start W3SVC' -ForegroundColor Red }"
echo.

REM ─── Step 4: Enable ARR proxy via appcmd (now that config is valid) ───
echo [4/5] Enabling ARR proxy via appcmd...
"%windir%\system32\inetsrv\appcmd.exe" set config -section:system.webServer/proxy /enabled:true /preserveHostHeader:true /commit:apphost
if %ERRORLEVEL% EQU 0 (
    echo       ARR proxy enabled successfully.
) else (
    echo       appcmd failed - you may need to enable proxy manually in IIS Manager.
    echo       IIS Manager ^> server name ^> Application Request Routing ^> Server Proxy Settings ^> Enable proxy
)
echo.

REM ─── Step 5: Create site and test ───
echo [5/5] Setting up IIS site and testing...
powershell -Command ^
  "Import-Module WebAdministration;" ^
  "Stop-Website -Name 'Default Web Site' -ErrorAction SilentlyContinue;" ^
  "Remove-Website -Name 'EmbraceAI' -ErrorAction SilentlyContinue;" ^
  "New-Website -Name 'EmbraceAI' -PhysicalPath 'C:\inetpub\embrace-ai' -Port 80 -Force | Out-Null;" ^
  "Start-Website -Name 'EmbraceAI';" ^
  "Write-Host '      IIS site created.' -ForegroundColor Green;" ^
  "Start-Sleep -Seconds 2;" ^
  "try {" ^
  "  $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10;" ^
  "  Write-Host '';" ^
  "  Write-Host '  ============================================' -ForegroundColor Green;" ^
  "  Write-Host '  SUCCESS! IIS reverse proxy is working!' -ForegroundColor Green;" ^
  "  Write-Host '  Open: http://SN1W7220.AD001.SIEMENS.NET' -ForegroundColor Green;" ^
  "  Write-Host '  ============================================' -ForegroundColor Green;" ^
  "} catch {" ^
  "  Write-Host '  IIS site created but proxy not forwarding yet.' -ForegroundColor Yellow;" ^
  "  Write-Host '  Enable ARR proxy manually:' -ForegroundColor Yellow;" ^
  "  Write-Host '    1. Open IIS Manager' -ForegroundColor Yellow;" ^
  "  Write-Host '    2. Click server name (top level)' -ForegroundColor Yellow;" ^
  "  Write-Host '    3. Double-click Application Request Routing Cache' -ForegroundColor Yellow;" ^
  "  Write-Host '    4. Click Server Proxy Settings (right panel)' -ForegroundColor Yellow;" ^
  "  Write-Host '    5. CHECK Enable proxy' -ForegroundColor Yellow;" ^
  "  Write-Host '    6. Click Apply' -ForegroundColor Yellow;" ^
  "  Write-Host '    7. Browse http://localhost' -ForegroundColor Yellow;" ^
  "}"
echo.
pause

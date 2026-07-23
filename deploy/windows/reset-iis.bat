@echo off
REM ═══════════════════════════════════════════════════════
REM  EMBRACE AI — Nuclear IIS Reset (reinstall from scratch)
REM  Run as Administrator on SN1W7220.AD001.SIEMENS.NET
REM
REM  This completely removes and reinstalls IIS to get a
REM  fresh, clean applicationHost.config. Node.js service
REM  is NOT affected.
REM ═══════════════════════════════════════════════════════

echo.
echo  ══════════════════════════════════════════════════
echo   IIS Complete Reset — This will:
echo     1. Uninstall IIS entirely
echo     2. Delete the corrupted config
echo     3. Reinstall IIS with WebSocket support
echo     4. Reinstall URL Rewrite + ARR
echo     5. Enable ARR proxy
echo     6. Create the EmbraceAI site
echo     7. Verify everything works
echo.
echo   Node.js service will NOT be touched.
echo  ══════════════════════════════════════════════════
echo.
pause

REM ─── Step 1: Uninstall IIS ───
echo.
echo [1/7] Uninstalling IIS (this takes ~60 seconds)...
powershell -Command "Uninstall-WindowsFeature Web-Server -IncludeManagementTools -Restart:$false"
echo       IIS removed.
echo.

REM ─── Step 2: Delete corrupted config ───
echo [2/7] Removing corrupted config files...
del /f "%windir%\system32\inetsrv\config\applicationHost.config" 2>nul
del /f "%windir%\system32\inetsrv\config\administration.config" 2>nul
echo       Old config deleted.
echo.

REM ─── Step 3: Reinstall IIS with all needed features ───
echo [3/7] Reinstalling IIS with WebSocket support (~90 seconds)...
powershell -Command "Install-WindowsFeature Web-Server, Web-WebSockets, Web-Mgmt-Console, Web-Stat-Compression, Web-Dyn-Compression, Web-Filtering -IncludeManagementTools"
echo       IIS reinstalled with clean config.
echo.

REM ─── Step 4: Reinstall URL Rewrite + ARR ───
echo [4/7] Reinstalling URL Rewrite module...
if exist "C:\temp-setup\urlrewrite.msi" (
    msiexec /i "C:\temp-setup\urlrewrite.msi" /qn /norestart
) else (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi' -OutFile 'C:\temp-setup\urlrewrite.msi' -UseBasicParsing; Start-Process msiexec.exe -ArgumentList '/i C:\temp-setup\urlrewrite.msi /qn /norestart' -Wait"
)
echo       URL Rewrite installed.

echo       Installing ARR...
if exist "C:\temp-setup\arr.msi" (
    msiexec /i "C:\temp-setup\arr.msi" /qn /norestart
) else (
    if not exist "C:\temp-setup" mkdir "C:\temp-setup"
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://download.microsoft.com/download/E/9/8/E9849D6A-020E-47E4-9FD0-A023E99B54EB/requestRouter_amd64.msi' -OutFile 'C:\temp-setup\arr.msi' -UseBasicParsing; Start-Process msiexec.exe -ArgumentList '/i C:\temp-setup\arr.msi /qn /norestart' -Wait"
)
echo       ARR installed.
echo.

REM ─── Step 5: Enable ARR proxy ───
echo [5/7] Enabling ARR proxy...
"%windir%\system32\inetsrv\appcmd.exe" set config -section:system.webServer/proxy /enabled:true /preserveHostHeader:true /commit:apphost
if %ERRORLEVEL% EQU 0 (
    echo       ARR proxy enabled.
) else (
    echo       appcmd proxy enable failed. Will try after iisreset.
    iisreset /restart
    timeout /t 3 /nobreak >nul
    "%windir%\system32\inetsrv\appcmd.exe" set config -section:system.webServer/proxy /enabled:true /preserveHostHeader:true /commit:apphost
)
echo.

REM ─── Step 6: Create site ───
echo [6/7] Creating EmbraceAI IIS site...
copy /y "C:\apps\embrace-ai\deploy\iis\web.config" "C:\inetpub\embrace-ai\web.config"
powershell -Command "Import-Module WebAdministration; Stop-Website -Name 'Default Web Site' -ErrorAction SilentlyContinue; New-Website -Name 'EmbraceAI' -PhysicalPath 'C:\inetpub\embrace-ai' -Port 80 -Force | Out-Null; Start-Website -Name 'EmbraceAI'; Write-Host '      Site created on port 80.' -ForegroundColor Green"
echo.

REM ─── Step 7: Open firewall + verify ───
echo [7/7] Final verification...
netsh advfirewall firewall add rule name="EmbraceAI HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
timeout /t 2 /nobreak >nul
powershell -Command ^
  "Write-Host '  Checking Node.js (port 3000)...' -ForegroundColor Cyan;" ^
  "try { Invoke-WebRequest -Uri 'http://localhost:3000/api/members' -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '      Node.js: OK' -ForegroundColor Green } catch { Write-Host '      Node.js not running! Starting service...' -ForegroundColor Yellow; C:\tools\nssm\nssm.exe start EmbraceAI; Start-Sleep 3 };" ^
  "Write-Host '  Checking IIS proxy (port 80)...' -ForegroundColor Cyan;" ^
  "try {" ^
  "  $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10;" ^
  "  Write-Host '';" ^
  "  Write-Host '  ╔══════════════════════════════════════════╗' -ForegroundColor Green;" ^
  "  Write-Host '  ║  SUCCESS! Everything is working!         ║' -ForegroundColor Green;" ^
  "  Write-Host '  ║                                          ║' -ForegroundColor Green;" ^
  "  Write-Host '  ║  http://SN1W7220.AD001.SIEMENS.NET       ║' -ForegroundColor Green;" ^
  "  Write-Host '  ║                                          ║' -ForegroundColor Green;" ^
  "  Write-Host '  ╚══════════════════════════════════════════╝' -ForegroundColor Green;" ^
  "} catch {" ^
  "  Write-Host '  IIS proxy not forwarding. Last resort:' -ForegroundColor Yellow;" ^
  "  Write-Host '    1. Open IIS Manager' -ForegroundColor Yellow;" ^
  "  Write-Host '    2. Click server name' -ForegroundColor Yellow;" ^
  "  Write-Host '    3. Double-click Application Request Routing Cache' -ForegroundColor Yellow;" ^
  "  Write-Host '    4. Click Server Proxy Settings (right panel)' -ForegroundColor Yellow;" ^
  "  Write-Host '    5. Tick Enable proxy > Apply' -ForegroundColor Yellow;" ^
  "  Write-Host '    6. Browse http://localhost — should work now' -ForegroundColor Yellow;" ^
  "}"
echo.
pause

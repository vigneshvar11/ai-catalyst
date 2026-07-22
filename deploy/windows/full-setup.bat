@echo off
REM ═══════════════════════════════════════════════════════════
REM  EMBRACE AI — One-Click Server Setup
REM  Run this as Administrator on SN1W7220.AD001.SIEMENS.NET
REM
REM  What it does:
REM    1. Downloads & installs Node.js 20 LTS (silently)
REM    2. Downloads & installs URL Rewrite for IIS
REM    3. Downloads & installs Application Request Routing (ARR)
REM    4. Downloads & installs NSSM (service manager)
REM    5. Clones the repo from code.siemens.com
REM    6. Installs npm dependencies
REM    7. Registers Node.js as Windows Service "EmbraceAI"
REM    8. Configures IIS reverse proxy site
REM    9. Opens firewall port 80
REM
REM  After this finishes, open: http://SN1W7220.AD001.SIEMENS.NET
REM ═══════════════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  EMBRACE AI — Full Server Setup                  ║
echo  ║  This will take 5-10 minutes. Sit back.         ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ─── Create directories ───
echo [1/9] Creating directories...
if not exist "C:\apps\embrace-ai" mkdir "C:\apps\embrace-ai"
if not exist "C:\inetpub\embrace-ai" mkdir "C:\inetpub\embrace-ai"
if not exist "C:\tools\nssm" mkdir "C:\tools\nssm"
if not exist "C:\temp-setup" mkdir "C:\temp-setup"
echo       Done.
echo.

REM ─── Install Node.js ───
echo [2/9] Downloading Node.js 20 LTS...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi' -OutFile 'C:\temp-setup\node-setup.msi' -UseBasicParsing"
echo       Installing Node.js (silent)...
msiexec /i "C:\temp-setup\node-setup.msi" /qn /norestart
echo       Node.js installed.
echo.

REM Refresh PATH so node/npm are available
set "PATH=%PATH%;C:\Program Files\nodejs"

REM Verify
echo       Verifying Node.js...
"C:\Program Files\nodejs\node.exe" --version
echo.

REM ─── Install URL Rewrite Module ───
echo [3/9] Downloading IIS URL Rewrite Module...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi' -OutFile 'C:\temp-setup\urlrewrite.msi' -UseBasicParsing"
echo       Installing URL Rewrite...
msiexec /i "C:\temp-setup\urlrewrite.msi" /qn /norestart
echo       URL Rewrite installed.
echo.

REM ─── Install ARR ───
echo [4/9] Downloading Application Request Routing (ARR)...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://download.microsoft.com/download/E/9/8/E9849D6A-020E-47E4-9FD0-A023E99B54EB/requestRouter_amd64.msi' -OutFile 'C:\temp-setup\arr.msi' -UseBasicParsing"
echo       Installing ARR...
msiexec /i "C:\temp-setup\arr.msi" /qn /norestart
echo       ARR installed.
echo.

REM Enable ARR Proxy
echo       Enabling ARR proxy in IIS...
powershell -Command "Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' -filter 'system.webServer/proxy' -name 'enabled' -value 'true' -ErrorAction SilentlyContinue; Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' -filter 'system.webServer/proxy' -name 'preserveHostHeader' -value 'true' -ErrorAction SilentlyContinue"
echo       ARR proxy enabled.
echo.

REM ─── Install IIS WebSocket feature ───
echo [5/9] Enabling IIS WebSocket Protocol...
powershell -Command "Install-WindowsFeature Web-WebSockets -ErrorAction SilentlyContinue"
echo       WebSocket enabled.
echo.

REM ─── Install NSSM ───
echo [6/9] Downloading NSSM (service manager)...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'C:\temp-setup\nssm.zip' -UseBasicParsing; Expand-Archive -Path 'C:\temp-setup\nssm.zip' -DestinationPath 'C:\temp-setup\nssm-extract' -Force; Copy-Item 'C:\temp-setup\nssm-extract\nssm-2.24\win64\nssm.exe' 'C:\tools\nssm\nssm.exe' -Force"
set "PATH=%PATH%;C:\tools\nssm"
echo       NSSM installed to C:\tools\nssm\nssm.exe
echo.

REM ─── Clone the repository ───
echo [7/9] Cloning repository from code.siemens.com...
echo       (You may be prompted for credentials)
echo       Username: your Siemens GID
echo       Password: your GitLab access token or Siemens password
echo.
cd /d "C:\apps"
if exist "C:\apps\embrace-ai\.git" (
    echo       Repo already cloned. Pulling latest...
    cd /d "C:\apps\embrace-ai"
    git pull
) else (
    rmdir /s /q "C:\apps\embrace-ai" 2>nul
    git clone https://code.siemens.com/engsys/ai_catalyest.git embrace-ai
    cd /d "C:\apps\embrace-ai"
)
echo       Repository ready.
echo.

REM ─── Install npm dependencies ───
echo [8/9] Installing Node.js dependencies (npm install)...
cd /d "C:\apps\embrace-ai"
"C:\Program Files\nodejs\npm.cmd" install --production
echo       Dependencies installed.
echo.

REM ─── Create Windows Service + IIS Site ───
echo [9/9] Setting up Windows Service and IIS site...

REM Stop existing service if running
C:\tools\nssm\nssm.exe stop EmbraceAI 2>nul
C:\tools\nssm\nssm.exe remove EmbraceAI confirm 2>nul

REM Create logs directory
if not exist "C:\apps\embrace-ai\logs" mkdir "C:\apps\embrace-ai\logs"

REM Install service
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

REM Start the service
C:\tools\nssm\nssm.exe start EmbraceAI
echo       Service "EmbraceAI" started.

REM Wait for Node to boot
timeout /t 3 /nobreak >nul

REM Copy IIS web.config
copy /y "C:\apps\embrace-ai\deploy\iis\web.config" "C:\inetpub\embrace-ai\web.config"

REM Create IIS site via PowerShell
powershell -Command "Import-Module WebAdministration; Stop-Website -Name 'Default Web Site' -ErrorAction SilentlyContinue; Remove-Website -Name 'EmbraceAI' -ErrorAction SilentlyContinue; New-Website -Name 'EmbraceAI' -PhysicalPath 'C:\inetpub\embrace-ai' -Port 80 -Force | Out-Null; Start-Website -Name 'EmbraceAI'"
echo       IIS site created on port 80.

REM Open firewall
netsh advfirewall firewall add rule name="EmbraceAI HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
echo       Firewall rule added.
echo.

REM ─── DONE ───
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║   Setup Complete!                                ║
echo  ║                                                  ║
echo  ║   Open in browser:                               ║
echo  ║   http://SN1W7220.AD001.SIEMENS.NET              ║
echo  ║                                                  ║
echo  ║   Admin: admin / admin                           ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM Clean up temp files
rmdir /s /q "C:\temp-setup" 2>nul

REM Verify
echo Verifying...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost/api/members' -UseBasicParsing -TimeoutSec 10; Write-Host '  API Status:' $r.StatusCode '- SUCCESS!' -ForegroundColor Green } catch { Write-Host '  API not responding yet. Wait 10 seconds and try http://localhost in browser.' -ForegroundColor Yellow }"
echo.
pause

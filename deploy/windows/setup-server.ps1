#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Sets up the Windows Server (SN1W7220.AD001.SIEMENS.NET) to host EMBRACE AI.

.DESCRIPTION
    Installs Node.js, IIS features, URL Rewrite, ARR, and NSSM.
    Run this ONCE on the server via an elevated PowerShell prompt.

.NOTES
    Server: SN1W7220.AD001.SIEMENS.NET
    Accounts: uawet39j / w99sjt30
#>

$ErrorActionPreference = "Stop"

Write-Host "`n=== EMBRACE AI — Server Setup ===" -ForegroundColor Cyan
Write-Host "Server: $env:COMPUTERNAME`n"

# ──────────────────────────────────────────────
# 1. INSTALL IIS + REQUIRED FEATURES
# ──────────────────────────────────────────────
Write-Host "[1/5] Installing IIS features..." -ForegroundColor Yellow

$features = @(
    "Web-Server",
    "Web-WebServer",
    "Web-Common-Http",
    "Web-Default-Doc",
    "Web-Static-Content",
    "Web-Http-Errors",
    "Web-Http-Logging",
    "Web-Request-Monitor",
    "Web-Filtering",
    "Web-Performance",
    "Web-Stat-Compression",
    "Web-Dyn-Compression",
    "Web-Mgmt-Console",
    "Web-WebSockets"         # Critical: needed for Socket.IO
)

foreach ($f in $features) {
    $installed = Get-WindowsFeature -Name $f -ErrorAction SilentlyContinue
    if ($installed -and -not $installed.Installed) {
        Install-WindowsFeature -Name $f -IncludeManagementTools
        Write-Host "  Installed: $f" -ForegroundColor Green
    } else {
        Write-Host "  Already installed: $f" -ForegroundColor DarkGray
    }
}

# ──────────────────────────────────────────────
# 2. INSTALL NODE.JS (LTS)
# ──────────────────────────────────────────────
Write-Host "`n[2/5] Checking Node.js..." -ForegroundColor Yellow

$nodeInstalled = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeInstalled) {
    Write-Host "  Node.js not found. Downloading Node.js LTS installer..."
    $nodeUrl = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi"
    $nodeInstaller = "$env:TEMP\node-lts.msi"
    
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller -UseBasicParsing
    
    Write-Host "  Installing Node.js (this may take a minute)..."
    Start-Process msiexec.exe -ArgumentList "/i `"$nodeInstaller`" /qn" -Wait -NoNewWindow
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Host "  Node.js installed: $(node --version)" -ForegroundColor Green
} else {
    Write-Host "  Node.js already installed: $(node --version)" -ForegroundColor DarkGray
}

# ──────────────────────────────────────────────
# 3. INSTALL URL REWRITE + ARR FOR IIS
# ──────────────────────────────────────────────
Write-Host "`n[3/5] Installing IIS URL Rewrite & ARR modules..." -ForegroundColor Yellow

# URL Rewrite 2.1
$urlRewriteUrl = "https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi"
$urlRewriteInstaller = "$env:TEMP\urlrewrite.msi"

if (-not (Test-Path "HKLM:\SOFTWARE\Microsoft\IIS Extensions\URL Rewrite")) {
    Write-Host "  Downloading URL Rewrite Module..."
    Invoke-WebRequest -Uri $urlRewriteUrl -OutFile $urlRewriteInstaller -UseBasicParsing
    Start-Process msiexec.exe -ArgumentList "/i `"$urlRewriteInstaller`" /qn" -Wait -NoNewWindow
    Write-Host "  URL Rewrite Module installed" -ForegroundColor Green
} else {
    Write-Host "  URL Rewrite already installed" -ForegroundColor DarkGray
}

# Application Request Routing (ARR) 3.0
$arrUrl = "https://download.microsoft.com/download/E/9/8/E9849D6A-020E-47E4-9FD0-A023E99B54EB/requestRouter_amd64.msi"
$arrInstaller = "$env:TEMP\arr.msi"

$arrKey = "HKLM:\SOFTWARE\Microsoft\IIS Extensions\Application Request Routing"
if (-not (Test-Path $arrKey)) {
    Write-Host "  Downloading Application Request Routing..."
    Invoke-WebRequest -Uri $arrUrl -OutFile $arrInstaller -UseBasicParsing
    Start-Process msiexec.exe -ArgumentList "/i `"$arrInstaller`" /qn" -Wait -NoNewWindow
    Write-Host "  ARR installed" -ForegroundColor Green
} else {
    Write-Host "  ARR already installed" -ForegroundColor DarkGray
}

# Enable ARR proxy
Write-Host "  Enabling ARR proxy..."
try {
    Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
        -filter "system.webServer/proxy" -name "enabled" -value "true"
    # Preserve host header for proper Socket.IO routing
    Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' `
        -filter "system.webServer/proxy" -name "preserveHostHeader" -value "true"
    Write-Host "  ARR proxy enabled" -ForegroundColor Green
} catch {
    Write-Host "  ARR proxy config may need manual enabling in IIS Manager" -ForegroundColor Yellow
}

# ──────────────────────────────────────────────
# 4. INSTALL NSSM (Non-Sucking Service Manager)
# ──────────────────────────────────────────────
Write-Host "`n[4/5] Installing NSSM (to run Node.js as a Windows Service)..." -ForegroundColor Yellow

$nssmPath = "C:\tools\nssm\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$env:TEMP\nssm.zip"
    $nssmExtract = "$env:TEMP\nssm-extract"
    
    Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
    Expand-Archive -Path $nssmZip -DestinationPath $nssmExtract -Force
    
    New-Item -ItemType Directory -Path "C:\tools\nssm" -Force | Out-Null
    Copy-Item "$nssmExtract\nssm-2.24\win64\nssm.exe" $nssmPath
    
    # Add to PATH
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($machinePath -notlike "*C:\tools\nssm*") {
        [System.Environment]::SetEnvironmentVariable("Path", "$machinePath;C:\tools\nssm", "Machine")
        $env:Path += ";C:\tools\nssm"
    }
    Write-Host "  NSSM installed to $nssmPath" -ForegroundColor Green
} else {
    Write-Host "  NSSM already installed" -ForegroundColor DarkGray
}

# ──────────────────────────────────────────────
# 5. CREATE APP DIRECTORY
# ──────────────────────────────────────────────
Write-Host "`n[5/5] Creating application directory..." -ForegroundColor Yellow

$appDir = "C:\apps\embrace-ai"
$iisDir = "C:\inetpub\embrace-ai"

New-Item -ItemType Directory -Path $appDir -Force | Out-Null
New-Item -ItemType Directory -Path $iisDir -Force | Out-Null

Write-Host "  App directory: $appDir" -ForegroundColor Green
Write-Host "  IIS site root: $iisDir" -ForegroundColor Green

# ──────────────────────────────────────────────
# DONE
# ──────────────────────────────────────────────
Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host @"

Next steps:
  1. Clone the repo:
       cd C:\apps\embrace-ai
       git clone https://code.siemens.com/YOUR_GROUP/embrace-ai.git .

  2. Install dependencies:
       npm install

  3. Run the install-service script:
       .\deploy\windows\install-service.ps1

  4. Copy IIS config:
       Copy-Item .\deploy\iis\web.config C:\inetpub\embrace-ai\web.config

  5. Create IIS site (or run create-iis-site.ps1)

"@

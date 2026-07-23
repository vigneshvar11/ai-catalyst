#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Sets up the Windows Server (SN1W7220.AD001.SIEMENS.NET) to host EMBRACE AI.

.DESCRIPTION
    Installs Node.js and NSSM for direct Node.js hosting on port 80.
    Run this ONCE on the server via an elevated PowerShell prompt.

.NOTES
    Server: SN1W7220.AD001.SIEMENS.NET
    Accounts: uawet39j / w99sjt30
#>

$ErrorActionPreference = "Stop"

Write-Host "`n=== EMBRACE AI - Server Setup ===" -ForegroundColor Cyan
Write-Host ('Server: ' + $env:COMPUTERNAME)
Write-Host ""

# ──────────────────────────────────────────────
# 1. INSTALL NODE.JS (LTS)
# ──────────────────────────────────────────────
Write-Host "[1/3] Checking Node.js..." -ForegroundColor Yellow

$nodeInstalled = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeInstalled) {
    Write-Host "  Node.js not found. Downloading Node.js LTS installer..."
    $nodeUrl = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi"
    $nodeInstaller = "$env:TEMP\node-lts.msi"
    
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller -UseBasicParsing
    
    Write-Host "  Installing Node.js (this may take a minute)..."
    Start-Process msiexec.exe -ArgumentList '/i', $nodeInstaller, '/qn' -Wait -NoNewWindow
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
    
    Write-Host ('  Node.js installed: ' + (node --version)) -ForegroundColor Green
} else {
    Write-Host ('  Node.js already installed: ' + (node --version)) -ForegroundColor DarkGray
}

# ──────────────────────────────────────────────
# 2. INSTALL NSSM (Non-Sucking Service Manager)
# ──────────────────────────────────────────────
Write-Host "`n[2/3] Installing NSSM (to run Node.js as a Windows Service)..." -ForegroundColor Yellow

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
# 3. CREATE APP DIRECTORY
# ──────────────────────────────────────────────
Write-Host "`n[3/3] Creating application directory..." -ForegroundColor Yellow

$appDir = "C:\apps\embrace-ai"

New-Item -ItemType Directory -Path $appDir -Force | Out-Null

Write-Host "  App directory: $appDir" -ForegroundColor Green

# ──────────────────────────────────────────────
# DONE
# ──────────────────────────────────────────────
Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host 'Next steps:'
Write-Host '  1. Clone the repo:'
Write-Host '       cd C:\apps\embrace-ai'
Write-Host '       git clone https://code.siemens.com/YOUR_GROUP/embrace-ai.git .'
Write-Host ''
Write-Host '  2. Install dependencies:'
Write-Host '       npm install'
Write-Host ''
Write-Host '  3. Run the install-service script:'
Write-Host '       .\deploy\windows\install-service.ps1'
Write-Host ''
Write-Host '  4. Switch the service to direct hosting on port 80:'
Write-Host '       .\deploy\windows\switch-to-direct.bat'

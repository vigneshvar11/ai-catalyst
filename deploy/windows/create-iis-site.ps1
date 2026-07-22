#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Creates the IIS site for EMBRACE AI (reverse proxy to Node.js on port 3000).

.DESCRIPTION
    Creates an IIS website that proxies all requests (including WebSocket)
    to the Node.js app running as a Windows Service on localhost:3000.

.NOTES
    Run after: setup-server.ps1, install-service.ps1
    Server: SN1W7220.AD001.SIEMENS.NET
#>

Import-Module WebAdministration -ErrorAction Stop
$ErrorActionPreference = "Stop"

$SiteName = "EmbraceAI"
$IISRoot = "C:\inetpub\embrace-ai"
$AppRoot = "C:\apps\embrace-ai"
$Port = 80   # Change to 443 if using HTTPS with a certificate

Write-Host "`n=== Creating IIS Site: $SiteName ===" -ForegroundColor Cyan

# Ensure IIS root directory exists and has the web.config
New-Item -ItemType Directory -Path $IISRoot -Force | Out-Null

$webConfigSrc = "$AppRoot\deploy\iis\web.config"
$webConfigDst = "$IISRoot\web.config"

if (Test-Path $webConfigSrc) {
    Copy-Item $webConfigSrc $webConfigDst -Force
    Write-Host "  Copied web.config to $IISRoot" -ForegroundColor Green
} else {
    Write-Error "web.config not found at $webConfigSrc"
    exit 1
}

# Remove Default Web Site if it's on port 80 (optional)
$defaultSite = Get-Website -Name "Default Web Site" -ErrorAction SilentlyContinue
if ($defaultSite) {
    Write-Host "  Stopping Default Web Site (port conflict)..." -ForegroundColor Yellow
    Stop-Website -Name "Default Web Site" -ErrorAction SilentlyContinue
}

# Remove existing EmbraceAI site if it exists
$existingSite = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
if ($existingSite) {
    Write-Host "  Removing existing '$SiteName' site..." -ForegroundColor Yellow
    Remove-Website -Name $SiteName
}

# Create the site
Write-Host "  Creating IIS site '$SiteName' on port $Port..." -ForegroundColor Yellow
New-Website -Name $SiteName `
    -PhysicalPath $IISRoot `
    -Port $Port `
    -Force | Out-Null

# Start the site
Start-Website -Name $SiteName
Write-Host "  IIS site '$SiteName' is RUNNING on port $Port" -ForegroundColor Green

# Verify connectivity
Write-Host "`n  Testing connectivity..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/members" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "  API responding via IIS reverse proxy!" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not reach API. Make sure the EmbraceAI service is running:" -ForegroundColor Yellow
    Write-Host "    nssm status EmbraceAI" -ForegroundColor Yellow
}

Write-Host @"

=== Setup Complete ===

Your app is now accessible at:
  Internal: http://SN1W7220.AD001.SIEMENS.NET
  Local:    http://localhost

Architecture:
  Browser → IIS (port $Port) → reverse proxy → Node.js (port 3000)
  WebSocket connections are proxied through IIS automatically.

To verify:
  1. Open http://SN1W7220.AD001.SIEMENS.NET in a browser
  2. Log in as admin (admin/admin)
  3. Test real-time features (create a quiz, launch a survey)

"@

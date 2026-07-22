#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Pulls the latest code from code.siemens.com and restarts the service.

.DESCRIPTION
    Quick deployment script: git pull → npm install → restart service.
    Use this whenever you push changes to the repo.
#>

$ErrorActionPreference = "Stop"
$AppDir = "C:\apps\embrace-ai"
$ServiceName = "EmbraceAI"
$NssmPath = "C:\tools\nssm\nssm.exe"

Write-Host "`n=== Updating EMBRACE AI ===" -ForegroundColor Cyan

Push-Location $AppDir

# Pull latest changes
Write-Host "  Pulling latest from code.siemens.com..." -ForegroundColor Yellow
git pull origin main

# Install any new dependencies
Write-Host "  Installing dependencies..." -ForegroundColor Yellow
npm install --production

# Restart the service
Write-Host "  Restarting service..." -ForegroundColor Yellow
& $NssmPath restart $ServiceName

Start-Sleep -Seconds 3
$svc = Get-Service -Name $ServiceName
Write-Host "  Service status: $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq "Running") { "Green" } else { "Red" })

Pop-Location

Write-Host "`n  Update complete!`n" -ForegroundColor Cyan

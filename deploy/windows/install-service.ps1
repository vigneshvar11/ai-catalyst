#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Registers the EMBRACE AI Node.js app as a Windows Service using NSSM.

.DESCRIPTION
    Creates a service named "EmbraceAI" that auto-starts with the server.
    The service runs node server.js from C:\apps\embrace-ai on a dedicated
    app port (default: 8080) to avoid IIS/port-80 conflicts.
#>

$ErrorActionPreference = 'Stop'
$ServiceName = 'EmbraceAI'
$AppDir = 'C:\apps\embrace-ai'
$NodePath = (Get-Command node).Source
$NssmPath = 'C:\tools\nssm\nssm.exe'
$DefaultPort = if ($env:EMBRACE_AI_PORT) { $env:EMBRACE_AI_PORT } else { '8080' }

if ($DefaultPort -notmatch '^\d+$') {
    Write-Error ('Invalid EMBRACE_AI_PORT value: ' + $DefaultPort)
    exit 1
}

Write-Host ''
Write-Host '=== Installing EmbraceAI as Windows Service ===' -ForegroundColor Cyan

if (-not (Test-Path ($AppDir + '\server.js'))) {
    Write-Error ('server.js not found at ' + $AppDir + '\server.js - clone the repo first.')
    exit 1
}

if (-not (Test-Path ($AppDir + '\node_modules'))) {
    Write-Error ('node_modules not found - run npm install in ' + $AppDir + ' first.')
    exit 1
}

if (-not (Test-Path $NssmPath)) {
    Write-Error ('NSSM not found at ' + $NssmPath + ' - run setup-server.ps1 first.')
    exit 1
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host '  Stopping existing service...' -ForegroundColor Yellow
    & $NssmPath stop $ServiceName 2>$null
    & $NssmPath remove $ServiceName confirm
    Write-Host '  Removed existing service' -ForegroundColor DarkGray
}

Write-Host ('  Creating service ' + $ServiceName + '...') -ForegroundColor Yellow
& $NssmPath install $ServiceName $NodePath ($AppDir + '\server.js')

& $NssmPath set $ServiceName AppDirectory $AppDir
& $NssmPath set $ServiceName DisplayName 'EMBRACE AI Dashboard'
& $NssmPath set $ServiceName Description 'EMBRACE AI - Engineering Systems Initiative Dashboard (Node.js + Socket.IO)'
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

$LogDir = ($AppDir + '\logs')
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
& $NssmPath set $ServiceName AppStdout ($LogDir + '\embrace-ai-stdout.log')
& $NssmPath set $ServiceName AppStderr ($LogDir + '\embrace-ai-stderr.log')
& $NssmPath set $ServiceName AppStdoutCreationDisposition 4
& $NssmPath set $ServiceName AppStderrCreationDisposition 4
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateBytes 5242880

& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 5000
& $NssmPath set $ServiceName AppEnvironmentExtra 'NODE_ENV=production' ('PORT=' + $DefaultPort)

Write-Host '  Starting service...' -ForegroundColor Yellow
& $NssmPath start $ServiceName

Start-Sleep -Seconds 3
$svc = Get-Service -Name $ServiceName
if ($svc.Status -eq 'Running') {
    Write-Host ('`n  Service ' + $ServiceName + ' is RUNNING') -ForegroundColor Green
    Write-Host ('  App available at: http://localhost:' + $DefaultPort) -ForegroundColor Green
} else {
    Write-Host ('`n  Service status: ' + $svc.Status) -ForegroundColor Red
    Write-Host ('  Check logs at: ' + $LogDir) -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Service management commands:'
Write-Host '  nssm start EmbraceAI - Start the service'
Write-Host '  nssm stop EmbraceAI - Stop the service'
Write-Host '  nssm restart EmbraceAI - Restart the service'
Write-Host '  nssm status EmbraceAI - Check status'
Write-Host '  nssm edit EmbraceAI - Edit service config (GUI)'
#Requires -RunAsAdministrator
param(
    [string]$AppDir = 'C:\apps\embrace-ai',
    [string]$RenderPointsUrl = 'https://ai-catalyest.onrender.com/api/points',
    [string]$ServiceName = 'EmbraceAI'
)

$ErrorActionPreference = 'Stop'

$DbPath = Join-Path $AppDir 'data\db.json'
$BackupsDir = Join-Path $AppDir 'backups'
$NssmPath = 'C:\tools\nssm\nssm.exe'

Write-Host ''
Write-Host '=== Sync Points From Render ===' -ForegroundColor Cyan
Write-Host ('App directory: ' + $AppDir)
Write-Host ('Render points URL: ' + $RenderPointsUrl)

if (-not (Test-Path $DbPath)) {
    throw ('db.json not found at ' + $DbPath)
}

if (-not (Test-Path $NssmPath)) {
    throw ('NSSM not found at ' + $NssmPath)
}

New-Item -ItemType Directory -Path $BackupsDir -Force | Out-Null

# 1) Safety backup of current db.json
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupPath = Join-Path $BackupsDir ('db-before-render-points-' + $stamp + '.json')
Copy-Item $DbPath $backupPath -Force
Write-Host ('Backed up current db.json to: ' + $backupPath) -ForegroundColor Green

# 2) Fetch Render points
$renderPoints = (Invoke-WebRequest -Uri $RenderPointsUrl -UseBasicParsing -TimeoutSec 30).Content | ConvertFrom-Json
Write-Host ('Fetched points from Render: ' + @($renderPoints).Count) -ForegroundColor Green

# 3) Inject into local db.json
$db = Get-Content $DbPath -Raw | ConvertFrom-Json
if (-not ($db.PSObject.Properties.Name -contains 'points')) {
    throw 'Local db.json does not contain a points collection.'
}

$db.points = @($renderPoints)
$db | ConvertTo-Json -Depth 100 | Set-Content $DbPath -Encoding UTF8
Write-Host ('Imported points entries: ' + @($db.points).Count) -ForegroundColor Green

# 4) Restart service
& $NssmPath restart $ServiceName
if ($LASTEXITCODE -ne 0) {
    throw ('Failed to restart service ' + $ServiceName)
}
Write-Host ('Service restarted: ' + $ServiceName) -ForegroundColor Green

# 5) Verify leaderboard and points endpoints
$lb = Invoke-WebRequest -Uri 'http://localhost/api/leaderboard' -UseBasicParsing -TimeoutSec 15
$pts = Invoke-WebRequest -Uri 'http://localhost/api/points' -UseBasicParsing -TimeoutSec 15

$lbCount = @(($lb.Content | ConvertFrom-Json)).Count
$ptsCount = @(($pts.Content | ConvertFrom-Json)).Count

Write-Host ''
Write-Host ('Leaderboard API status: ' + $lb.StatusCode) -ForegroundColor Green
Write-Host ('Points API status: ' + $pts.StatusCode) -ForegroundColor Green
Write-Host ('Leaderboard rows: ' + $lbCount) -ForegroundColor Green
Write-Host ('Points rows: ' + $ptsCount) -ForegroundColor Green
Write-Host ''
Write-Host 'Done. Refresh the browser to see updated leaderboard values.' -ForegroundColor Cyan

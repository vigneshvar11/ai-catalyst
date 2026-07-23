#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Creates a backup of the live EMBRACE AI data before updates.

.DESCRIPTION
    Saves a timestamped copy of data/db.json and uploads/avatars to the
    backups folder so changes can be restored if a deploy goes wrong.
#>

$ErrorActionPreference = 'Stop'
$AppDir = 'C:\apps\embrace-ai'
$BackupRoot = Join-Path $AppDir 'backups'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $BackupRoot $Stamp
$DataDir = Join-Path $AppDir 'data'
$UploadDir = Join-Path $AppDir 'uploads\avatars'

Write-Host ''
Write-Host '=== Backing up EMBRACE AI data ===' -ForegroundColor Cyan

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

if (Test-Path (Join-Path $DataDir 'db.json')) {
    Copy-Item (Join-Path $DataDir 'db.json') (Join-Path $BackupDir 'db.json') -Force
    Write-Host '  Backed up db.json' -ForegroundColor Green
} else {
    Write-Host '  db.json not found - skipping data backup' -ForegroundColor Yellow
}

if (Test-Path $UploadDir) {
    $AvatarBackup = Join-Path $BackupDir 'avatars'
    Copy-Item $UploadDir $AvatarBackup -Recurse -Force
    Write-Host '  Backed up avatar uploads' -ForegroundColor Green
} else {
    Write-Host '  Avatar upload folder not found - skipping avatar backup' -ForegroundColor Yellow
}

$manifest = @{
    createdAt = (Get-Date).ToString('o')
    appDir = $AppDir
    backupDir = $BackupDir
    files = @('data/db.json', 'uploads/avatars')
} | ConvertTo-Json -Depth 5

Set-Content -Path (Join-Path $BackupDir 'manifest.json') -Value $manifest -Encoding UTF8

Write-Host ('  Backup created at: ' + $BackupDir) -ForegroundColor Cyan
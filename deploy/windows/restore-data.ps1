#Requires -RunAsAdministrator
param(
    [string]$BackupPath
)

<#
.SYNOPSIS
    Restores a previous EMBRACE AI data backup.

.DESCRIPTION
    Restores db.json and avatar uploads from a chosen backup folder.
    By default, restores the most recent backup in C:\apps\embrace-ai\backups.
#>

$ErrorActionPreference = 'Stop'
$AppDir = 'C:\apps\embrace-ai'
$BackupRoot = Join-Path $AppDir 'backups'
$DataDir = Join-Path $AppDir 'data'
$UploadDir = Join-Path $AppDir 'uploads\avatars'

if (-not $BackupPath) {
    $BackupPath = Get-ChildItem -Path $BackupRoot -Directory |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $BackupPath -or -not (Test-Path $BackupPath)) {
    throw 'No backup folder found. Pass -BackupPath or create one with backup-data.ps1.'
}

Write-Host ''
Write-Host '=== Restoring EMBRACE AI data ===' -ForegroundColor Cyan
Write-Host ('  Backup: ' + $BackupPath) -ForegroundColor Yellow

$backupDb = Join-Path $BackupPath 'db.json'
if (Test-Path $backupDb) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    Copy-Item $backupDb (Join-Path $DataDir 'db.json') -Force
    Write-Host '  Restored db.json' -ForegroundColor Green
} else {
    Write-Host '  db.json not found in backup - skipping' -ForegroundColor Yellow
}

$backupAvatars = Join-Path $BackupPath 'avatars'
if (Test-Path $backupAvatars) {
    New-Item -ItemType Directory -Path $UploadDir -Force | Out-Null
    Copy-Item (Join-Path $backupAvatars '*') $UploadDir -Recurse -Force
    Write-Host '  Restored avatar uploads' -ForegroundColor Green
} else {
    Write-Host '  Avatar folder not found in backup - skipping' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Restart the service after restoring data:' -ForegroundColor Cyan
Write-Host '  nssm restart EmbraceAI'
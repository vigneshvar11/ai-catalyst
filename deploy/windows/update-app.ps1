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
$DbRelPath = "data/db.json"
$DbTempPath = "data/db.server-live.json"

function Resolve-NpmPath {
    $cmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallbacks = @(
        'C:\Program Files\nodejs\npm.cmd',
        'C:\Program Files (x86)\nodejs\npm.cmd'
    )
    foreach ($p in $fallbacks) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Restart-ServiceSafe {
    param([string]$Nssm, [string]$Name)

    Write-Host "  Restarting service..." -ForegroundColor Yellow
    & $Nssm restart $Name 2>$null
    Start-Sleep -Seconds 2

    $svc = Get-Service -Name $Name
    if ($svc.Status -eq 'Paused') {
        sc.exe continue $Name | Out-Null
        Start-Sleep -Seconds 2
        $svc = Get-Service -Name $Name
    }
    if ($svc.Status -ne 'Running') {
        & $Nssm stop $Name 2>$null
        Start-Sleep -Seconds 2
        & $Nssm start $Name 2>$null
        Start-Sleep -Seconds 3
        $svc = Get-Service -Name $Name
    }
    return $svc
}

Write-Host "`n=== Updating EMBRACE AI ===" -ForegroundColor Cyan

Push-Location $AppDir

try {
    if (Test-Path $DbTempPath) {
        Remove-Item $DbTempPath -Force
    }

    # Back up live data before pulling new code
    Write-Host "  Creating data backup..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File .\deploy\windows\backup-data.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Data backup failed. Aborting update."
    }

    # Resolve npm robustly (npm may not be on PATH in service/admin shells)
    $npmPath = Resolve-NpmPath
    if (-not $npmPath) {
        throw "npm.cmd not found. Run deploy\\windows\\setup-server.ps1 first."
    }

    # If db.json is locally modified (live runtime data), preserve it across pull.
    $dbDirty = ((git status --porcelain -- $DbRelPath) | Where-Object { $_.Trim() -ne '' }).Count -gt 0
    $localChanges = @(git status --porcelain)
    $ignoredLocalPatterns = @(
        '^\?\?\s+backups/',
        '^\?\?\s+package-lock\.json$'
    )
    $otherChanges = @($localChanges | Where-Object {
        $line = $_
        if ($line -match ('\s' + [regex]::Escape($DbRelPath) + '$')) { return $false }
        foreach ($pat in $ignoredLocalPatterns) {
            if ($line -match $pat) { return $false }
        }
        return ($line.Trim() -ne '')
    })
    if ($otherChanges.Count -gt 0) {
        Write-Host "  Local changes detected (outside data/db.json):" -ForegroundColor Yellow
        $otherChanges | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor Yellow }
        throw "Please commit/stash those local changes before update-app.ps1."
    }
    if ($dbDirty) {
        Write-Host "  Preserving local live data/db.json for this update..." -ForegroundColor Yellow
        Copy-Item $DbRelPath $DbTempPath -Force
        git restore --source=HEAD --worktree --staged -- $DbRelPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to reset data/db.json before git pull"
        }
    }

    # Pull latest changes
    $upstream = (git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null).Trim()
    if (-not $upstream) {
        $upstream = 'origin/master'
    }

    $remote = 'origin'
    $branch = 'master'
    if ($upstream -match '/') {
        $parts = $upstream.Split('/', 2)
        $remote = $parts[0]
        $branch = $parts[1]
    }

    Write-Host ("  Pulling latest from " + $upstream + "...") -ForegroundColor Yellow
    git pull --ff-only $remote $branch
    if ($LASTEXITCODE -ne 0) {
        throw ("git pull failed for " + $remote + " " + $branch)
    }

    # Restore live db.json after pull so runtime data is never overwritten.
    if (Test-Path $DbTempPath) {
        Copy-Item $DbTempPath $DbRelPath -Force
        Remove-Item $DbTempPath -Force
    }

    # Prevent future pull conflicts caused by runtime writes to db.json.
    git update-index --skip-worktree -- $DbRelPath 2>$null

    # Install any new dependencies
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    & $npmPath install --production
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed"
    }

    # Restart the service safely (handles paused/partial states)
    $svc = Restart-ServiceSafe -Nssm $NssmPath -Name $ServiceName
    Write-Host "  Service status: $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq "Running") { "Green" } else { "Red" })

    if ($svc.Status -ne "Running") {
        throw ("Failed to bring service " + $ServiceName + " to Running state")
    }
}
finally {
    if (Test-Path $DbTempPath) {
        Copy-Item $DbTempPath $DbRelPath -Force
        Remove-Item $DbTempPath -Force
    }
    Pop-Location
}

Write-Host "`n  Update complete!`n" -ForegroundColor Cyan

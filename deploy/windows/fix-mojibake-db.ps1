#Requires -RunAsAdministrator
param(
    [string]$AppDir = 'C:\apps\embrace-ai',
    [string]$ServiceName = 'EmbraceAI'
)

$ErrorActionPreference = 'Stop'

$DbPath = Join-Path $AppDir 'data\db.json'
$BackupsDir = Join-Path $AppDir 'backups'
$NssmPath = 'C:\tools\nssm\nssm.exe'
$Cp1252 = [System.Text.Encoding]::GetEncoding(1252)
$Utf8 = [System.Text.Encoding]::UTF8

function Test-LooksMojibake {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $false }

    $c3 = [char]0x00C3
    $c2 = [char]0x00C2
    $e2 = [char]0x00E2
    return $Text.Contains($c3) -or $Text.Contains($c2) -or $Text.Contains($e2)
}

function Repair-String {
    param([string]$Text)
    if (-not (Test-LooksMojibake -Text $Text)) {
        return $Text
    }

    try {
        $bytes = $Cp1252.GetBytes($Text)
        $fixed = $Utf8.GetString($bytes)
        if ([string]::IsNullOrEmpty($fixed)) {
            return $Text
        }
        return $fixed
    }
    catch {
        return $Text
    }
}

function Repair-Object {
    param(
        [AllowNull()]$Value,
        [ref]$FixCount
    )

    if ($null -eq $Value) { return $null }

    if ($Value -is [string]) {
        $newValue = Repair-String -Text $Value
        if ($newValue -ne $Value) {
            $FixCount.Value++
        }
        return $newValue
    }

    if ($Value -is [System.Collections.IList]) {
        for ($i = 0; $i -lt $Value.Count; $i++) {
            $Value[$i] = Repair-Object -Value $Value[$i] -FixCount $FixCount
        }
        return $Value
    }

    if ($Value -is [pscustomobject] -or $Value -is [hashtable]) {
        foreach ($prop in @($Value.PSObject.Properties)) {
            $Value.$($prop.Name) = Repair-Object -Value $prop.Value -FixCount $FixCount
        }
        return $Value
    }

    return $Value
}

Write-Host ''
Write-Host '=== Fix Mojibake In db.json ===' -ForegroundColor Cyan
Write-Host ('App directory: ' + $AppDir)

if (-not (Test-Path $DbPath)) {
    throw ('db.json not found at ' + $DbPath)
}

if (-not (Test-Path $NssmPath)) {
    throw ('NSSM not found at ' + $NssmPath)
}

New-Item -ItemType Directory -Path $BackupsDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupPath = Join-Path $BackupsDir ('db-before-mojibake-fix-' + $stamp + '.json')
Copy-Item $DbPath $backupPath -Force
Write-Host ('Backed up db.json to: ' + $backupPath) -ForegroundColor Green

$db = Get-Content $DbPath -Raw | ConvertFrom-Json
$fixCount = 0
$null = Repair-Object -Value $db -FixCount ([ref]$fixCount)

$json = $db | ConvertTo-Json -Depth 100
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($DbPath, $json, $utf8NoBom)

Write-Host ('String fixes applied: ' + $fixCount) -ForegroundColor Green

& $NssmPath restart $ServiceName
if ($LASTEXITCODE -ne 0) {
    throw ('Failed to restart service ' + $ServiceName)
}
Write-Host ('Service restarted: ' + $ServiceName) -ForegroundColor Green

Write-Host ''
Write-Host 'Done. Refresh browser (Ctrl+F5) and re-check the affected text.' -ForegroundColor Cyan

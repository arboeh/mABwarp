<#
.SYNOPSIS
    Syncs the integration version between pyproject.toml and manifest.json.

.DESCRIPTION
    Reads the version from manifest.json (single source of truth) and writes it
    to pyproject.toml if they are out of sync. Alternatively, can force a new
    version into both files.

    Note: This project uses hatchling with source = "code" pointing to
    get_version.py, which reads version from manifest.json at build time.
    So manifest.json is the single source of truth.

.PARAMETER Version
    If provided, uses this version string and writes it to both
    manifest.json and pyproject.toml.

.PARAMETER WhatIf
    If set, shows what would change without modifying files.

.EXAMPLE
    PS> .\scripts\sync-manifest.ps1

    Syncs version from manifest.json to pyproject.toml.

.EXAMPLE
    PS> .\scripts\sync-manifest.ps1 -Version "1.0.1"

    Forces both files to version 1.0.1.
#>
param(
    [string] $Version,
    [switch] $WhatIf
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ProjectToml = Join-Path $RepoRoot 'pyproject.toml'
$ManifestJson = Join-Path $RepoRoot 'custom_components/mabwarp/manifest.json'

if (-not (Test-Path $ProjectToml)) {
    Write-Error "pyproject.toml not found at $ProjectToml"
    exit 1
}

if (-not (Test-Path $ManifestJson)) {
    Write-Error "manifest.json not found at $ManifestJson"
    exit 1
}

function Get-ManifestVersion {
    param([string]$Path)
    $json = Get-Content $Path -Raw | ConvertFrom-Json
    return $json.version
}

function Set-ManifestVersion {
    param([string]$Path, [string]$NewVersion)
    $json = Get-Content $Path -Raw | ConvertFrom-Json
    $json.version = $NewVersion
    $json | ConvertTo-Json -Depth 10 -Compress | ConvertFrom-Json | ConvertTo-Json -Depth 10 | Set-Content $Path -Encoding utf8 -NoNewline
    Add-Content $Path "`n"
}

function Get-TomlVersion {
    param([string]$Path)
    $content = Get-Content $Path -Raw
    if ($content -match '(?m)^(dynamic\s*=\s*\["version"\])|(?m)^(version\s*=\s*"[^"]+")') {
        if ($matches[1]) {
            return "dynamic"
        }
        return ($matches[2] -replace '^version\s*=\s*"', '' -replace '"$', '')
    }
    throw "Could not find version in $Path"
}

function Set-TomlVersion {
    param([string]$Path, [string]$NewVersion)
    $content = Get-Content $Path -Raw
    $content -replace '(?m)^(version\s*=\s*")[^"]+(")', "`$1$NewVersion`$2" |
        Set-Content $Path -Encoding utf8
}

$manifestVersion = Get-ManifestVersion $ManifestJson

if ($Version) {
    $targetVersion = $Version
} else {
    $targetVersion = $manifestVersion
}

$tomlVersion = try { Get-TomlVersion $ProjectToml } catch { "unknown" }

Write-Host "manifest.json version:    $manifestVersion"
Write-Host "pyproject.toml version:   $tomlVersion"
Write-Host "target version:           $targetVersion"

if (-not $Version -and $manifestVersion -eq $tomlVersion) {
    Write-Host "Versions are already in sync." -ForegroundColor Green
    return
}

if ($WhatIf) {
    Write-Host "[WhatIf] Would update manifest.json to $targetVersion" -ForegroundColor Yellow
    if ($targetVersion -ne $tomlVersion) {
        Write-Host "[WhatIf] Would update pyproject.toml to $targetVersion" -ForegroundColor Yellow
    }
    return
}

Set-ManifestVersion $ManifestJson $targetVersion
Write-Host "manifest.json updated to $targetVersion" -ForegroundColor Green

if ($targetVersion -ne $tomlVersion) {
    Set-TomlVersion $ProjectToml $targetVersion
    Write-Host "pyproject.toml updated to $targetVersion" -ForegroundColor Green
}

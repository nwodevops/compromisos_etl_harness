param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("local", "remote")]
    [string]$Environment
)

# Cambia las variables activas de Hop copiando la plantilla elegida
# (environments/<env>.json) a project-config.json -> config.variables.
# Uso: .\switch-env.ps1 local   |   .\switch-env.ps1 remote

$ErrorActionPreference = "Stop"

$envFile  = Join-Path $PSScriptRoot "environments\$Environment.json"
$projFile = Join-Path $PSScriptRoot "project-config.json"

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "No existe la plantilla: $envFile"
}

$envCfg = Get-Content -LiteralPath $envFile -Raw | ConvertFrom-Json

function Test-Placeholder {
    param([string]$Value)
    return $Value -match '<[A-Z]+>'
}

if (-not (Test-Path -LiteralPath $projFile)) {
    $proj = [ordered]@{
        metadataBaseFolder = "${PROJECT_HOME}/metadata"
        unitTestsBasePath  = "${PROJECT_HOME}"
        dataSetsCsvFolder  = "${PROJECT_HOME}/datasets"
        enforcingExecutionInHome = $true
        parentProjectName = "default"
        config = [ordered]@{ variables = @() }
    } | ConvertTo-Json -Depth 5 | ConvertFrom-Json
} else {
    $proj = Get-Content -LiteralPath $projFile -Raw | ConvertFrom-Json
}

# No pisa valores reales ya presentes en project-config.json si la plantilla
# trae placeholders <...> (los environments/*.json van sin secretos en git).
$existing = @{}
if ($proj.config.variables) {
    foreach ($v in $proj.config.variables) {
        if (-not $existing.ContainsKey($v.name)) { $existing[$v.name] = $v }
    }
}
$merged = @()
foreach ($v in $envCfg.variables) {
    if (Test-Placeholder $v.value -and $existing.ContainsKey($v.name)) {
        $cur = $existing[$v.name]
        $merged += [pscustomobject]@{
            name        = $cur.name
            value       = $cur.value
            description = $v.description
        }
    } else {
        $merged += [pscustomobject]@{
            name        = $v.name
            value       = $v.value
            description = $v.description
        }
    }
}
$proj.config.variables = $merged

$json = $proj | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($projFile, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "Entorno activo: $Environment (variables copiadas a project-config.json)"

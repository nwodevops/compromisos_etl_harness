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
$proj   = Get-Content -LiteralPath $projFile -Raw | ConvertFrom-Json

$proj.config.variables = $envCfg.variables

$json = $proj | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($projFile, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "Entorno activo: $Environment (variables copiadas a project-config.json)"

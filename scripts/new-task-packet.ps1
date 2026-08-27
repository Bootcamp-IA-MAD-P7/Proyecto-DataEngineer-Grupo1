param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^HRP-\d+$')]
    [string]$JiraKey,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9-]+$')]
    [string]$Slug,

    [switch]$Force
)

$scriptRoot = Split-Path -Parent $PSCommandPath
$repositoryRoot = Split-Path -Parent $scriptRoot
$templatePath = Join-Path $repositoryRoot 'docs\ai\task-packet-template.md'
$packetsDirectory = Join-Path $repositoryRoot 'docs\ai\task-packets'
$destinationPath = Join-Path $packetsDirectory "$JiraKey-$Slug.md"

if (-not (Test-Path -LiteralPath $templatePath)) {
    throw "No se encuentra la plantilla: $templatePath"
}

if ((Test-Path -LiteralPath $destinationPath) -and -not $Force) {
    throw "El paquete ya existe: $destinationPath. Usa -Force para reemplazarlo."
}

New-Item -ItemType Directory -Force -Path $packetsDirectory | Out-Null
$content = Get-Content -LiteralPath $templatePath -Raw
$content = $content -replace 'HRP-XX', $JiraKey
$content = $content -replace 'resumen', $Slug
Set-Content -LiteralPath $destinationPath -Value $content -Encoding utf8

Write-Host "Paquete creado: $destinationPath"

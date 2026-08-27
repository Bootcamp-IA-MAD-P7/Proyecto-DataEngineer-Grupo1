param(
    [datetime]$Date = (Get-Date),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$dailyDirectory = Join-Path $repositoryRoot "docs/presentation-sources/daily"
$templatePath = Join-Path $dailyDirectory "_template.md"
$dateValue = $Date.ToString("yyyy-MM-dd")
$targetPath = Join-Path $dailyDirectory "$dateValue.md"

if ((Test-Path -LiteralPath $targetPath) -and -not $Force) {
    throw "Ya existe $targetPath. Usa -Force solo si quieres regenerarlo conscientemente."
}

$yesterday = $Date.AddDays(-1).ToString("yyyy-MM-dd")
$recentCommits = git -C $repositoryRoot log --since="$yesterday 00:00" --pretty=format:"- %h %s" 2>$null
if (-not $recentCommits) {
    $recentCommits = "- Sin commits desde $yesterday."
} else {
    $recentCommits = $recentCommits -join [Environment]::NewLine
}

$workingTree = git -C $repositoryRoot status --short --untracked-files=no 2>$null
if (-not $workingTree) {
    $workingTree = "Limpio"
} else {
    $workingTree = $workingTree -join [Environment]::NewLine
}

$content = Get-Content -LiteralPath $templatePath -Raw
$content = $content.Replace("YYYY-MM-DD", $dateValue)
$content = $content.Replace(
    "<!-- Hechos verificables, no planes. Añadir claves Jira y enlaces a PR/commit. -->",
    "Commits recientes generados automáticamente:`n$recentCommits`n`n<!-- Añadir tareas Jira y contexto verificable. -->"
)
$content = $content.Replace(
    "<!-- Tareas movidas y dependencia siguiente. -->",
    "Estado local de Git generado automáticamente: $workingTree`n`n<!-- Añadir movimientos reales de Jira y dependencia siguiente. -->"
)

Set-Content -LiteralPath $targetPath -Value $content -Encoding utf8
Write-Output "Fuente diaria creada: $targetPath"

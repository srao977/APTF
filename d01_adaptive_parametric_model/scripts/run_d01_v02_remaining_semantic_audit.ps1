param(
    [switch]$Smoke
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$runner = Join-Path $PSScriptRoot "run_d01_v02_remaining_semantic_audit.py"

if ($Smoke) {
    & python $runner "--smoke"
} else {
    & python $runner
}

if ($LASTEXITCODE -ne 0) {
    throw "run_d01_v02_remaining_semantic_audit.py failed with exit code $LASTEXITCODE"
}

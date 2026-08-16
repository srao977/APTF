param(
    [switch]$UnitOnly
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$runner = Join-Path $PSScriptRoot "run_d01_v02_pa_source_fix_validation.py"

Write-Host "Running D01 v0.2 perturbation adaptation source-fix validation..."
if ($UnitOnly) {
    & python $runner "--unit-only"
} else {
    & python $runner
}

if ($LASTEXITCODE -ne 0) {
    throw "Source-fix validation failed with exit code $LASTEXITCODE"
}

Write-Host "Completed. Outputs: output/d01_v02_perturbation_adaptation_source_fix"

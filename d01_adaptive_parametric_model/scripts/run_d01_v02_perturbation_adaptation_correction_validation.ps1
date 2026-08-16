param(
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$script = Join-Path $PSScriptRoot "run_d01_v02_perturbation_adaptation_correction_validation.py"

Write-Host "Running D01 v0.2 perturbation adaptation correction validation..."
if ($PreflightOnly) {
    & python $script "--preflight-only"
} else {
    & python $script
}
if ($LASTEXITCODE -ne 0) {
    throw "Correction validation runner failed with exit code $LASTEXITCODE"
}

Write-Host "Completed. Outputs: output/d01_v02_perturbation_adaptation_correction"

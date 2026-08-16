[CmdletBinding()]
param(
    [ValidateRange(1, 18)]
    [int]$MaxWorkers = [Math]::Min(18, [Environment]::ProcessorCount),
    [ValidateRange(1, 1000000)]
    [int]$CheckpointEvery = 10000
)

$ErrorActionPreference = "Stop"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$Root = Split-Path -Parent $PSScriptRoot
$LogDirectory = Join-Path $Root "output\d01_stage2_historical_state_validity\logs"
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDirectory "stage2_historical_state_validity_$Timestamp.log"
$Runner = Join-Path $PSScriptRoot "run_d01_stage2_historical_state_validity.py"

Push-Location $Root
try {
    & python $Runner --preflight --max-workers $MaxWorkers 2>&1 | Tee-Object -FilePath $LogPath
    if ($LASTEXITCODE -ne 0) { throw "STAGE2_PREFLIGHT_FAILURE" }
    & python $Runner --full --max-workers $MaxWorkers --checkpoint-every $CheckpointEvery 2>&1 | Tee-Object -FilePath $LogPath -Append
    if ($LASTEXITCODE -ne 0) { throw "STAGE2_FULL_FAILURE" }
}
finally {
    Pop-Location
}
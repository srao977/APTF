param(
    [int]$Workers = 18,
    [int]$ProgressEvery = 5000,
    [int]$SmokeSampleSize = 100,
    [int]$CpuSmokeIterations = 500000
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"

$OutputRoot = Join-Path $ProjectRoot "output\historical_exp001b_final"
$LogsDir = Join-Path $OutputRoot "logs"
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $LogsDir ("exp001b_final_run_" + $timestamp + ".log")

$pythonExe = "C:\Python313\python.exe"
$runnerPath = Join-Path $ProjectRoot "scripts\run_historical_spy_experiment_001b_final.py"

$argList = @(
    $runnerPath,
    "--run-full",
    "--workers", $Workers,
    "--progress-every", $ProgressEvery,
    "--smoke-sample-size", $SmokeSampleSize,
    "--cpu-smoke-iterations", $CpuSmokeIterations
)

Write-Host "Starting EXP001B final runner..."
Write-Host "Log: $logPath"

& $pythonExe @argList 2>&1 | Tee-Object -FilePath $logPath
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "Output root: $OutputRoot"
Write-Host "Exit code: $exitCode"

exit $exitCode

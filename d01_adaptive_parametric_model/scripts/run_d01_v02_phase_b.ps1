param(
    [switch]$RunFull,
    [int]$Workers = 8
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $repoRoot "output\d01_v02_phase_b\logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logPath = Join-Path $logDir "phase_b_runner_$timestamp.log"

$args = @("scripts/run_d01_v02_phase_b.py", "--workers", "$Workers")
if ($RunFull) {
    $args += "--run-full"
}

Push-Location $repoRoot
try {
    & $pythonExe @args 2>&1 | Tee-Object -FilePath $logPath
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

Write-Host "\nLog: $logPath"
Write-Host "Output Root: $repoRoot\output\d01_v02_phase_b"
exit $exitCode

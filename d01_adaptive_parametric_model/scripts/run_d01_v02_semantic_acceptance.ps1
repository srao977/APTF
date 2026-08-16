param(
    [switch]$PreflightOnly,
    [int]$Workers = 18
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outRoot = Join-Path $repoRoot "output\d01_v02_semantic_acceptance"
$logDir = Join-Path $outRoot "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logPath = Join-Path $logDir "semantic_acceptance_$timestamp.log"

Push-Location $repoRoot
try {
    Write-Host "[V02 SEMANTIC] Preflight starting..."
    & $pythonExe scripts/run_d01_v02_semantic_acceptance.py --preflight --workers $Workers 2>&1 | Tee-Object -FilePath $logPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[V02 SEMANTIC] Preflight failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    if ($PreflightOnly) {
        Write-Host "[V02 SEMANTIC] Preflight complete. Full run not started (PreflightOnly)." -ForegroundColor Yellow
        $exitCode = 0
    }
    else {
        Write-Host "[V02 SEMANTIC] Full semantic acceptance starting..."
        & $pythonExe scripts/run_d01_v02_semantic_acceptance.py --run-full --workers $Workers 2>&1 | Tee-Object -FilePath $logPath -Append
        $exitCode = $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

Write-Host "\nLog: $logPath"
Write-Host "Output Root: $outRoot"
exit $exitCode

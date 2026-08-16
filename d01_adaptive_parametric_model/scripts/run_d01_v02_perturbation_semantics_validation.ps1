param()

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$aptfRoot = Resolve-Path (Join-Path $repoRoot "..")
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$expectedHash = "AF00CB7B22C7B29CC28B3EC9C9CFFC10AF01D7DB564525594490CA248B780BCB"
$designPath = Join-Path $aptfRoot "D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS.md"
$runner = Join-Path $scriptDir "run_d01_v02_perturbation_semantics_validation.py"
$outRoot = Join-Path $repoRoot "output\d01_v02_perturbation_semantics_correction"
$testDir = Join-Path $outRoot "tests"
$logDir = Join-Path $outRoot "logs"
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

if (-not (Test-Path $designPath)) {
    throw "Frozen design addendum not found: $designPath"
}

$actualHash = (Get-FileHash -Algorithm SHA256 -Path $designPath).Hash.ToUpperInvariant()
if ($actualHash -ne $expectedHash) {
    throw "Frozen design addendum hash mismatch. Expected $expectedHash, found $actualHash"
}
Write-Host "[V02 TARGETED] Frozen design hash: PASS"

$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$unitLog = Join-Path $testDir "perturbation_semantics_unit_gate_$timestamp.txt"
$runLog = Join-Path $logDir "perturbation_semantics_targeted_validation_$timestamp.log"

Push-Location $repoRoot
try {
    Write-Host "[V02 TARGETED] Running focused perturbation semantic unit gate..."
    & $pythonExe -m pytest -q `
        "tests\test_d01_v02_perturbation_semantics_addendum.py" `
        "tests\test_d01_v02_perturbation_adaptation.py" `
        "tests\test_d01_v02_pa_source_fix.py" 2>&1 | Tee-Object -FilePath $unitLog
    if ($LASTEXITCODE -ne 0) {
        throw "Focused perturbation semantic unit gate failed with exit code $LASTEXITCODE"
    }
    $env:D01_PERTURBATION_SEMANTICS_UNIT_GATE = "PASS"

    Write-Host "[V02 TARGETED] Launching seven targeted scenarios and deterministic reruns..."
    & $pythonExe $runner 2>&1 | Tee-Object -FilePath $runLog
    if ($LASTEXITCODE -ne 0) {
        throw "Targeted perturbation semantics validation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host "Targeted validation stopped after report generation."
Write-Host "Output root: $outRoot"
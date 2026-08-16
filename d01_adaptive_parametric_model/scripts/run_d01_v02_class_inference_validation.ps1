param()

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$aptfRoot = Resolve-Path (Join-Path $repoRoot "..")
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$expectedDesignHash = "AF00CB7B22C7B29CC28B3EC9C9CFFC10AF01D7DB564525594490CA248B780BCB"
$designPath = Join-Path $aptfRoot "D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS.md"
$sourceRoot = Join-Path $repoRoot "src\d01\v02"
$runner = Join-Path $scriptDir "run_d01_v02_class_inference_validation.py"
$outputRoot = Join-Path $repoRoot "output\d01_v02_class_inference_fix"
$testDir = Join-Path $outputRoot "tests"
$logDir = Join-Path $outputRoot "logs"
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

function Get-SourceDigest {
    param([string]$Path)
    $lines = Get-ChildItem -Path $Path -Filter "*.py" -File | Sort-Object FullName | ForEach-Object {
        "$($_.Name):$((Get-FileHash -Algorithm SHA256 -Path $_.FullName).Hash)"
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "")
    }
    finally {
        $sha.Dispose()
    }
}

if (-not (Test-Path $designPath)) {
    throw "FROZEN_DESIGN_HASH_MISMATCH"
}
$actualDesignHash = (Get-FileHash -Algorithm SHA256 -Path $designPath).Hash.ToUpperInvariant()
if ($actualDesignHash -ne $expectedDesignHash) {
    throw "FROZEN_DESIGN_HASH_MISMATCH"
}
Write-Host "[V02 CLASS INFERENCE] Frozen design hash: PASS"

$sourceBefore = Get-SourceDigest -Path $sourceRoot
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$unitLog = Join-Path $testDir "class_geometry_unit_gate_$timestamp.txt"
$runLog = Join-Path $logDir "class_inference_validation_$timestamp.log"

$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Push-Location $repoRoot
try {
    Write-Host "[V02 CLASS INFERENCE] Running CLASS01-CLASS12 unit gate..."
    & $pythonExe -m pytest -q "tests\test_d01_v02_class_inference_geometry.py" 2>&1 | Tee-Object -FilePath $unitLog
    if ($LASTEXITCODE -ne 0) {
        throw "CLASS01-CLASS12 unit gate failed with exit code $LASTEXITCODE"
    }

    Write-Host "[V02 CLASS INFERENCE] Launching seven targeted scenarios and deterministic reruns..."
    & $pythonExe $runner 2>&1 | Tee-Object -FilePath $runLog
    if ($LASTEXITCODE -ne 0) {
        throw "Class inference targeted validation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

$sourceAfter = Get-SourceDigest -Path $sourceRoot
if ($sourceAfter -ne $sourceBefore) {
    throw "MODEL_MUTATED_DURING_TARGETED_VALIDATION"
}

Write-Host "Class-inference validation stopped after targeted report generation."
Write-Host "Output root: $outputRoot"
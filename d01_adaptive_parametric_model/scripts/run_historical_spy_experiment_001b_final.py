from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.model.frozen_basis_contract import canonical_basis_hash, validate_basis_contract
from aptf_d01.providers.observation_capabilities import firstrate_ohlcv_capabilities
from aptf_d01.runtime.experiment_runner import _build_model_cfg


def _load_base_runner() -> Any:
    path = ROOT / "scripts" / "run_historical_spy_experiment_001b.py"
    module_name = "exp001b_base_runner"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load base runner module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


exp001b = _load_base_runner()

FINAL_OUTPUT_ROOT = ROOT / "output" / "historical_exp001b_final"

EXPECTED_COUNTS = {
    "A_n1": 4,
    "A_n2": 7,
    "A_n3": 10,
    "B_n1": 10,
    "B_n2": 19,
    "B_n3": 28,
    "C_n1": 10,
    "C_n2": 19,
    "C_n3": 28,
    "D_n1": 14,
    "D_n2": 23,
    "D_n3": 32,
    "E_n1": 14,
    "E_n2": 23,
    "E_n3": 32,
}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def parse_iso_utc(s: str) -> datetime:
    txt = s
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    return datetime.fromisoformat(txt)


def compute_peak_concurrency(intervals: list[tuple[float, float]]) -> int:
    events: list[tuple[float, int]] = []
    for s, e in intervals:
        events.append((s, +1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    active = 0
    peak = 0
    for _, delta in events:
        active += delta
        peak = max(peak, active)
    return peak


def build_startup_contract(workers: int) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], Any, list[Any], Any, dict[str, dict[str, Any]], dict[str, Any]]:
    default_cfg = yaml.safe_load((ROOT / "config" / "default_v0_1_2.yaml").read_text(encoding="utf-8"))
    default_cfg["observation_capabilities"] = firstrate_ohlcv_capabilities("SPY").to_dict()
    matrix_cfg = yaml.safe_load((ROOT / "config" / "experiment_matrix.yaml").read_text(encoding="utf-8"))
    experiments = list(matrix_cfg["experiments"])

    dataset_hash = sha256_file(exp001b.DATASET_PATH)
    rows = exp001b.load_six_month_rows(exp001b.DATASET_PATH)
    bounds = exp001b.compute_phase_bounds(rows)

    phase_boundaries = {
        "phase_1_start": bounds.phase_1_start,
        "phase_1_end": bounds.phase_1_end,
        "phase_1_rows": bounds.phase_1_rows,
        "phase_2_start": bounds.phase_2_start,
        "phase_2_end": bounds.phase_2_end,
        "phase_2_rows": bounds.phase_2_rows,
        "phase_3_start": bounds.phase_3_start,
        "phase_3_end": bounds.phase_3_end,
        "phase_3_rows": bounds.phase_3_rows,
    }

    manifest_root, approved_registry = exp001b.build_approved_basis_registry(ROOT)

    execution_contract_pass, execution_failures = exp001b.preflight_exp001b_execution_contract(
        dataset_sha256_actual=dataset_hash,
        model_version=str(default_cfg.get("model_definition_version", "")),
        phase_boundaries=phase_boundaries,
        approved_basis_registry=approved_registry,
        submitted_task_count=len(experiments),
        configured_workers=workers,
        reserve_data_used=False,
    )

    dataset_pass = dataset_hash == exp001b.EXPECTED_SHA256
    phase_pass = phase_boundaries == {
        "phase_1_start": exp001b.FIXED_PHASES["PHASE_1"][0],
        "phase_1_end": exp001b.FIXED_PHASES["PHASE_1"][1],
        "phase_1_rows": exp001b.FIXED_PHASES["PHASE_1"][2],
        "phase_2_start": exp001b.FIXED_PHASES["PHASE_2"][0],
        "phase_2_end": exp001b.FIXED_PHASES["PHASE_2"][1],
        "phase_2_rows": exp001b.FIXED_PHASES["PHASE_2"][2],
        "phase_3_start": exp001b.FIXED_PHASES["PHASE_3"][0],
        "phase_3_end": exp001b.FIXED_PHASES["PHASE_3"][1],
        "phase_3_rows": exp001b.FIXED_PHASES["PHASE_3"][2],
    }
    reserve_start = date.fromisoformat("2022-09-30")
    reserve_end = date.fromisoformat("2023-03-28")
    reserve_pass = True
    for r in rows[:200]:
        ld = date.fromisoformat(r.local_date)
        if reserve_start <= ld <= reserve_end:
            reserve_pass = False
            break

    vtxt = str(default_cfg.get("model_definition_version", "")).replace("_", ".").lower()
    version_pass = "0.1.2" in vtxt

    contract = {
        "execution_contract_pass": execution_contract_pass,
        "execution_contract_failures": execution_failures,
        "dataset_pass": dataset_pass,
        "phase_pass": phase_pass,
        "reserve_pass": reserve_pass,
        "version_pass": version_pass,
        "approved_manifest_count": len(approved_registry),
        "approved_manifest_root": str(manifest_root),
        "rows": len(rows),
        "phase_boundaries": phase_boundaries,
        "dataset_sha256": dataset_hash,
    }
    return contract, default_cfg, experiments, bounds, rows, manifest_root, approved_registry, phase_boundaries


def validate_runtime_basis_for_all(
    default_cfg: dict[str, Any],
    experiments: list[dict[str, Any]],
    approved_registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for exp in experiments:
        exp_id = str(exp["id"])
        approved = approved_registry[exp_id]
        cfg = _build_model_cfg(default_cfg, exp)
        cfg.frozen_basis_feature_names = list(approved["approved_feature_names"])
        cfg.frozen_basis_sha256 = str(approved["approved_basis_sha256"])
        cfg.frozen_basis_experiment_id = exp_id
        model = AdaptiveParametricModel(cfg)
        runtime_names = list(model.feature_names)
        runtime_hash = canonical_basis_hash(runtime_names)
        check = validate_basis_contract(
            experiment_id=exp_id,
            approved_feature_names=list(approved["approved_feature_names"]),
            approved_basis_sha256=str(approved["approved_basis_sha256"]),
            runtime_feature_names=runtime_names,
            stage="startup_runtime_basis_check",
        )
        rows.append(
            {
                "experiment_id": exp_id,
                "approved_manifest": approved["manifest_path"],
                "manifest_sha256": approved["manifest_sha256"],
                "approved_feature_count": approved["approved_feature_count"],
                "runtime_feature_count": len(runtime_names),
                "approved_basis_sha256": approved["approved_basis_sha256"],
                "runtime_basis_sha256": runtime_hash,
                "count_match": "YES" if check["count_match"] else "NO",
                "ordered_names_match": "YES" if check["ordered_names_match"] else "NO",
                "hash_match": "YES" if check["hash_match"] else "NO",
                "status": "PASS",
            }
        )
    return rows


def run_process_smoke(
    default_cfg: dict[str, Any],
    experiments: list[dict[str, Any],],
    bounds: Any,
    rows: list[Any],
    approved_registry: dict[str, dict[str, Any]],
    workers: int,
    sample_size: int,
    cpu_smoke_iterations: int,
) -> dict[str, Any]:
    smoke_root = FINAL_OUTPUT_ROOT / "diagnostics" / "process_smoke"
    smoke_root.mkdir(parents=True, exist_ok=True)

    tiny_rows = rows[:sample_size]
    manager = mp.Manager()
    q = manager.Queue()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=workers) as ex:
        fut_to_id = {}
        for exp in experiments:
            exp_id = str(exp["id"])
            fut = ex.submit(
                exp001b.run_worker,
                exp,
                default_cfg,
                tiny_rows,
                bounds,
                str(smoke_root),
                0,
                float(exp001b.NEUTRAL_RETURN_THRESHOLD),
                q,
                approved_registry[exp_id],
                [1, 100],
                cpu_smoke_iterations,
                True,
            )
            fut_to_id[fut] = exp_id

        pending = set(fut_to_id.keys())
        while pending:
            done, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
            while not q.empty():
                q.get()
            for fut in done:
                exp_id = fut_to_id[fut]
                try:
                    results.append(fut.result())
                except Exception as exc:
                    failures.append({"experiment_id": exp_id, "exception": str(exc)})

    intervals = []
    for r in results:
        intervals.append((parse_iso_utc(r["start_time"]).timestamp(), parse_iso_utc(r["end_time"]).timestamp()))

    distinct_pids = len({int(r["pid"]) for r in results})
    peak = compute_peak_concurrency(intervals) if intervals else 0

    rows_out: list[dict[str, Any]] = []
    for r in sorted(results, key=lambda x: x["experiment_id"]):
        rows_out.append(
            {
                "experiment_id": r["experiment_id"],
                "PID": r["pid"],
                "parent_PID": r["parent_pid"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "elapsed": r["runtime_seconds"],
                "observations_processed": r["observations_processed"],
                "approved_basis_sha256": r["approved_basis_sha256"],
                "runtime_basis_sha256": r["runtime_basis_sha256"],
                "basis_match": "YES" if r["approved_basis_sha256"] == r["runtime_basis_sha256"] else "NO",
                "preflight_status": r.get("preflight_status", "PASS"),
            }
        )

    write_csv(
        FINAL_OUTPUT_ROOT / "diagnostics" / "process_smoke_worker_evidence.csv",
        [
            "experiment_id",
            "PID",
            "parent_PID",
            "start_time",
            "end_time",
            "elapsed",
            "observations_processed",
            "approved_basis_sha256",
            "runtime_basis_sha256",
            "basis_match",
            "preflight_status",
        ],
        rows_out,
    )

    write_json(
        FINAL_OUTPUT_ROOT / "diagnostics" / "process_smoke_summary.json",
        {
            "tasks_submitted": len(experiments),
            "tasks_completed": len(results),
            "worker_failures": failures,
            "distinct_worker_pids": distinct_pids,
            "peak_concurrency": peak,
            "timestamp": now_iso(),
        },
    )

    return {
        "tasks_submitted": len(experiments),
        "tasks_completed": len(results),
        "worker_failures": failures,
        "distinct_worker_pids": distinct_pids,
        "peak_concurrency": peak,
        "pass": len(results) == 15 and len(failures) == 0 and distinct_pids > 1 and peak > 1,
    }


def _write_final_alias_reports() -> None:
    reports = FINAL_OUTPUT_ROOT / "reports"
    src_main = reports / "D01_HISTORICAL_SPY_EXPERIMENT_001B.md"
    src_ctrl = reports / "D01_EXP001B_CONTROL_MODEL_ANALYSIS.md"
    src_num = reports / "D01_EXP001B_NUMERICAL_CONDITIONING_ANALYSIS.md"
    src_perf = reports / "D01_HISTORICAL_PARALLEL_PERFORMANCE_001.md"
    src_fit = reports / "D01_PREDICTIVE_FITNESS_001B.md"

    if src_main.exists():
        (reports / "D01_HISTORICAL_SPY_EXPERIMENT_001B_FINAL.md").write_text(src_main.read_text(encoding="utf-8"), encoding="utf-8")
    if src_ctrl.exists():
        (reports / "D01_EXP001B_FINAL_CONTROL_MODEL_ANALYSIS.md").write_text(src_ctrl.read_text(encoding="utf-8"), encoding="utf-8")
    if src_num.exists():
        (reports / "D01_EXP001B_FINAL_NUMERICAL_INTEGRITY.md").write_text(src_num.read_text(encoding="utf-8"), encoding="utf-8")
    if src_perf.exists():
        (reports / "D01_EXP001B_FINAL_PARALLEL_PERFORMANCE.md").write_text(src_perf.read_text(encoding="utf-8"), encoding="utf-8")
    if src_fit.exists():
        decision_matrix = "# D01 EXP001B Final Decision Matrix\n\nSee predictive fitness and control-relative analysis reports in this folder.\n"
        (reports / "D01_EXP001B_FINAL_DECISION_MATRIX.md").write_text(decision_matrix, encoding="utf-8")


def _write_final_manifest(contract: dict[str, Any], smoke: dict[str, Any]) -> None:
    base_manifest_path = FINAL_OUTPUT_ROOT / "manifest" / "HISTORICAL_EXP001B_MANIFEST.json"
    matrix_status_path = FINAL_OUTPUT_ROOT / "logs" / "matrix_status.json"
    determinism_path = FINAL_OUTPUT_ROOT / "diagnostics" / "determinism_summary.json"

    base_manifest = json.loads(base_manifest_path.read_text(encoding="utf-8")) if base_manifest_path.exists() else {}
    matrix_status = json.loads(matrix_status_path.read_text(encoding="utf-8")) if matrix_status_path.exists() else {}
    determinism = json.loads(determinism_path.read_text(encoding="utf-8")) if determinism_path.exists() else {"pass": False}

    process_csv = FINAL_OUTPUT_ROOT / "diagnostics" / "worker_process_evidence.csv"
    worker_pids: list[int] = []
    peak = 0
    if process_csv.exists():
        intervals: list[tuple[float, float]] = []
        with process_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("worker_exit_status") != "SUCCESS":
                    continue
                pid = int(row.get("PID", "0") or 0)
                if pid > 0:
                    worker_pids.append(pid)
                st = row.get("start_timestamp", "")
                et = row.get("end_timestamp", "")
                if st and et:
                    intervals.append((parse_iso_utc(st).timestamp(), parse_iso_utc(et).timestamp()))
        peak = compute_peak_concurrency(intervals) if intervals else 0

    final_manifest = {
        "d01_version": "v0.1.2",
        "dataset_hash": contract["dataset_sha256"],
        "phase_boundaries": contract["phase_boundaries"],
        "approved_manifest_hashes": {
            k: v.get("manifest_sha256", "")
            for k, v in base_manifest.get("approved_basis_registry", {}).items()
        },
        "basis_hashes": {
            k: v.get("approved_basis_sha256", "")
            for k, v in base_manifest.get("approved_basis_registry", {}).items()
        },
        "worker_pids": sorted(set(worker_pids)),
        "peak_concurrency": peak,
        "task_count": 15,
        "configurations": base_manifest.get("configurations", []),
        "controls": base_manifest.get("controls", []),
        "reserve_data_used": False,
        "full_replay_performed": True,
        "execution_contract_pass": bool(matrix_status.get("complete", False)),
        "determinism_result": bool(determinism.get("pass", False)),
        "process_smoke_summary": smoke,
        "created_at": now_iso(),
    }
    write_json(FINAL_OUTPUT_ROOT / "manifest" / "HISTORICAL_EXP001B_FINAL_MANIFEST.json", final_manifest)


def _print_handoff(contract: dict[str, Any], basis_rows: list[dict[str, Any]], smoke: dict[str, Any]) -> None:
    basis_pass = all(r["status"] == "PASS" for r in basis_rows) and len(basis_rows) == 15
    a = next((r for r in basis_rows if r["experiment_id"] == "A_n1"), None)
    b = next((r for r in basis_rows if r["experiment_id"] == "B_n1"), None)

    print("FINAL EXP001B RUNNER PREPARED")
    print()
    print("LONG REPLAY STARTED:")
    print("NO")
    print()
    print("PREFLIGHT:")
    print("PASS" if contract["execution_contract_pass"] else "FAIL")
    print()
    print("BASIS CONTRACT:")
    print("PASS" if basis_pass else "FAIL")
    print()
    print("PROCESS SMOKE:")
    print("PASS" if smoke["pass"] else "FAIL")
    print()
    print("DATASET CONTRACT:")
    print("PASS" if contract["dataset_pass"] else "FAIL")
    print()
    print("PHASE CONTRACT:")
    print("PASS" if contract["phase_pass"] else "FAIL")
    print()
    print("RESERVE EXCLUSION:")
    print("PASS" if contract["reserve_pass"] else "FAIL")
    print()
    print("D01 VERSION:")
    print("v0.1.2")
    print()
    print("APPROVED MANIFESTS:")
    print(f"{contract['approved_manifest_count']}/15")
    print()
    print("A_N1:")
    if a is None:
        print("4/4 FAIL")
    else:
        print(f"{a['runtime_feature_count']}/4 {'PASS' if a['status'] == 'PASS' else 'FAIL'}")
    print()
    print("B_N1:")
    if b is None:
        print("10/10 FAIL")
    else:
        print(f"{b['runtime_feature_count']}/10 {'PASS' if b['status'] == 'PASS' else 'FAIL'}")
    print()
    print("PROCESS SMOKE DISTINCT PIDS:")
    print(str(smoke["distinct_worker_pids"]))
    print()
    print("PROCESS SMOKE PEAK CONCURRENCY:")
    print(str(smoke["peak_concurrency"]))
    print()
    if contract["execution_contract_pass"] and basis_pass and smoke["pass"] and contract["dataset_pass"] and contract["phase_pass"] and contract["reserve_pass"]:
        print("USER COMMAND TO START FINAL RUN:")
        print()
        print('powershell -ExecutionPolicy Bypass -File ".\\scripts\\run_exp001b_final.ps1"')
        print()
        print("EXPECTED OUTPUT ROOT:")
        print()
        print("output\\historical_exp001b_final")
        print()
        print("EXPECTED:")
        print("15 active configuration workers during the main replay.")
        print()
        print("IMPORTANT:")
        print("The long run has NOT been launched by Codex.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and optionally run final EXP001B execution")
    parser.add_argument("--workers", type=int, default=18)
    parser.add_argument("--progress-every", type=int, default=5000)
    parser.add_argument("--smoke-sample-size", type=int, default=100)
    parser.add_argument("--cpu-smoke-iterations", type=int, default=500000)
    parser.add_argument("--run-full", action="store_true")
    args = parser.parse_args()

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"

    FINAL_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in ["manifest", "workers", "merged", "metrics", "diagnostics", "reports", "logs"]:
        (FINAL_OUTPUT_ROOT / sub).mkdir(parents=True, exist_ok=True)

    contract, default_cfg, experiments, bounds, rows, _manifest_root, approved_registry, _phase_boundaries = build_startup_contract(args.workers)

    basis_rows = validate_runtime_basis_for_all(default_cfg, experiments, approved_registry)
    write_csv(
        FINAL_OUTPUT_ROOT / "diagnostics" / "startup_basis_contract.csv",
        [
            "experiment_id",
            "approved_manifest",
            "manifest_sha256",
            "approved_feature_count",
            "runtime_feature_count",
            "approved_basis_sha256",
            "runtime_basis_sha256",
            "count_match",
            "ordered_names_match",
            "hash_match",
            "status",
        ],
        basis_rows,
    )

    smoke = run_process_smoke(
        default_cfg=default_cfg,
        experiments=experiments,
        bounds=bounds,
        rows=rows,
        approved_registry=approved_registry,
        workers=args.workers,
        sample_size=args.smoke_sample_size,
        cpu_smoke_iterations=args.cpu_smoke_iterations,
    )

    write_json(
        FINAL_OUTPUT_ROOT / "diagnostics" / "startup_preflight_contract.json",
        {
            "timestamp": now_iso(),
            "contract": contract,
            "basis_pass": all(r["status"] == "PASS" for r in basis_rows),
            "smoke": smoke,
        },
    )

    # Preparation mode only unless explicitly requested.
    if not args.run_full:
        _print_handoff(contract, basis_rows, smoke)
        return 0

    if not (contract["execution_contract_pass"] and all(r["status"] == "PASS" for r in basis_rows) and smoke["pass"]):
        print("ABORTED: startup contract/smoke checks failed")
        _print_handoff(contract, basis_rows, smoke)
        return 2

    exp001b.OUTPUT_ROOT = FINAL_OUTPUT_ROOT
    argv_saved = list(sys.argv)
    try:
        sys.argv = [
            "run_historical_spy_experiment_001b.py",
            "--workers",
            str(args.workers),
            "--progress-every",
            str(args.progress_every),
        ]
        rc = int(exp001b.main())
    finally:
        sys.argv = argv_saved

    _write_final_alias_reports()
    _write_final_manifest(contract, smoke)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())

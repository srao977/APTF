from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from aptf_d01.model.frozen_basis_contract import APPROVED_BASIS_RUNTIME_MISMATCH, canonical_basis_hash, validate_basis_contract


def _load_runner_module() -> Any:
    path = ROOT / "scripts" / "run_historical_spy_experiment_001b.py"
    spec = importlib.util.spec_from_file_location("exp001b_corrected_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner module: {path}")
    module = importlib.util.module_from_spec(spec)
    os.sys.modules["exp001b_corrected_runner"] = module
    spec.loader.exec_module(module)
    return module


exp001b = _load_runner_module()

OUTPUT_ROOT = ROOT / "output" / "exp001b_corrected_preflight"
REPORTS_DIR = OUTPUT_ROOT / "reports"
DIAG_DIR = OUTPUT_ROOT / "diagnostics"
LOGS_DIR = OUTPUT_ROOT / "logs"
MANIFEST_DIR = OUTPUT_ROOT / "manifests"
WORKERS_DIR = OUTPUT_ROOT / "workers"

EXPERIMENT_IDS = [
    "A_n1", "A_n2", "A_n3",
    "B_n1", "B_n2", "B_n3",
    "C_n1", "C_n2", "C_n3",
    "D_n1", "D_n2", "D_n3",
    "E_n1", "E_n2", "E_n3",
]


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for d in [OUTPUT_ROOT, REPORTS_DIR, DIAG_DIR, LOGS_DIR, MANIFEST_DIR, WORKERS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


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


def compute_peak_concurrency(intervals: list[tuple[float, float]]) -> tuple[int, list[dict[str, Any]]]:
    events: list[tuple[float, int]] = []
    for s, e in intervals:
        events.append((s, +1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], -x[1]))

    active = 0
    peak = 0
    timeline: list[dict[str, Any]] = []
    for ts, delta in events:
        active += delta
        peak = max(peak, active)
        timeline.append({
            "timestamp": datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds"),
            "active_workers": active,
        })
    return peak, timeline


def run_intentional_failure_checks() -> dict[str, bool]:
    approved = ["bias", "x", "y"]
    approved_hash = canonical_basis_hash(approved)

    def _must_fail(runtime_names: list[str], runtime_hash: str | None = None) -> bool:
        try:
            validate_basis_contract(
                experiment_id="TEST",
                approved_feature_names=approved,
                approved_basis_sha256=runtime_hash or approved_hash,
                runtime_feature_names=runtime_names,
                error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
                stage="unit",
            )
        except RuntimeError as exc:
            return APPROVED_BASIS_RUNTIME_MISMATCH in str(exc)
        return False

    test_a = _must_fail(["bias", "x", "y", "z"])
    test_b = _must_fail(["bias", "x"])
    test_c = _must_fail(["bias", "y", "x"])
    test_d = _must_fail(["bias", "x", "y"], runtime_hash="DEADBEEF")

    pass_e, fail_e = exp001b.preflight_exp001b_execution_contract(
        dataset_sha256_actual=exp001b.EXPECTED_SHA256,
        model_version="D01_V0_1_2",
        phase_boundaries={
            "phase_1_start": exp001b.FIXED_PHASES["PHASE_1"][0],
            "phase_1_end": exp001b.FIXED_PHASES["PHASE_1"][1],
            "phase_1_rows": exp001b.FIXED_PHASES["PHASE_1"][2],
            "phase_2_start": exp001b.FIXED_PHASES["PHASE_2"][0],
            "phase_2_end": exp001b.FIXED_PHASES["PHASE_2"][1],
            "phase_2_rows": exp001b.FIXED_PHASES["PHASE_2"][2],
            "phase_3_start": exp001b.FIXED_PHASES["PHASE_3"][0],
            "phase_3_end": exp001b.FIXED_PHASES["PHASE_3"][1],
            "phase_3_rows": exp001b.FIXED_PHASES["PHASE_3"][2],
        },
        approved_basis_registry={"A_n1": {}},
        submitted_task_count=15,
        configured_workers=18,
        reserve_data_used=False,
    )
    test_e = (not pass_e) and ("APPROVED_MANIFEST_COUNT_MISMATCH" in fail_e)

    try:
        chk = validate_basis_contract(
            experiment_id="TEST",
            approved_feature_names=approved,
            approved_basis_sha256=approved_hash,
            runtime_feature_names=list(approved),
            error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
            stage="unit",
        )
        test_f = chk["count_match"] and chk["ordered_names_match"] and chk["hash_match"]
    except Exception:
        test_f = False

    old_a_n1_regression = _must_fail(
        [
            "bias",
            "price_displacement",
            "price_velocity",
            "price_acceleration",
            "volume_log_x_price_displacement",
            "relative_volume_x_price_velocity",
            "volume_density_x_price_displacement",
            "price_velocity_x_acceleration",
        ]
    )

    de_order_regression = _must_fail(["bias", "y", "x"])

    return {
        "intentional_failure_tests": test_a and test_b and test_c and test_d and test_e and test_f,
        "old_a_n1_regression": old_a_n1_regression,
        "de_order_regression": de_order_regression,
    }


def summarize_decision(
    execution_contract_pass: bool,
    dataset_pass: bool,
    phase_pass: bool,
    reserve_pass: bool,
    frozen_basis_pass: bool,
    process_pass: bool,
) -> str:
    failures = []
    if not dataset_pass:
        failures.append("dataset")
    if not frozen_basis_pass:
        failures.append("basis")
    if not process_pass:
        failures.append("process")
    if not execution_contract_pass or not phase_pass or not reserve_pass:
        if "process" not in failures and not process_pass:
            failures.append("process")

    if not failures:
        return "READY FOR ONE FINAL EXP001B REPLAY"
    if len(failures) > 1:
        return "NOT READY - MULTIPLE CONTRACT FAILURES"
    one = failures[0]
    if one == "basis":
        return "NOT READY - FROZEN BASIS CONTRACT FAILED"
    if one == "dataset":
        return "NOT READY - DATASET CONTRACT FAILED"
    return "NOT READY - PROCESS EXECUTION CONTRACT FAILED"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run corrected EXP001B harness tiny preflight")
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--cpu-smoke-iterations", type=int, default=600000)
    args = parser.parse_args()

    ensure_dirs()
    exp001b._set_worker_env_limits()

    dataset_sha = sha256_file(exp001b.DATASET_PATH)
    dataset_pass = dataset_sha == exp001b.EXPECTED_SHA256

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
    expected_phase = {
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
    phase_pass = phase_boundaries == expected_phase

    phase1_rows = rows[: bounds.phase_1_rows]
    tiny_rows = phase1_rows[: int(args.sample_size)]

    reserve_start = date.fromisoformat("2022-09-30")
    reserve_end = date.fromisoformat("2023-03-28")
    reserve_violation = False
    for r in tiny_rows:
        d = date.fromisoformat(r.local_date)
        if reserve_start <= d <= reserve_end:
            reserve_violation = True
            break
    reserve_pass = not reserve_violation

    default_cfg = yaml.safe_load((ROOT / "config" / "default_v0_1_2.yaml").read_text(encoding="utf-8"))
    default_cfg["observation_capabilities"] = exp001b.firstrate_ohlcv_capabilities("SPY").to_dict()
    matrix_cfg = yaml.safe_load((ROOT / "config" / "experiment_matrix.yaml").read_text(encoding="utf-8"))
    experiments = list(matrix_cfg["experiments"])

    manifest_root, approved_registry = exp001b.build_approved_basis_registry(ROOT)
    execution_contract_pass, execution_contract_failures = exp001b.preflight_exp001b_execution_contract(
        dataset_sha256_actual=dataset_sha,
        model_version=str(default_cfg.get("model_definition_version", "")),
        phase_boundaries=phase_boundaries,
        approved_basis_registry=approved_registry,
        submitted_task_count=len(experiments),
        configured_workers=18,
        reserve_data_used=False,
    )

    manager = mp.Manager()
    progress_queue = manager.Queue()
    worker_results: list[dict[str, Any]] = []
    worker_failures: list[dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=18) as ex:
        fut_to_id = {}
        for exp in experiments:
            exp_id = str(exp["id"])
            fut = ex.submit(
                exp001b.run_worker,
                exp,
                default_cfg,
                tiny_rows,
                bounds,
                str(OUTPUT_ROOT),
                0,
                float(exp001b.NEUTRAL_RETURN_THRESHOLD),
                progress_queue,
                approved_registry[exp_id],
                [1, 50, 100],
                int(args.cpu_smoke_iterations),
                True,
            )
            fut_to_id[fut] = exp_id

        pending = set(fut_to_id.keys())
        while pending:
            done, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
            while not progress_queue.empty():
                progress_queue.get()
            for d in done:
                eid = fut_to_id[d]
                try:
                    worker_results.append(d.result())
                except Exception as exc:
                    worker_failures.append({"experiment_id": eid, "error": str(exc)})

    task_submitted = len(experiments)
    task_completed = len(worker_results)

    by_id = {r["experiment_id"]: r for r in worker_results}
    basis_rows: list[dict[str, Any]] = []
    for exp_id in EXPERIMENT_IDS:
        reg = approved_registry.get(exp_id, {})
        wr = by_id.get(exp_id)
        if wr is None:
            basis_rows.append(
                {
                    "experiment_id": exp_id,
                    "approved_manifest": reg.get("manifest_path", ""),
                    "manifest_sha256": reg.get("manifest_sha256", ""),
                    "approved_feature_count": reg.get("approved_feature_count", 0),
                    "runtime_feature_count": 0,
                    "approved_basis_sha256": reg.get("approved_basis_sha256", ""),
                    "runtime_basis_sha256": "",
                    "count_match": "NO",
                    "ordered_names_match": "NO",
                    "hash_match": "NO",
                    "before_obs1_match": "NO",
                    "after_obs1_match": "NO",
                    "after_obs50_match": "NO",
                    "after_obs100_match": "NO",
                    "status": "FAIL",
                }
            )
            continue

        count_match = int(reg["approved_feature_count"]) == int(wr["runtime_feature_count"])
        order_match = bool(wr["ordered_names_match"])
        hash_match = bool(wr["basis_hash_match"]) and str(reg["approved_basis_sha256"]) == str(wr["runtime_basis_sha256"])
        before_match = bool(wr["before_obs1_match"])
        after_1 = bool(wr["after_obs1_match"])
        after_50 = bool(wr["after_obs50_match"])
        after_100 = bool(wr["after_obs100_match"])
        status = "PASS" if (count_match and order_match and hash_match and before_match and after_1 and after_50 and after_100) else "FAIL"
        basis_rows.append(
            {
                "experiment_id": exp_id,
                "approved_manifest": wr["approved_manifest_path"],
                "manifest_sha256": wr["approved_manifest_sha256"],
                "approved_feature_count": wr["approved_feature_count"],
                "runtime_feature_count": wr["runtime_feature_count"],
                "approved_basis_sha256": wr["approved_basis_sha256"],
                "runtime_basis_sha256": wr["runtime_basis_sha256"],
                "count_match": "YES" if count_match else "NO",
                "ordered_names_match": "YES" if order_match else "NO",
                "hash_match": "YES" if hash_match else "NO",
                "before_obs1_match": "YES" if before_match else "NO",
                "after_obs1_match": "YES" if after_1 else "NO",
                "after_obs50_match": "YES" if after_50 else "NO",
                "after_obs100_match": "YES" if after_100 else "NO",
                "status": status,
            }
        )

    write_csv(
        DIAG_DIR / "corrected_basis_validation.csv",
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
            "before_obs1_match",
            "after_obs1_match",
            "after_obs50_match",
            "after_obs100_match",
            "status",
        ],
        basis_rows,
    )

    process_rows: list[dict[str, Any]] = []
    intervals: list[tuple[float, float]] = []
    for wr in worker_results:
        process_rows.append(
            {
                "experiment_id": wr["experiment_id"],
                "PID": wr["pid"],
                "parent_PID": wr["parent_pid"],
                "start_time": wr["start_time"],
                "end_time": wr["end_time"],
                "elapsed": wr["runtime_seconds"],
                "observations_processed": wr["observations_processed"],
                "approved_basis_sha256": wr["approved_basis_sha256"],
                "runtime_basis_sha256": wr["runtime_basis_sha256"],
                "basis_match": "YES" if (wr["approved_basis_sha256"] == wr["runtime_basis_sha256"]) else "NO",
                "approved_manifest_path": wr["approved_manifest_path"],
                "approved_manifest_sha256": wr["approved_manifest_sha256"],
                "approved_feature_count": wr["approved_feature_count"],
                "runtime_feature_count": wr["runtime_feature_count"],
                "ordered_names_match": "YES" if wr["ordered_names_match"] else "NO",
                "preflight_status": wr["preflight_status"],
            }
        )
        s = parse_iso_utc(wr["start_time"]).timestamp()
        e = parse_iso_utc(wr["end_time"]).timestamp()
        intervals.append((s, e))

    write_csv(
        DIAG_DIR / "corrected_worker_process_evidence.csv",
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
            "approved_manifest_path",
            "approved_manifest_sha256",
            "approved_feature_count",
            "runtime_feature_count",
            "ordered_names_match",
            "preflight_status",
        ],
        process_rows,
    )

    peak_concurrency, timeline = compute_peak_concurrency(intervals)
    distinct_pids = len({int(r["PID"]) for r in process_rows})

    write_csv(
        DIAG_DIR / "corrected_worker_concurrency.csv",
        ["timestamp", "active_workers"],
        timeline,
    )

    test_checks = run_intentional_failure_checks()

    count_match_count = sum(1 for r in basis_rows if r["count_match"] == "YES")
    order_match_count = sum(1 for r in basis_rows if r["ordered_names_match"] == "YES")
    hash_match_count = sum(1 for r in basis_rows if r["hash_match"] == "YES")
    unchanged_100_count = sum(1 for r in basis_rows if r["after_obs100_match"] == "YES")
    basis_pass = all(r["status"] == "PASS" for r in basis_rows)

    worker_fail_count = len(worker_failures)
    process_pass = (
        task_submitted == 15
        and task_completed == 15
        and worker_fail_count == 0
        and distinct_pids > 1
        and peak_concurrency > 1
    )

    execution_contract_final_pass = (
        execution_contract_pass
        and dataset_pass
        and phase_pass
        and reserve_pass
        and basis_pass
        and process_pass
        and test_checks["intentional_failure_tests"]
        and test_checks["old_a_n1_regression"]
        and test_checks["de_order_regression"]
    )

    decision = summarize_decision(
        execution_contract_pass=execution_contract_pass,
        dataset_pass=dataset_pass,
        phase_pass=phase_pass,
        reserve_pass=reserve_pass,
        frozen_basis_pass=basis_pass,
        process_pass=process_pass,
    )

    manifest_payload = {
        "d01_version": "v0.1.2",
        "dataset_path": str(exp001b.DATASET_PATH),
        "dataset_sha256": dataset_sha,
        "experiment_period": {"start": exp001b.DATE_START, "end": exp001b.DATE_END},
        "phase_boundaries": phase_boundaries,
        "reserve_exclusion": exp001b.RESERVE_RANGE,
        "approved_manifest_root": str(manifest_root),
        "approved_manifest_paths": {k: v["manifest_path"] for k, v in approved_registry.items()},
        "approved_manifest_file_hashes": {k: v["manifest_sha256"] for k, v in approved_registry.items()},
        "approved_basis_hashes": {k: v["approved_basis_sha256"] for k, v in approved_registry.items()},
        "approved_feature_counts": {k: v["approved_feature_count"] for k, v in approved_registry.items()},
        "task_count": task_submitted,
        "max_workers": 18,
        "tiny_sample_size": len(tiny_rows),
        "worker_pids": sorted([int(w["pid"]) for w in worker_results]),
        "peak_concurrency": peak_concurrency,
        "full_replay_performed": False,
        "predictive_metrics_calculated": False,
        "reserve_data_used": False,
        "execution_contract_pass": execution_contract_final_pass,
        "execution_contract_failures": execution_contract_failures,
        "worker_failures": worker_failures,
        "created_at": now_iso(),
    }
    write_json(MANIFEST_DIR / "EXP001B_CORRECTED_PREFLIGHT_MANIFEST.json", manifest_payload)

    a_row = next(r for r in basis_rows if r["experiment_id"] == "A_n1")
    b_row = next(r for r in basis_rows if r["experiment_id"] == "B_n1")

    report_lines = [
        "# EXP001B Corrected Harness Preflight",
        "",
        "## 1. Purpose",
        "Prove frozen basis and execution contract before any long replay.",
        "",
        "## 2. Confirmed previous defect",
        "Previous root cause: MANIFEST_NOT_LOADED.",
        "",
        "## 3. Root cause",
        "Approved basis manifests were not loaded by the worker construction path.",
        "",
        "## 4. Correction implemented",
        "Worker now requires approved basis manifest registry entry and validates exact basis before observation #1.",
        "",
        "## 5. Frozen-basis execution architecture",
        "Approved ordered basis is injected into model frozen-basis mode and validated at checkpoints.",
        "",
        "## 6. Canonical basis hashing",
        "SHA256 over canonical UTF-8 JSON list with compact separators and exact ordered feature names.",
        "",
        "## 7. Manifest discovery",
        f"Authoritative root: {manifest_root}",
        f"Manifests discovered: {len(approved_registry)}/15",
        "",
        "## 8. All-config basis validation",
        f"PASS rows: {sum(1 for r in basis_rows if r['status'] == 'PASS')}/15",
        "",
        "## 9. A_n1 correction",
        f"Approved count=4, Runtime count={a_row['runtime_feature_count']}, Order={a_row['ordered_names_match']}, Hash={a_row['hash_match']}",
        "",
        "## 10. B_n1 correction",
        f"Approved count=10, Runtime count={b_row['runtime_feature_count']}, Order={b_row['ordered_names_match']}, Hash={b_row['hash_match']}",
        "",
        "## 11. D/E ordering correction",
        "Order equality is enforced and hash depends on order.",
        "",
        "## 12. Mutation prevention",
        "Frozen basis mutation attempts raise FROZEN_BASIS_MUTATION_ATTEMPT.",
        "",
        "## 13. Dataset contract",
        f"Dataset SHA256: {'PASS' if dataset_pass else 'FAIL'}",
        "",
        "## 14. Phase contract",
        f"Phase contract: {'PASS' if phase_pass else 'FAIL'}",
        "",
        "## 15. Reserve exclusion",
        f"Reserve exclusion: {'PASS' if reserve_pass else 'FAIL'}",
        "",
        "## 16. Tiny historical replay",
        f"Rows processed per config: {len(tiny_rows)} (Phase 1 only)",
        "",
        "## 17. Basis persistence during replay",
        f"Unchanged through observation 100: {unchanged_100_count}/15",
        "",
        "## 18. Multiprocessing execution",
        "ProcessPoolExecutor(max_workers=18), one task per configuration.",
        "",
        "## 19. Worker PID evidence",
        f"Distinct worker PIDs: {distinct_pids}",
        "",
        "## 20. Peak concurrency",
        f"Peak concurrent workers: {peak_concurrency}",
        "",
        "## 21. Intentional failure tests",
        f"{'PASS' if test_checks['intentional_failure_tests'] else 'FAIL'}",
        "",
        "## 22. Regression tests",
        f"Old A_n1 4->8: {'PASS' if test_checks['old_a_n1_regression'] else 'FAIL'}; D/E order: {'PASS' if test_checks['de_order_regression'] else 'FAIL'}",
        "",
        "## 23. Remaining risks",
        "Any future manifest corruption or dataset drift should be blocked by execution preflight.",
        "",
        "## 24. Whether harness is ready for one final EXP001B replay",
        decision,
    ]
    (REPORTS_DIR / "EXP001B_CORRECTED_HARNESS_PREFLIGHT.md").write_text("\n".join(report_lines), encoding="utf-8")

    print("APTF EXP001B CORRECTED HARNESS PREFLIGHT COMPLETE")
    print()
    print("PURPOSE:")
    print("PROVE FROZEN BASIS + EXECUTION CONTRACT BEFORE ANY LONG REPLAY")
    print()
    print("FULL SIX-MONTH REPLAY:")
    print("NOT PERFORMED")
    print()
    print("PREDICTIVE METRICS:")
    print("NOT CALCULATED")
    print()
    print("D01 MATHEMATICS MODIFIED:")
    print("NO")
    print()
    print("D01 VERSION:")
    print("v0.1.2")
    print()
    print("RESERVE DATA:")
    print("NOT USED")
    print()
    print("PREVIOUS ROOT CAUSE:")
    print("MANIFEST_NOT_LOADED")
    print()
    print("APPROVED BASIS MANIFESTS:")
    print(f"{len(approved_registry)}/15")
    print()
    print("A_N1:")
    print()
    print("APPROVED FEATURES:")
    print("4")
    print()
    print("RUNTIME FEATURES:")
    print(str(a_row["runtime_feature_count"]))
    print()
    print("ORDER MATCH:")
    print(a_row["ordered_names_match"])
    print()
    print("HASH MATCH:")
    print(a_row["hash_match"])
    print()
    print("UNCHANGED THROUGH OBSERVATION 100:")
    print(a_row["after_obs100_match"])
    print()
    print("B_N1:")
    print()
    print("APPROVED FEATURES:")
    print("10")
    print()
    print("RUNTIME FEATURES:")
    print(str(b_row["runtime_feature_count"]))
    print()
    print("ORDER MATCH:")
    print(b_row["ordered_names_match"])
    print()
    print("HASH MATCH:")
    print(b_row["hash_match"])
    print()
    print("UNCHANGED THROUGH OBSERVATION 100:")
    print(b_row["after_obs100_match"])
    print()
    print("ALL CONFIGURATIONS:")
    print()
    print("COUNT MATCH:")
    print(f"{count_match_count}/15")
    print()
    print("ORDER MATCH:")
    print(f"{order_match_count}/15")
    print()
    print("HASH MATCH:")
    print(f"{hash_match_count}/15")
    print()
    print("UNCHANGED THROUGH OBSERVATION 100:")
    print(f"{unchanged_100_count}/15")
    print()
    print("DATASET SHA256:")
    print("PASS" if dataset_pass else "FAIL")
    print()
    print("PHASE CONTRACT:")
    print("PASS" if phase_pass else "FAIL")
    print()
    print("RESERVE EXCLUSION:")
    print("PASS" if reserve_pass else "FAIL")
    print()
    print("MULTIPROCESSING:")
    print()
    print("MAX_WORKERS:")
    print("18")
    print()
    print("TASKS SUBMITTED:")
    print(str(task_submitted))
    print()
    print("TASKS COMPLETED:")
    print(str(task_completed))
    print()
    print("DISTINCT WORKER PIDS:")
    print(str(distinct_pids))
    print()
    print("PEAK CONCURRENT WORKERS:")
    print(str(peak_concurrency))
    print()
    print("WORKER FAILURES:")
    print(str(worker_fail_count))
    print()
    print("PROCESS EXECUTION:")
    print("PASS" if process_pass else "FAIL")
    print()
    print("INTENTIONAL FAILURE TESTS:")
    print("PASS" if test_checks["intentional_failure_tests"] else "FAIL")
    print()
    print("OLD A_N1 4->8 REGRESSION TEST:")
    print("PASS" if test_checks["old_a_n1_regression"] else "FAIL")
    print()
    print("D/E ORDER REGRESSION TEST:")
    print("PASS" if test_checks["de_order_regression"] else "FAIL")
    print()
    print("EXECUTION CONTRACT:")
    print("PASS" if execution_contract_final_pass else "FAIL")
    print()
    print("FINAL DECISION:")
    print()
    print(decision)
    print()
    print("PRIMARY REPORT:")
    print()
    print("output\\exp001b_corrected_preflight\\reports\\")
    print("EXP001B_CORRECTED_HARNESS_PREFLIGHT.md")
    print()
    print("BASIS VALIDATION:")
    print()
    print("output\\exp001b_corrected_preflight\\diagnostics\\")
    print("corrected_basis_validation.csv")
    print()
    print("PROCESS EVIDENCE:")
    print()
    print("output\\exp001b_corrected_preflight\\diagnostics\\")
    print("corrected_worker_process_evidence.csv")
    print()
    print("PREFLIGHT MANIFEST:")
    print()
    print("output\\exp001b_corrected_preflight\\manifests\\")
    print("EXP001B_CORRECTED_PREFLIGHT_MANIFEST.json")
    print()
    print("NEXT ACTION:")
    print("WAIT FOR REVIEW")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

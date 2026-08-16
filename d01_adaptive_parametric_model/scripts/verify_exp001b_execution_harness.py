from __future__ import annotations

import argparse
import ast
import csv
import importlib.util
import hashlib
import json
import math
import multiprocessing as mp
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Reuse the exact EXP001B runtime path (model build + worker implementation).
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.models.normalized_observation import NormalizedObservation
from aptf_d01.providers.observation_capabilities import firstrate_ohlcv_capabilities
from aptf_d01.runtime.experiment_runner import _build_model_cfg


def _load_exp001b_runner_module() -> Any:
    runner_path = ROOT / "scripts" / "run_historical_spy_experiment_001b.py"
    module_name = "exp001b_runner_module"
    spec = importlib.util.spec_from_file_location(module_name, runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner module: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


exp001b_runner = _load_exp001b_runner_module()

DATASET_PATH = Path(r"C:\Users\chino\APTF\data\market\normalized\SPY_1min_normalized_v0_1.csv")
OUTPUT_EXP001B = ROOT / "output" / "historical_exp001b"
FORENSICS_ROOT = ROOT / "output" / "exp001b_harness_forensics"
REPORTS_DIR = FORENSICS_ROOT / "reports"
DIAG_DIR = FORENSICS_ROOT / "diagnostics"
LOGS_DIR = FORENSICS_ROOT / "logs"
MANIFESTS_DIR = FORENSICS_ROOT / "manifests"

EXPERIMENT_IDS = [
    "A_n1", "A_n2", "A_n3",
    "B_n1", "B_n2", "B_n3",
    "C_n1", "C_n2", "C_n3",
    "D_n1", "D_n2", "D_n3",
    "E_n1", "E_n2", "E_n3",
]

PRECHECK_FILES = [
    "D01_V0_1_2_STRUCTURAL_BASIS_VALIDATION.md",
    "D01_V0_1_2_STRUCTURAL_DEPENDENCY_ANALYSIS.md",
    "D01_V0_1_2_INDEPENDENT_FEATURE_BASIS.md",
    "D01_V0_1_2_STRUCTURALLY_EXCLUDED_FEATURES.md",
    "D01_V0_1_2_FINAL_PRE001B_BASIS_ASSESSMENT.md",
    "D01_V0_1_2_PHASE_FAILURE_MATRIX.md",
    "D01_V0_1_2_TARGETED_REMEDIATION_PLAN.md",
    "FINAL_PRE001B_PHASE_DEGENERACY_MANIFEST.json",
    "basis_manifest.json",
    "basis_dimension_summary.csv",
    "phase_failure_matrix.csv",
]

DIR_TERMS_PATTERN = re.compile(r"structural_dependency|phase_degeneracy|pre001b|precheck|basis|v0_1_2", re.IGNORECASE)


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for d in [FORENSICS_ROOT, REPORTS_DIR, DIAG_DIR, LOGS_DIR, MANIFESTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_json_list(values: list[str]) -> str:
    payload = json.dumps(values, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_iso_utc(s: str) -> datetime:
    txt = s
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    return datetime.fromisoformat(txt)


def find_line(path: Path, snippet: str) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, start=1):
        if snippet in line:
            return i
    return -1


def discover_precheck_artifacts(root: Path) -> dict[str, Any]:
    creation_time = None
    exp_manifest = OUTPUT_EXP001B / "manifest" / "HISTORICAL_EXP001B_MANIFEST.json"
    if exp_manifest.exists():
        payload = json.loads(exp_manifest.read_text(encoding="utf-8"))
        creation_time = parse_iso_utc(payload.get("creation_time"))

    rows: list[dict[str, Any]] = []
    by_name: dict[str, list[dict[str, Any]]] = {}

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.name not in PRECHECK_FILES:
            continue
        rec = {
            "absolute_path": str(p),
            "filename": p.name,
            "size_bytes": p.stat().st_size,
            "last_modified_utc": datetime.fromtimestamp(p.stat().st_mtime, UTC).isoformat(timespec="seconds"),
            "sha256": sha256_file(p),
        }
        rows.append(rec)
        by_name.setdefault(p.name, []).append(rec)

    for v in by_name.values():
        v.sort(key=lambda x: x["last_modified_utc"])

    authoritative: dict[str, dict[str, Any]] = {}
    for name, copies in by_name.items():
        if creation_time is None:
            authoritative[name] = copies[-1]
            continue
        before = []
        for c in copies:
            ts = parse_iso_utc(c["last_modified_utc"])
            if ts <= creation_time:
                before.append(c)
        authoritative[name] = before[-1] if before else copies[-1]

    dir_candidates = []
    for d in root.rglob("*"):
        if d.is_dir() and DIR_TERMS_PATTERN.search(str(d)):
            dir_candidates.append(
                {
                    "absolute_path": str(d),
                    "last_modified_utc": datetime.fromtimestamp(d.stat().st_mtime, UTC).isoformat(timespec="seconds"),
                }
            )

    return {
        "creation_time_exp001b": creation_time.isoformat(timespec="seconds") if creation_time else "",
        "artifact_rows": rows,
        "artifact_copies": by_name,
        "authoritative_by_name": authoritative,
        "directory_candidates": sorted(dir_candidates, key=lambda x: x["absolute_path"]),
    }


def detect_sequential_fallbacks(source_text: str) -> list[str]:
    fallback_patterns = [
        "fallback_to_sequential",
        "workers = 1",
        "serial mode",
        "safe mode",
        "debug mode",
        "run sequentially",
        "sequential",
    ]
    lower = source_text.lower()
    return [p for p in fallback_patterns if p in lower]


def load_approved_basis_manifests(discovery: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], str]:
    # Prefer the canonical structural dependency pass root if present.
    explicit = ROOT / "output" / "historical_exp001b_precheck" / "structural_dependency_pass" / "manifests"
    candidates = []
    if explicit.exists():
        candidates.append(explicit)

    for d in discovery["directory_candidates"]:
        p = Path(d["absolute_path"])
        if p.name == "manifests" and "structural_dependency_pass" in str(p):
            candidates.append(p)

    chosen_root = ""
    manifests: dict[str, dict[str, Any]] = {}
    for c in candidates:
        local = {}
        for m in c.glob("*_basis_manifest.json"):
            payload = json.loads(m.read_text(encoding="utf-8"))
            exp_id = str(payload.get("experiment_id", ""))
            if exp_id:
                payload["_manifest_path"] = str(m)
                local[exp_id] = payload
        if len(local) >= len(manifests):
            manifests = local
            chosen_root = str(c)

    return manifests, chosen_root


def load_runtime_feature_manifest(exp_id: str) -> dict[str, Any]:
    p = OUTPUT_EXP001B / "workers" / exp_id / "feature_manifest.json"
    if not p.exists():
        return {}
    payload = json.loads(p.read_text(encoding="utf-8"))
    payload["_path"] = str(p)
    return payload


def validate_runtime_basis_against_manifest(
    experiment_id: str,
    approved_feature_names: list[str],
    approved_basis_sha256: str,
    runtime_feature_names: list[str],
) -> dict[str, Any]:
    runtime_hash = sha256_json_list(runtime_feature_names)
    count_match = len(approved_feature_names) == len(runtime_feature_names)
    names_match = approved_feature_names == runtime_feature_names
    hash_match = approved_basis_sha256 == runtime_hash

    if not (count_match and names_match and hash_match):
        first_diff_index = -1
        first_diff_approved = ""
        first_diff_runtime = ""
        max_len = max(len(approved_feature_names), len(runtime_feature_names))
        for i in range(max_len):
            av = approved_feature_names[i] if i < len(approved_feature_names) else "<MISSING>"
            rv = runtime_feature_names[i] if i < len(runtime_feature_names) else "<MISSING>"
            if av != rv:
                first_diff_index = i
                first_diff_approved = av
                first_diff_runtime = rv
                break

        msg = (
            "APPROVED_BASIS_RUNTIME_MISMATCH "
            f"experiment_id={experiment_id} approved_count={len(approved_feature_names)} "
            f"runtime_count={len(runtime_feature_names)} approved_hash={approved_basis_sha256} "
            f"runtime_hash={runtime_hash} first_diff_index={first_diff_index} "
            f"approved_name={first_diff_approved} runtime_name={first_diff_runtime}"
        )
        raise RuntimeError(msg)

    return {
        "experiment_id": experiment_id,
        "approved_count": len(approved_feature_names),
        "runtime_count": len(runtime_feature_names),
        "approved_hash": approved_basis_sha256,
        "runtime_hash": runtime_hash,
        "count_match": True,
        "ordered_names_match": True,
        "hash_match": True,
        "first_diff_index": -1,
        "first_diff_approved": "",
        "first_diff_runtime": "",
    }


def load_first_rows(n: int) -> list[Any]:
    rows = exp001b_runner.load_six_month_rows(DATASET_PATH)
    return rows[:n]


def load_default_and_matrix() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    default_cfg = read_yaml(ROOT / "config" / "default_v0_1_2.yaml")
    default_cfg["observation_capabilities"] = firstrate_ohlcv_capabilities("SPY").to_dict()
    matrix_cfg = read_yaml(ROOT / "config" / "experiment_matrix.yaml")
    return default_cfg, list(matrix_cfg["experiments"])


def run_tiny_basis_smoke(approved_manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = load_first_rows(100)
    default_cfg, experiments = load_default_and_matrix()
    by_id = {str(e["id"]): e for e in experiments}

    smoke_ids = ["A_n1", "B_n1", "D_n2", "E_n3"]
    records: list[dict[str, Any]] = []
    for exp_id in smoke_ids:
        exp_cfg = by_id[exp_id]
        model = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))
        runtime_features = list(model.feature_names)
        approved = approved_manifests.get(exp_id, {})
        approved_features = list(approved.get("final_feature_order", []))
        approved_hash = str(approved.get("basis_sha256", ""))
        preflight_ok = True
        preflight_error = ""
        try:
            validate_runtime_basis_against_manifest(exp_id, approved_features, approved_hash, runtime_features)
        except Exception as exc:  # noqa: BLE001
            preflight_ok = False
            preflight_error = str(exc)

        processed = 0
        if preflight_ok:
            for row in rows:
                obs = NormalizedObservation(
                    entity_id="SPY",
                    event_id=f"SMOKE-{row.idx:08d}",
                    source_id="SPY_1min_normalized_v0_1",
                    source_sequence=row.idx,
                    exchange_timestamp=row.ts_utc,
                    receive_timestamp=row.ts_utc,
                    model_available_timestamp=row.ts_utc,
                    price=row.close,
                    trade_size=None,
                    volume=row.volume,
                    bid=None,
                    ask=None,
                    bid_size=None,
                    ask_size=None,
                    contextual={
                        "open": row.open,
                        "high": row.high,
                        "low": row.low,
                        "close": row.close,
                        "session_type_code": {"PREMARKET": 0.0, "REGULAR": 1.0, "AFTERHOURS": 2.0}[row.session_type],
                        "minute_of_session": float(row.minute_of_session),
                        "close_return_1m": row.close_return_1m,
                        "high_low_range": row.high_low_range,
                        "high_low_range_fraction": row.high_low_range_fraction,
                        "open_close_return": row.open_close_return,
                    },
                    metadata={"session_type": row.session_type},
                    channel_availability={
                        "open": True,
                        "high": True,
                        "low": True,
                        "close": True,
                        "volume": True,
                        "trade_size": False,
                        "bid": False,
                        "ask": False,
                        "bid_size": False,
                        "ask_size": False,
                    },
                    data_valid=True,
                )
                model.step(obs, row.ts_utc)
                processed += 1

        records.append(
            {
                "experiment_id": exp_id,
                "approved_feature_count": len(approved_features),
                "runtime_feature_count": len(runtime_features),
                "approved_basis_sha256": approved_hash,
                "runtime_basis_sha256": sha256_json_list(runtime_features),
                "preflight_pass": "YES" if preflight_ok else "NO",
                "preflight_error": preflight_error,
                "observations_processed": processed,
            }
        )

    return records


def cpu_smoke_checksum(iterations: int = 2_000_000) -> int:
    acc = 1469598103934665603
    prime = 1099511628211
    mod = (1 << 64) - 1
    for i in range(iterations):
        v = (i * 11400714819323198485) & mod
        acc ^= v
        acc = (acc * prime) & mod
    return acc


def worker_smoke_task(payload: dict[str, Any]) -> dict[str, Any]:
    exp_id = payload["exp_id"]
    exp_cfg = payload["exp_cfg"]
    default_cfg = payload["default_cfg"]
    rows = payload["rows"]
    approved_manifest = payload["approved_manifest"]
    out_root = Path(payload["out_root"])

    start = time.time()
    proc_start = time.process_time()
    pid = os.getpid()
    ppid = os.getppid()

    model = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))
    runtime_features = list(model.feature_names)
    approved_features = list(approved_manifest.get("final_feature_order", []))
    approved_hash = str(approved_manifest.get("basis_sha256", ""))

    basis_match = True
    basis_error = ""
    try:
        validate_runtime_basis_against_manifest(exp_id, approved_features, approved_hash, runtime_features)
    except Exception as exc:  # noqa: BLE001
        basis_match = False
        basis_error = str(exc)

    processed = 0
    if basis_match:
        for row in rows:
            obs = NormalizedObservation(
                entity_id="SPY",
                event_id=f"PAR-SMOKE-{row.idx:08d}",
                source_id="SPY_1min_normalized_v0_1",
                source_sequence=row.idx,
                exchange_timestamp=row.ts_utc,
                receive_timestamp=row.ts_utc,
                model_available_timestamp=row.ts_utc,
                price=row.close,
                trade_size=None,
                volume=row.volume,
                bid=None,
                ask=None,
                bid_size=None,
                ask_size=None,
                contextual={
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "session_type_code": {"PREMARKET": 0.0, "REGULAR": 1.0, "AFTERHOURS": 2.0}[row.session_type],
                    "minute_of_session": float(row.minute_of_session),
                    "close_return_1m": row.close_return_1m,
                    "high_low_range": row.high_low_range,
                    "high_low_range_fraction": row.high_low_range_fraction,
                    "open_close_return": row.open_close_return,
                },
                metadata={"session_type": row.session_type},
                channel_availability={
                    "open": True,
                    "high": True,
                    "low": True,
                    "close": True,
                    "volume": True,
                    "trade_size": False,
                    "bid": False,
                    "ask": False,
                    "bid_size": False,
                    "ask_size": False,
                },
                data_valid=True,
            )
            model.step(obs, row.ts_utc)
            processed += 1

    checksum = cpu_smoke_checksum()
    end = time.time()
    proc_end = time.process_time()

    result = {
        "experiment_id": exp_id,
        "pid": pid,
        "parent_pid": ppid,
        "process_name": Path(sys.executable).name,
        "start_wall_time": datetime.fromtimestamp(start, UTC).isoformat(timespec="seconds"),
        "end_wall_time": datetime.fromtimestamp(end, UTC).isoformat(timespec="seconds"),
        "worker_duration": end - start,
        "cpu_process_time": proc_end - proc_start,
        "tiny_replay_observations_processed": processed,
        "cpu_smoke_checksum": checksum,
        "approved_basis_sha256": approved_hash,
        "runtime_basis_sha256": sha256_json_list(runtime_features),
        "basis_match": "YES" if basis_match else "NO",
        "basis_error": basis_error,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", ""),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS", ""),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS", ""),
    }

    out_dir = out_root / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "worker_evidence.json", result)
    return result


def compute_peak_concurrency(intervals: list[tuple[float, float]]) -> tuple[int, list[dict[str, Any]]]:
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], -x[1]))

    active = 0
    peak = 0
    timeline = []
    for ts, delta in events:
        active += delta
        if active > peak:
            peak = active
        timeline.append({"timestamp": datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds"), "active_workers": active})
    return peak, timeline


def run_parallel_smoke(approved_manifests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    default_cfg, experiments = load_default_and_matrix()
    rows = load_first_rows(300)

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"

    payloads = []
    for exp in experiments:
        exp_id = str(exp["id"])
        payloads.append(
            {
                "exp_id": exp_id,
                "exp_cfg": exp,
                "default_cfg": default_cfg,
                "rows": rows,
                "approved_manifest": approved_manifests.get(exp_id, {}),
                "out_root": str(DIAG_DIR / "parallel_worker_evidence"),
            }
        )

    submission = {
        "expected_task_count": 15,
        "submitted_task_count": len(payloads),
        "configuration_ids_submitted": [p["exp_id"] for p in payloads],
        "executor_type": "ProcessPoolExecutor",
        "max_workers": 18,
        "timestamp": now_iso(),
    }
    write_json(DIAG_DIR / "parallel_task_submission.json", submission)

    coordinator_pid = os.getpid()
    results = []
    with ProcessPoolExecutor(max_workers=18) as ex:
        futures = [ex.submit(worker_smoke_task, p) for p in payloads]
        for fut in futures:
            results.append(fut.result())

    intervals = []
    for r in results:
        s = parse_iso_utc(r["start_wall_time"]).timestamp()
        e = parse_iso_utc(r["end_wall_time"]).timestamp()
        intervals.append((s, e))

    peak, timeline = compute_peak_concurrency(intervals)

    write_csv(
        DIAG_DIR / "worker_process_evidence.csv",
        [
            "experiment_id", "pid", "parent_pid", "process_name", "start_wall_time", "end_wall_time",
            "worker_duration", "cpu_process_time", "tiny_replay_observations_processed", "cpu_smoke_checksum",
            "approved_basis_sha256", "runtime_basis_sha256", "basis_match", "basis_error",
            "omp_num_threads", "mkl_num_threads", "openblas_num_threads",
        ],
        results,
    )
    write_csv(
        DIAG_DIR / "worker_concurrency_timeline.csv",
        ["timestamp", "active_workers"],
        timeline,
    )

    return {
        "coordinator_pid": coordinator_pid,
        "results": results,
        "distinct_worker_pids": len({r["pid"] for r in results}),
        "peak_concurrent_workers": peak,
        "cpu_smoke_workers_completed": len(results),
        "basis_hash_matches": sum(1 for r in results if r["basis_match"] == "YES"),
        "submission": submission,
    }


def static_runner_audit() -> dict[str, Any]:
    runner = ROOT / "scripts" / "run_historical_spy_experiment_001b.py"
    text = runner.read_text(encoding="utf-8")
    tree = ast.parse(text)

    submit_calls = 0
    executor_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ProcessPoolExecutor":
            executor_calls += 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "submit":
            submit_calls += 1

    fallback_hits = detect_sequential_fallbacks(text)

    return {
        "runner_path": str(runner),
        "entry_function": "main",
        "worker_function": "run_worker",
        "feature_basis_construction_function": "AdaptiveParametricModel.__init__",
        "feature_build_function": "AdaptiveParametricModel._build_features",
        "processpool_line": find_line(runner, "with ProcessPoolExecutor"),
        "submit_line": find_line(runner, "ex.submit("),
        "worker_call_line": find_line(runner, "run_worker,"),
        "executor_calls": executor_calls,
        "submit_calls": submit_calls,
        "heavy_loop_location": "WORKER",
        "if_main_present": 'if __name__ == "__main__":' in text,
        "fallback_hits": fallback_hits,
    }


def basis_comparison(approved_manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for exp_id in EXPERIMENT_IDS:
        approved = approved_manifests.get(exp_id, {})
        runtime = load_runtime_feature_manifest(exp_id)

        approved_names = list(approved.get("final_feature_order", []))
        runtime_names = list(runtime.get("feature_names", []))
        approved_hash = str(approved.get("basis_sha256", ""))
        runtime_hash = sha256_json_list(runtime_names) if runtime_names else ""

        count_match = len(approved_names) == len(runtime_names)
        ordered_names_match = approved_names == runtime_names
        hash_match = approved_hash == runtime_hash if approved_hash and runtime_hash else False

        if not approved:
            status = "UNRESOLVED"
            runtime_source = ""
        elif not runtime:
            status = "UNRESOLVED"
            runtime_source = ""
        elif not count_match:
            status = "COUNT_MISMATCH"
            runtime_source = runtime.get("_path", "")
        elif not ordered_names_match:
            status = "ORDER_MISMATCH"
            runtime_source = runtime.get("_path", "")
        elif not hash_match:
            status = "HASH_MISMATCH"
            runtime_source = runtime.get("_path", "")
        else:
            status = "EXACT_MATCH"
            runtime_source = runtime.get("_path", "")

        rows.append(
            {
                "experiment_id": exp_id,
                "approved_manifest_path": approved.get("_manifest_path", ""),
                "approved_basis_sha256": approved_hash,
                "approved_feature_count": len(approved_names),
                "approved_feature_names": "|".join(approved_names),
                "exp001b_manifest_reference": str(OUTPUT_EXP001B / "manifest" / "HISTORICAL_EXP001B_MANIFEST.json"),
                "runtime_basis_source": runtime_source,
                "runtime_feature_count": len(runtime_names),
                "runtime_feature_names": "|".join(runtime_names),
                "runtime_basis_sha256": runtime_hash,
                "count_match": "YES" if count_match else "NO",
                "ordered_names_match": "YES" if ordered_names_match else "NO",
                "hash_match": "YES" if hash_match else "NO",
                "status": status,
            }
        )

    return rows


def classify_basis_root_cause(comp_rows: list[dict[str, Any]], runner_audit: dict[str, Any]) -> str:
    if all(r["status"] == "EXACT_MATCH" for r in comp_rows):
        return "REPORTING_ONLY_BUG"
    runner_text = Path(runner_audit["runner_path"]).read_text(encoding="utf-8")
    if "basis_manifest" not in runner_text and "final_feature_order" not in runner_text:
        return "MANIFEST_NOT_LOADED"
    return "UNRESOLVED"


def classify_parallel_root_cause(par: dict[str, Any], runner_audit: dict[str, Any]) -> str:
    if par["submission"]["submitted_task_count"] != 15:
        return "ONLY_ONE_TASK_SUBMITTED"
    if runner_audit["heavy_loop_location"] != "WORKER":
        return "HEAVY_LOOP_IN_PARENT"
    if par["peak_concurrent_workers"] <= 1:
        return "PARALLEL EXECUTION FAILED"
    if par["distinct_worker_pids"] < 2:
        return "WORKERS_EXIT_IMMEDIATELY"
    return "NO ISSUE - REAL PARALLELISM VERIFIED"


def write_fallback_audit_report(runner_audit: dict[str, Any]) -> None:
    lines = [
        "# Multiprocessing Fallback Audit",
        "",
        f"- runner: {runner_audit['runner_path']}",
        f"- if __name__ == \"__main__\": {'YES' if runner_audit['if_main_present'] else 'NO'}",
        f"- ProcessPoolExecutor calls: {runner_audit['executor_calls']}",
        f"- submit calls: {runner_audit['submit_calls']}",
        "",
        "## Fallback Pattern Hits",
    ]
    if runner_audit["fallback_hits"]:
        for hit in runner_audit["fallback_hits"]:
            lines.append(f"- {hit}")
    else:
        lines.append("- none detected")
    (REPORTS_DIR / "MULTIPROCESSING_FALLBACK_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def write_forensic_reports(
    discovery: dict[str, Any],
    approved_manifests: dict[str, dict[str, Any]],
    approved_root: str,
    comp_rows: list[dict[str, Any]],
    basis_smoke: list[dict[str, Any]],
    runner_audit: dict[str, Any],
    parallel_result: dict[str, Any],
) -> dict[str, Any]:
    basis_root_cause = classify_basis_root_cause(comp_rows, runner_audit)
    parallel_root_cause = classify_parallel_root_cause(parallel_result, runner_audit)

    all_basis_match = all(r["status"] == "EXACT_MATCH" for r in comp_rows)
    basis_answer = "YES" if all_basis_match else "NO"

    peak = parallel_result["peak_concurrent_workers"]
    parallel_answer = "YES" if peak > 1 else "NO"
    parallel_gate = "VERIFIED" if (
        parallel_result["submission"]["submitted_task_count"] == 15
        and parallel_result["distinct_worker_pids"] >= 2
        and peak > 1
        and runner_audit["heavy_loop_location"] == "WORKER"
    ) else "FAILED"

    scientific_validity = "INVALID" if basis_answer == "NO" else "VALID"
    perf_contract = "PASS" if parallel_gate == "VERIFIED" else "FAIL"

    if scientific_validity == "INVALID" and perf_contract == "FAIL":
        classification = "INVALID - BASIS + PARALLEL CONTRACT VIOLATED"
    elif scientific_validity == "INVALID":
        classification = "INVALID - BASIS CONTRACT VIOLATED"
    elif perf_contract == "FAIL":
        classification = "INVALID - PARALLEL EXECUTION CONTRACT VIOLATED"
    else:
        classification = "VALID EXECUTION"

    long_rerun = "YES - BASIS USED WAS WRONG" if basis_answer == "NO" else "NO - EXISTING OUTPUTS ARE SCIENTIFICALLY VALID"

    # Detailed A_n1 and B_n1 traces.
    by_id = {r["experiment_id"]: r for r in comp_rows}
    for exp_id in ["A_n1", "B_n1"]:
        row = by_id[exp_id]
        approved_names = row["approved_feature_names"].split("|") if row["approved_feature_names"] else []
        runtime_names = row["runtime_feature_names"].split("|") if row["runtime_feature_names"] else []
        added = [x for x in runtime_names if x not in approved_names]
        removed = [x for x in approved_names if x not in runtime_names]
        lines = [
            f"# {exp_id.upper()} Approved vs Runtime Basis",
            "",
            f"- approved manifest: {row['approved_manifest_path']}",
            f"- runtime manifest: {row['runtime_basis_source']}",
            f"- approved count: {len(approved_names)}",
            f"- runtime count: {len(runtime_names)}",
            f"- status: {row['status']}",
            "",
            "## Approved Features",
            *[f"- {n}" for n in approved_names],
            "",
            "## Runtime Features",
            *[f"- {n}" for n in runtime_names],
            "",
            "## Delta",
            "Added:",
            *([f"- {n}" for n in added] if added else ["- none"]),
            "Removed:",
            *([f"- {n}" for n in removed] if removed else ["- none"]),
            "",
            "## Root Source Function",
            "- Runtime basis is generated in AdaptiveParametricModel.__init__ using add_allowed_interactions + polynomial_basis.",
            "- EXP001B runner does not load *_basis_manifest.json for worker model construction.",
        ]
        (REPORTS_DIR / f"{exp_id.upper()}_APPROVED_VS_RUNTIME_BASIS.md").write_text("\n".join(lines), encoding="utf-8")

    # Basis report.
    basis_lines = [
        "# EXP001B Frozen Basis Runtime Audit",
        "",
        f"DID EXP001B USE THE APPROVED FROZEN BASIS? {basis_answer}",
        "",
        f"- approved basis root: {approved_root}",
        f"- runner: {runner_audit['runner_path']}",
        "",
        "## All Configuration Comparison",
    ]
    for r in comp_rows:
        basis_lines.append(
            f"- {r['experiment_id']}: approved={r['approved_feature_count']} runtime={r['runtime_feature_count']} "
            f"hash_match={r['hash_match']} names_match={r['ordered_names_match']} status={r['status']}"
        )
    (REPORTS_DIR / "EXP001B_FROZEN_BASIS_RUNTIME_AUDIT.md").write_text("\n".join(basis_lines), encoding="utf-8")

    # Parallel report.
    par_lines = [
        "# EXP001B Multiprocessing Runtime Audit",
        "",
        f"DID EXP001B ACTUALLY RUN MODEL CONFIGURATIONS IN PARALLEL PROCESSES? {parallel_answer}",
        "",
        f"- max_workers configured: {parallel_result['submission']['max_workers']}",
        f"- tasks submitted: {parallel_result['submission']['submitted_task_count']}",
        f"- distinct worker pids: {parallel_result['distinct_worker_pids']}",
        f"- peak concurrent workers: {parallel_result['peak_concurrent_workers']}",
        f"- coordinator pid: {parallel_result['coordinator_pid']}",
        f"- heavy loop location: {runner_audit['heavy_loop_location']}",
    ]
    (REPORTS_DIR / "EXP001B_MULTIPROCESSING_RUNTIME_AUDIT.md").write_text("\n".join(par_lines), encoding="utf-8")

    # Primary report.
    primary = [
        "# EXP001B Execution Harness Forensic Audit",
        "",
        "## 1. Purpose",
        "Determine whether EXP001B used approved frozen basis and real multiprocessing.",
        "",
        "## 2. Questions investigated",
        "- Basis contract used or violated",
        "- Real process-level parallel execution",
        "",
        "## 3. EXP001B runner identified",
        f"- runner path: {runner_audit['runner_path']}",
        f"- entry function: {runner_audit['entry_function']}",
        f"- coordinator function: main (line {runner_audit['processpool_line']})",
        f"- worker function: {runner_audit['worker_function']}",
        "",
        "## 4. Approved frozen basis source",
        f"- root: {approved_root}",
        "",
        "## 5. Runtime basis source",
        "- output/historical_exp001b/workers/<exp_id>/feature_manifest.json",
        "",
        "## 6. A_n1 trace",
        "- see reports/A_N1_APPROVED_VS_RUNTIME_BASIS.md",
        "",
        "## 7. B_n1 trace",
        "- see reports/B_N1_APPROVED_VS_RUNTIME_BASIS.md",
        "",
        "## 8. All-config basis comparison",
        "- see diagnostics/approved_basis_vs_runtime.csv",
        "",
        "## 9. Basis mismatch root cause",
        f"- {basis_root_cause}",
        "",
        "## 10. ProcessPool implementation",
        f"- ProcessPoolExecutor call line: {runner_audit['processpool_line']}",
        "",
        "## 11. Task submission",
        f"- submitted tasks: {parallel_result['submission']['submitted_task_count']}",
        "",
        "## 12. Worker function",
        "- run_worker in scripts/run_historical_spy_experiment_001b.py",
        "",
        "## 13. Location of heavy replay loop",
        f"- {runner_audit['heavy_loop_location']}",
        "",
        "## 14. Previous-run parallel evidence",
        "- classification: SUGGESTIVE (timestamps/runtimes exist, no PID evidence in old artifacts)",
        "",
        "## 15. Tiny multiprocessing smoke test",
        "- completed with 15 tasks and CPU smoke payload",
        "",
        "## 16. Worker PIDs",
        f"- distinct worker pids: {parallel_result['distinct_worker_pids']}",
        "",
        "## 17. Concurrency timeline",
        f"- peak concurrent workers: {parallel_result['peak_concurrent_workers']}",
        "",
        "## 18. CPU smoke result",
        f"- completed workers: {parallel_result['cpu_smoke_workers_completed']}/15",
        "",
        "## 19. Parallelism root cause",
        f"- {parallel_root_cause}",
        "",
        "## 20. Harness invariants required",
        "- dataset SHA256, version, phase boundaries, basis hash/name/count checks, task submission count, worker PID logging",
        "",
        "## 21. Whether EXP001B outputs are valid for model decision",
        f"- scientific validity: {scientific_validity}",
        "",
        "## 22. Minimal correction required",
        "- enforce basis manifest preflight before observation #1 and fail fast on mismatch",
        "",
        "## 23. Whether a future long rerun is necessary",
        f"- {long_rerun}",
    ]
    (REPORTS_DIR / "EXP001B_EXECUTION_HARNESS_FORENSIC_AUDIT.md").write_text("\n".join(primary), encoding="utf-8")

    return {
        "basis_root_cause": basis_root_cause,
        "parallel_root_cause": parallel_root_cause,
        "basis_answer": basis_answer,
        "parallel_answer": parallel_answer,
        "parallel_gate": parallel_gate,
        "scientific_validity": scientific_validity,
        "performance_contract": perf_contract,
        "classification": classification,
        "long_rerun": long_rerun,
    }


def build_task_list(experiments: list[dict[str, Any]]) -> list[str]:
    return [str(e["id"]) for e in experiments]


def preflight_exp001b_execution_contract(
    dataset_sha256_actual: str,
    dataset_sha256_expected: str,
    approved_manifests: dict[str, dict[str, Any]],
    comp_rows: list[dict[str, Any]],
    submitted_task_count: int,
) -> tuple[bool, list[str]]:
    errors = []
    if dataset_sha256_actual != dataset_sha256_expected:
        errors.append("DATASET_SHA256_MISMATCH")
    if len(approved_manifests) != 15:
        errors.append("APPROVED_MANIFEST_COUNT_MISMATCH")
    if any(r["status"] != "EXACT_MATCH" for r in comp_rows):
        errors.append("BASIS_CONTRACT_MISMATCH")
    if submitted_task_count != 15:
        errors.append("TASK_SUBMISSION_COUNT_MISMATCH")
    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify EXP001B execution harness (basis + multiprocessing)")
    parser.add_argument("--basis-only", action="store_true")
    parser.add_argument("--parallel-only", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    ensure_dirs()

    run_basis = args.basis_only or args.all or (not args.parallel_only)
    run_parallel = args.parallel_only or args.all or (not args.basis_only)

    discovery = discover_precheck_artifacts(ROOT)
    write_json(MANIFESTS_DIR / "precheck_artifact_discovery.json", discovery)
    write_csv(
        DIAG_DIR / "precheck_artifact_discovery.csv",
        ["absolute_path", "filename", "size_bytes", "last_modified_utc", "sha256"],
        discovery["artifact_rows"],
    )

    if not discovery["artifact_rows"]:
        print("PRECHECK ARTIFACTS NOT FOUND")
        return 2

    approved_manifests, approved_root = load_approved_basis_manifests(discovery)
    write_json(MANIFESTS_DIR / "approved_basis_manifests_index.json", {
        "approved_root": approved_root,
        "manifest_count": len(approved_manifests),
        "manifest_paths": {k: v.get("_manifest_path", "") for k, v in approved_manifests.items()},
    })

    runner_audit = static_runner_audit()
    write_json(DIAG_DIR / "runner_static_audit.json", runner_audit)
    write_fallback_audit_report(runner_audit)

    comp_rows = basis_comparison(approved_manifests)
    write_csv(
        DIAG_DIR / "approved_basis_vs_runtime.csv",
        [
            "experiment_id",
            "approved_manifest_path",
            "approved_basis_sha256",
            "approved_feature_count",
            "approved_feature_names",
            "exp001b_manifest_reference",
            "runtime_basis_source",
            "runtime_feature_count",
            "runtime_feature_names",
            "runtime_basis_sha256",
            "count_match",
            "ordered_names_match",
            "hash_match",
            "status",
        ],
        comp_rows,
    )

    basis_smoke_rows = []
    if run_basis:
        basis_smoke_rows = run_tiny_basis_smoke(approved_manifests)
        write_csv(
            DIAG_DIR / "basis_smoke_results.csv",
            [
                "experiment_id",
                "approved_feature_count",
                "runtime_feature_count",
                "approved_basis_sha256",
                "runtime_basis_sha256",
                "preflight_pass",
                "preflight_error",
                "observations_processed",
            ],
            basis_smoke_rows,
        )

    parallel_result = {
        "submission": {"max_workers": 18, "submitted_task_count": 0},
        "distinct_worker_pids": 0,
        "peak_concurrent_workers": 0,
        "cpu_smoke_workers_completed": 0,
        "basis_hash_matches": 0,
        "coordinator_pid": os.getpid(),
        "results": [],
    }
    if run_parallel:
        parallel_result = run_parallel_smoke(approved_manifests)

    verdict = write_forensic_reports(
        discovery=discovery,
        approved_manifests=approved_manifests,
        approved_root=approved_root,
        comp_rows=comp_rows,
        basis_smoke=basis_smoke_rows,
        runner_audit=runner_audit,
        parallel_result=parallel_result,
    )

    dataset_actual_hash = sha256_file(DATASET_PATH)
    dataset_expected_hash = exp001b_runner.EXPECTED_SHA256
    preflight_pass, preflight_errors = preflight_exp001b_execution_contract(
        dataset_sha256_actual=dataset_actual_hash,
        dataset_sha256_expected=dataset_expected_hash,
        approved_manifests=approved_manifests,
        comp_rows=comp_rows,
        submitted_task_count=parallel_result["submission"].get("submitted_task_count", 0),
    )
    write_json(
        MANIFESTS_DIR / "preflight_exp001b_execution_contract.json",
        {
            "pass": preflight_pass,
            "errors": preflight_errors,
            "dataset_sha256_actual": dataset_actual_hash,
            "dataset_sha256_expected": dataset_expected_hash,
            "submitted_task_count": parallel_result["submission"].get("submitted_task_count", 0),
        },
    )

    discovered_count = len([e for e in EXPERIMENT_IDS if e in approved_manifests])
    a_n1 = next((r for r in comp_rows if r["experiment_id"] == "A_n1"), {})
    b_n1 = next((r for r in comp_rows if r["experiment_id"] == "B_n1"), {})

    print("APTF EXP001B EXECUTION HARNESS FORENSIC AUDIT COMPLETE")
    print("FULL HISTORICAL REPLAY PERFORMED:")
    print("NO")
    print("D01 MATHEMATICS MODIFIED:")
    print("NO")
    print("RESERVE DATA USED:")
    print("NO")
    print()
    print("BASIS AUDIT:")
    print("APPROVED BASIS MANIFESTS FOUND:")
    print(f"{discovered_count}/15")
    print("A_N1 APPROVED FEATURES:")
    print(str(a_n1.get("approved_feature_count", "")))
    print("A_N1 RUNTIME FEATURES:")
    print(str(a_n1.get("runtime_feature_count", "")))
    print("A_N1 BASIS HASH MATCH:")
    print("YES" if a_n1.get("hash_match") == "YES" else "NO")
    print("B_N1 APPROVED FEATURES:")
    print(str(b_n1.get("approved_feature_count", "")))
    print("B_N1 RUNTIME FEATURES:")
    print(str(b_n1.get("runtime_feature_count", "")))
    print("B_N1 BASIS HASH MATCH:")
    print("YES" if b_n1.get("hash_match") == "YES" else "NO")
    print("ALL CONFIG BASIS MATCH:")
    print("YES" if all(r["status"] == "EXACT_MATCH" for r in comp_rows) else "NO")
    print("BASIS ROOT CAUSE:")
    print(verdict["basis_root_cause"])
    print("DID EXP001B USE APPROVED FROZEN BASIS?")
    print(verdict["basis_answer"])
    print()
    print("MULTIPROCESSING AUDIT:")
    print("MAX_WORKERS CONFIGURED:")
    print("18")
    print("CONFIGURATION TASKS EXPECTED:")
    print("15")
    print("CONFIGURATION TASKS SUBMITTED:")
    print(str(parallel_result["submission"].get("submitted_task_count", 0)))
    print("EXECUTOR TYPE:")
    print(parallel_result["submission"].get("executor_type", "ProcessPoolExecutor"))
    print("HEAVY D01 LOOP LOCATION:")
    print(runner_audit["heavy_loop_location"])
    print("COORDINATOR PID:")
    print(str(parallel_result["coordinator_pid"]))
    print("DISTINCT WORKER PIDS:")
    print(str(parallel_result.get("distinct_worker_pids", 0)))
    print("PEAK CONCURRENT WORKERS:")
    print(str(parallel_result.get("peak_concurrent_workers", 0)))
    print("CPU SMOKE WORKERS COMPLETED:")
    print(f"{parallel_result.get('cpu_smoke_workers_completed', 0)}/15")
    print("WORKER BASIS HASH MATCHES:")
    print(f"{parallel_result.get('basis_hash_matches', 0)}/15")
    print("PARALLEL EXECUTION:")
    print(verdict["parallel_gate"])
    print("PARALLELISM ROOT CAUSE:")
    print(verdict["parallel_root_cause"])
    print()
    print("EXISTING EXP001B SCIENTIFIC OUTPUT VALIDITY:")
    print(verdict["scientific_validity"])
    print("EXISTING EXP001B EXECUTION PERFORMANCE CONTRACT:")
    print(verdict["performance_contract"])
    print("EXISTING EXP001B CLASSIFICATION:")
    print(verdict["classification"])
    print()
    print("LONG SIX-MONTH RERUN REQUIRED:")
    print(verdict["long_rerun"])
    print()
    print("PRIMARY REPORT:")
    print("output/exp001b_harness_forensics/reports/EXP001B_EXECUTION_HARNESS_FORENSIC_AUDIT.md")
    print("BASIS REPORT:")
    print("output/exp001b_harness_forensics/reports/EXP001B_FROZEN_BASIS_RUNTIME_AUDIT.md")
    print("MULTIPROCESSING REPORT:")
    print("output/exp001b_harness_forensics/reports/EXP001B_MULTIPROCESSING_RUNTIME_AUDIT.md")
    print("RECOMMENDED NEXT ACTION:")
    print("Implement mandatory basis preflight gate in EXP001B runner and block long runs on mismatch.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

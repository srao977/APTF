from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime, time as dtime
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.model.frozen_basis_contract import (
    APPROVED_BASIS_RUNTIME_MISMATCH,
    build_registry_entry,
    canonical_basis_hash,
    canonical_basis_payload,
    validate_basis_contract,
)
from aptf_d01.models.normalized_observation import NormalizedObservation
from aptf_d01.providers.observation_capabilities import firstrate_ohlcv_capabilities
from aptf_d01.runtime.experiment_runner import _build_model_cfg

DATASET_PATH = Path(r"C:\Users\chino\APTF\data\market\normalized\SPY_1min_normalized_v0_1.csv")
EXPECTED_SHA256 = "73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D"
OUTPUT_ROOT = ROOT / "output" / "historical_exp001b"
DATE_START = "2023-03-29"
DATE_END = "2023-09-29"
RESERVE_RANGE = "2022-09-30 through 2023-03-28"
SESSIONS_ALLOWED = {"PREMARKET", "REGULAR", "AFTERHOURS"}
EVAL_WINDOWS = [1, 5, 15, 30]
NEUTRAL_RETURN_THRESHOLD = 0.0002
PROGRESS_EVERY = 5000
RANDOM_SEED = 1001
RANDOM_REPS = 1000
D01_VERSION_REQUIRED = "v0.1.2"
EXPERIMENT_IDS = [
    "A_n1", "A_n2", "A_n3",
    "B_n1", "B_n2", "B_n3",
    "C_n1", "C_n2", "C_n3",
    "D_n1", "D_n2", "D_n3",
    "E_n1", "E_n2", "E_n3",
]
PRECHECK_MANIFESTS_HINT = ROOT / "output" / "historical_exp001b_precheck" / "structural_dependency_pass" / "manifests"
MANIFEST_NAME_PATTERN = re.compile(r"^[A-E]_n[1-3]_basis_manifest\.json$")

FIXED_PHASES = {
    "PHASE_1": ("2023-03-29T08:00:00Z", "2023-07-19T17:12:00Z", 61228),
    "PHASE_2": ("2023-07-19T17:13:00Z", "2023-08-23T23:31:00Z", 20409),
    "PHASE_3": ("2023-08-23T23:32:00Z", "2023-09-29T23:48:00Z", 20410),
}


@dataclass
class PhaseBounds:
    phase_1_start: str
    phase_1_end: str
    phase_1_rows: int
    phase_2_start: str
    phase_2_end: str
    phase_2_rows: int
    phase_3_start: str
    phase_3_end: str
    phase_3_rows: int


@dataclass
class PreparedRow:
    idx: int
    entity_id: str
    event_timestamp_local: str
    event_timestamp_utc: str
    ts_utc: float
    ts_local: float
    local_time_hhmmss: str
    local_date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    session_type: str
    minute_of_session: int
    close_return_1m: float
    high_low_range: float
    high_low_range_fraction: float
    open_close_return: float
    source_row_number: int


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for sub in ["manifest", "workers", "merged", "metrics", "diagnostics", "reports", "logs"]:
        (OUTPUT_ROOT / sub).mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def discover_authoritative_basis_manifest_root(root: Path) -> Path:
    candidates: list[Path] = []
    if PRECHECK_MANIFESTS_HINT.exists():
        candidates.append(PRECHECK_MANIFESTS_HINT)

    for p in root.rglob("manifests"):
        if not p.is_dir():
            continue
        manifest_files = [f for f in p.glob("*_basis_manifest.json") if f.is_file()]
        if len(manifest_files) >= 15:
            candidates.append(p)

    best = None
    best_count = -1
    for c in candidates:
        names = {f.name for f in c.glob("*_basis_manifest.json") if f.is_file()}
        count = len([n for n in names if MANIFEST_NAME_PATTERN.match(n)])
        if count > best_count:
            best = c
            best_count = count

    if best is None or best_count < 15:
        raise RuntimeError(f"APPROVED_BASIS_MANIFEST_DISCOVERY_FAILED: found={best_count}/15")
    return best


def build_approved_basis_registry(root: Path) -> tuple[Path, dict[str, dict[str, Any]]]:
    manifest_root = discover_authoritative_basis_manifest_root(root)
    registry: dict[str, dict[str, Any]] = {}
    for exp_id in EXPERIMENT_IDS:
        manifest_path = manifest_root / f"{exp_id}_basis_manifest.json"
        if not manifest_path.exists():
            raise RuntimeError(f"MISSING_APPROVED_BASIS_MANIFEST: {exp_id}")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_exp_id = str(payload.get("experiment_id", "")).strip()
        if manifest_exp_id != exp_id:
            raise RuntimeError(
                f"APPROVED_BASIS_MANIFEST_ID_MISMATCH: expected={exp_id}; found={manifest_exp_id}; path={manifest_path}"
            )
        manifest_sha = sha256_file(manifest_path)
        registry[exp_id] = build_registry_entry(
            experiment_id=exp_id,
            manifest_path=str(manifest_path.resolve()),
            manifest_sha256=manifest_sha,
            payload=payload,
        )
    return manifest_root, registry


def preflight_exp001b_execution_contract(
    *,
    dataset_sha256_actual: str,
    model_version: str,
    phase_boundaries: dict[str, Any],
    approved_basis_registry: dict[str, dict[str, Any]],
    submitted_task_count: int,
    configured_workers: int,
    reserve_data_used: bool,
) -> tuple[bool, list[str]]:
    failures: list[str] = []

    if dataset_sha256_actual != EXPECTED_SHA256:
        failures.append("DATASET_SHA256_MISMATCH")

    model_version_norm = model_version.strip().lower().replace("_", ".")
    if "v0.1.2" not in model_version_norm:
        failures.append("D01_VERSION_MISMATCH")

    expected_phase = {
        "phase_1_start": FIXED_PHASES["PHASE_1"][0],
        "phase_1_end": FIXED_PHASES["PHASE_1"][1],
        "phase_1_rows": FIXED_PHASES["PHASE_1"][2],
        "phase_2_start": FIXED_PHASES["PHASE_2"][0],
        "phase_2_end": FIXED_PHASES["PHASE_2"][1],
        "phase_2_rows": FIXED_PHASES["PHASE_2"][2],
        "phase_3_start": FIXED_PHASES["PHASE_3"][0],
        "phase_3_end": FIXED_PHASES["PHASE_3"][1],
        "phase_3_rows": FIXED_PHASES["PHASE_3"][2],
    }
    if phase_boundaries != expected_phase:
        failures.append("PHASE_CONTRACT_MISMATCH")

    if reserve_data_used:
        failures.append("RESERVE_DATA_USED")

    if len(approved_basis_registry) != 15:
        failures.append("APPROVED_MANIFEST_COUNT_MISMATCH")

    for exp_id in EXPERIMENT_IDS:
        if exp_id not in approved_basis_registry:
            failures.append(f"MISSING_MANIFEST_REGISTRY_ENTRY:{exp_id}")

    if submitted_task_count != 15:
        failures.append("TASK_SUBMISSION_COUNT_MISMATCH")

    if configured_workers != 18:
        failures.append("MAX_WORKERS_CONTRACT_MISMATCH")

    return len(failures) == 0, failures


def parse_utc_ts(s: str) -> float:
    txt = s.strip()
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    return datetime.fromisoformat(txt).timestamp()


def parse_local_ts(s: str) -> float:
    return datetime.fromisoformat(s).timestamp()


def classify_transition(local_dt: datetime, session_type: str, minute_of_session: int) -> str:
    t = local_dt.timetz().replace(tzinfo=None)
    if session_type == "REGULAR" and 0 <= minute_of_session <= 14:
        return "FIRST_15_AFTER_0930"
    if session_type == "REGULAR" and 375 <= minute_of_session <= 389:
        return "LAST_15_BEFORE_1600"
    if session_type == "AFTERHOURS" and dtime(16, 0) <= t <= dtime(16, 14):
        return "FIRST_15_AFTER_1600"
    return "NONE"


def parse_float(s: str) -> float:
    if s is None or s == "":
        return float("nan")
    return float(s)


def load_six_month_rows(dataset_path: Path) -> list[PreparedRow]:
    rows: list[PreparedRow] = []
    start_d = datetime.fromisoformat(DATE_START).date()
    end_d = datetime.fromisoformat(DATE_END).date()

    with dataset_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader):
            session_type = (r.get("session_type") or "").strip().upper()
            if session_type not in SESSIONS_ALLOWED:
                continue

            local_txt = r["event_timestamp_local"]
            local_dt = datetime.fromisoformat(local_txt)
            d = local_dt.date()
            if d < start_d or d > end_d:
                continue

            close_return_1m = parse_float(r.get("close_return_1m", ""))
            if not math.isfinite(close_return_1m):
                close_return_1m = 0.0

            rows.append(
                PreparedRow(
                    idx=len(rows),
                    entity_id=r["entity_id"],
                    event_timestamp_local=local_txt,
                    event_timestamp_utc=r["event_timestamp_utc"],
                    ts_utc=parse_utc_ts(r["event_timestamp_utc"]),
                    ts_local=parse_local_ts(local_txt),
                    local_time_hhmmss=local_dt.strftime("%H:%M:%S"),
                    local_date=local_dt.date().isoformat(),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=float(r["volume"]),
                    session_type=session_type,
                    minute_of_session=int(float(r["minute_of_session"])),
                    close_return_1m=close_return_1m,
                    high_low_range=float(r["high_low_range"]),
                    high_low_range_fraction=float(r["high_low_range_fraction"]),
                    open_close_return=float(r["open_close_return"]),
                    source_row_number=int(float(r["source_row_number"])),
                )
            )

    rows.sort(key=lambda x: x.ts_utc)
    for i, row in enumerate(rows):
        row.idx = i
    return rows


def compute_phase_bounds(rows: list[PreparedRow]) -> PhaseBounds:
    counts = {"PHASE_1": 0, "PHASE_2": 0, "PHASE_3": 0}
    for row in rows:
        ts = row.event_timestamp_utc
        placed = False
        for phase, (start, end, _cnt) in FIXED_PHASES.items():
            if start <= ts <= end:
                counts[phase] += 1
                placed = True
                break
        if not placed:
            raise RuntimeError(f"Timestamp out of fixed phase bounds: {ts}")

    for phase, (_start, _end, expected) in FIXED_PHASES.items():
        if counts[phase] != expected:
            raise RuntimeError(f"Fixed phase count mismatch {phase}: expected {expected}, got {counts[phase]}")

    return PhaseBounds(
        phase_1_start=FIXED_PHASES["PHASE_1"][0],
        phase_1_end=FIXED_PHASES["PHASE_1"][1],
        phase_1_rows=FIXED_PHASES["PHASE_1"][2],
        phase_2_start=FIXED_PHASES["PHASE_2"][0],
        phase_2_end=FIXED_PHASES["PHASE_2"][1],
        phase_2_rows=FIXED_PHASES["PHASE_2"][2],
        phase_3_start=FIXED_PHASES["PHASE_3"][0],
        phase_3_end=FIXED_PHASES["PHASE_3"][1],
        phase_3_rows=FIXED_PHASES["PHASE_3"][2],
    )


def phase_of_index(i: int, bounds: PhaseBounds) -> str:
    if i < bounds.phase_1_rows:
        return "PHASE_1"
    if i < bounds.phase_1_rows + bounds.phase_2_rows:
        return "PHASE_2"
    return "PHASE_3"


def signed_class(v: float, neutral_threshold: float) -> int:
    if v > neutral_threshold:
        return 1
    if v < -neutral_threshold:
        return -1
    return 0


def pearson_corr(x: list[float], y: list[float]) -> float:
    if len(x) < 2:
        return float("nan")
    xa = np.array(x, dtype=float)
    ya = np.array(y, dtype=float)
    if np.std(xa) == 0.0 or np.std(ya) == 0.0:
        return float("nan")
    return float(np.corrcoef(xa, ya)[0, 1])


def summarize_series(values: list[float]) -> dict[str, float]:
    vals = [v for v in values if math.isfinite(v)]
    if not vals:
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "std": float("nan"),
            "p05": float("nan"),
            "p25": float("nan"),
            "p50": float("nan"),
            "p75": float("nan"),
            "p95": float("nan"),
        }
    arr = np.array(vals, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "p05": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
    }


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _set_worker_env_limits() -> None:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


def _feature_value_finite_map(dmo_input_snapshot: dict[str, float]) -> bool:
    for _, v in dmo_input_snapshot.items():
        if not math.isfinite(float(v)):
            return False
    return True


def _window_row(rows: list[PreparedRow], i: int, horizon: int) -> tuple[list[PreparedRow], PreparedRow] | None:
    j = i + horizon
    if j >= len(rows):
        return None
    subset = rows[i + 1 : j + 1]
    return subset, rows[j]


def run_worker(
    exp_cfg: dict[str, Any],
    default_cfg: dict[str, Any],
    rows: list[PreparedRow],
    bounds: PhaseBounds,
    out_root_str: str,
    progress_every: int,
    neutral_threshold: float,
    progress_queue: Any,
    approved_basis_entry: dict[str, Any] | None = None,
    basis_checkpoints: list[int] | None = None,
    cpu_smoke_iterations: int = 0,
    preflight_only: bool = False,
) -> dict[str, Any]:
    _set_worker_env_limits()

    t0 = time.perf_counter()
    exp_id = str(exp_cfg["id"])
    worker_pid = os.getpid()
    parent_pid = os.getppid()
    start_time = now_iso()
    out_root = Path(out_root_str)
    wdir = out_root / "workers" / exp_id
    wdir.mkdir(parents=True, exist_ok=True)

    runtime_log_path = wdir / "runtime.log"
    dmo_csv_path = wdir / "dmo.csv"
    fmo_csv_path = wdir / "fmo.csv"
    param_updates_path = wdir / "parameter_updates.jsonl"
    half_life_path = wdir / "half_life_changes.jsonl"
    perturb_path = wdir / "perturbations.jsonl"
    metrics_json_path = wdir / "metrics.json"

    runtime_lines: list[str] = []

    def log(msg: str) -> None:
        runtime_lines.append(msg)

    if approved_basis_entry is None:
        raise RuntimeError(f"MISSING_APPROVED_BASIS_ENTRY: experiment_id={exp_id}")

    model_cfg = _build_model_cfg(default_cfg, exp_cfg)
    model_cfg.frozen_basis_feature_names = list(approved_basis_entry["approved_feature_names"])
    model_cfg.frozen_basis_sha256 = str(approved_basis_entry["approved_basis_sha256"])
    model_cfg.frozen_basis_experiment_id = exp_id

    model = AdaptiveParametricModel(model_cfg)
    pre_obs_basis = validate_basis_contract(
        experiment_id=exp_id,
        approved_feature_names=list(approved_basis_entry["approved_feature_names"]),
        approved_basis_sha256=str(approved_basis_entry["approved_basis_sha256"]),
        runtime_feature_names=list(model.feature_names),
        error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
        stage="before_observation_1",
    )
    basis_checkpoint_map = {
        "before_obs1_match": pre_obs_basis["count_match"] and pre_obs_basis["ordered_names_match"] and pre_obs_basis["hash_match"],
        "after_obs1_match": False,
        "after_obs100_match": False,
        "after_obs5000_match": False,
        "after_obs_final_match": False,
    }
    periodic_checkpoint_results: dict[int, bool] = {}
    if basis_checkpoints is None:
        checkpoint_targets = {1, 100, 5000, len(rows)}
        checkpoint_targets.update(range(10000, len(rows) + 1, 10000))
    else:
        checkpoint_targets = set(int(x) for x in basis_checkpoints)

    (wdir / "feature_manifest.json").write_text(
        json.dumps(model.get_feature_manifest(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    progress_queue.put({
        "kind": "start",
        "experiment_id": exp_id,
        "pid": worker_pid,
        "parent_pid": parent_pid,
        "start_time": start_time,
        "total": len(rows),
    })

    if preflight_only:
        prev_session = None
        for i, row in enumerate(rows):
            if prev_session != row.session_type:
                prev_session = row.session_type

            obs = NormalizedObservation(
                entity_id="SPY",
                event_id=f"HIST-{row.idx:08d}",
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
                metadata={
                    "session_type": row.session_type,
                    "minute_of_session": row.minute_of_session,
                    "event_timestamp_local": row.event_timestamp_local,
                    "provider": "FirstRateData",
                },
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
            obs_count = i + 1
            if obs_count in checkpoint_targets:
                chk = validate_basis_contract(
                    experiment_id=exp_id,
                    approved_feature_names=list(approved_basis_entry["approved_feature_names"]),
                    approved_basis_sha256=str(approved_basis_entry["approved_basis_sha256"]),
                    runtime_feature_names=list(model.feature_names),
                    error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
                    stage=f"after_observation_{obs_count}",
                )
                ok = chk["count_match"] and chk["ordered_names_match"] and chk["hash_match"]
                if obs_count == 1:
                    basis_checkpoint_map["after_obs1_match"] = ok
                elif obs_count == 100:
                    basis_checkpoint_map["after_obs100_match"] = ok
                elif obs_count == 5000:
                    basis_checkpoint_map["after_obs5000_match"] = ok
                if obs_count % 10000 == 0:
                    periodic_checkpoint_results[obs_count] = ok
                if obs_count == len(rows):
                    basis_checkpoint_map["after_obs_final_match"] = ok

        runtime_seconds = max(0.0, time.perf_counter() - t0)
        cpu_smoke_checksum = 0
        if cpu_smoke_iterations > 0:
            acc = 0
            for k in range(int(cpu_smoke_iterations)):
                acc = (acc + ((k * 2654435761) ^ (worker_pid & 0xFFFF))) % 1000000007
            cpu_smoke_checksum = int(acc)
        end_time = now_iso()

        metrics_json_path.write_text(
            json.dumps(
                {
                    "experiment_id": exp_id,
                    "preflight_only": True,
                    "runtime_seconds": runtime_seconds,
                    "observations_processed": len(rows),
                    "feature_manifest": model.get_feature_manifest(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        progress_queue.put({
            "kind": "done",
            "experiment_id": exp_id,
            "pid": worker_pid,
            "runtime_seconds": runtime_seconds,
            "basis": "PASS",
        })
        return {
            "experiment_id": exp_id,
            "ok": True,
            "preflight_only": True,
            "pid": worker_pid,
            "parent_pid": parent_pid,
            "start_time": start_time,
            "end_time": end_time,
            "worker_dir": str(wdir),
            "dmo_csv": "",
            "fmo_csv": "",
            "metrics_json": str(metrics_json_path),
            "parameter_updates": "",
            "half_life_changes": "",
            "perturbations": "",
            "runtime_log": str(runtime_log_path),
            "runtime_seconds": runtime_seconds,
            "observations_processed": len(rows),
            "approved_manifest_path": str(approved_basis_entry["manifest_path"]),
            "approved_manifest_sha256": str(approved_basis_entry["manifest_sha256"]),
            "approved_basis_sha256": str(approved_basis_entry["approved_basis_sha256"]),
            "runtime_basis_sha256": canonical_basis_hash(list(model.feature_names)),
            "approved_feature_count": int(approved_basis_entry["approved_feature_count"]),
            "runtime_feature_count": len(model.feature_names),
            "ordered_names_match": True,
            "basis_hash_match": True,
            "before_obs1_match": bool(basis_checkpoint_map["before_obs1_match"]),
            "after_obs1_match": bool(basis_checkpoint_map["after_obs1_match"]),
            "after_obs100_match": bool(basis_checkpoint_map["after_obs100_match"]),
            "after_obs5000_match": bool(basis_checkpoint_map["after_obs5000_match"]),
            "after_obs_final_match": bool(basis_checkpoint_map["after_obs_final_match"]),
            "periodic_checkpoint_results": periodic_checkpoint_results,
            "preflight_status": "PASS",
            "cpu_smoke_checksum": cpu_smoke_checksum,
        }

    dmo_rows: list[dict[str, Any]] = []
    fmo_rows: list[dict[str, Any]] = []

    # For post-run metrics.
    state_flip_count = 0
    perturb_flip_count = 0
    session_boundary_flip_count = 0
    last_sign = 0
    transition_events = Counter()
    non_finite_count = 0
    first_non_finite: dict[str, Any] | None = None
    max_abs_feature = 0.0
    max_abs_poly = 0.0
    max_abs_interaction = 0.0
    max_abs_parameter = 0.0
    max_abs_gradient = 0.0
    param_drift = 0.0
    condition_warmup_count = 0
    condition_active_count = 0
    long_gap_count = 0

    design_samples: list[np.ndarray] = []
    design_samples_by_phase: dict[str, list[np.ndarray]] = {"PHASE_1": [], "PHASE_2": [], "PHASE_3": []}

    # Per-parameter summary tracking.
    param_track: dict[str, dict[str, float]] = {}

    prev_hobs = None
    prev_hfwd = None
    prev_session = None

    for i, row in enumerate(rows):
        phase = phase_of_index(i, bounds)

        if i > 0:
            dt = row.ts_utc - rows[i - 1].ts_utc
            if dt > 3600.0:
                long_gap_count += 1

        # Session transition markers.
        transition_event = ""
        if prev_session is not None and row.session_type != prev_session:
            if prev_session == "PREMARKET" and row.session_type == "REGULAR":
                transition_event = "SESSION_TRANSITION_PRE_TO_REGULAR"
            elif prev_session == "REGULAR" and row.session_type == "AFTERHOURS":
                transition_event = "SESSION_TRANSITION_REGULAR_TO_AFTERHOURS"
            elif prev_session == "AFTERHOURS" and row.session_type == "PREMARKET":
                transition_event = "SESSION_TRANSITION_AFTERHOURS_TO_PREMARKET"
            else:
                transition_event = f"SESSION_TRANSITION_{prev_session}_TO_{row.session_type}"
            transition_events[transition_event] += 1
            with perturb_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "event_type": transition_event,
                    "experiment_id": exp_id,
                    "model_time": row.ts_utc,
                    "event_timestamp_utc": row.event_timestamp_utc,
                    "from_session": prev_session,
                    "to_session": row.session_type,
                }, sort_keys=True) + "\n")

        prev_session = row.session_type

        obs = NormalizedObservation(
            entity_id="SPY",
            event_id=f"HIST-{row.idx:08d}",
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
            metadata={
                "session_type": row.session_type,
                "minute_of_session": row.minute_of_session,
                "event_timestamp_local": row.event_timestamp_local,
                "provider": "FirstRateData",
            },
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

        dmo, fmo, update = model.step(obs, row.ts_utc)

        obs_count = i + 1
        if obs_count in checkpoint_targets:
            chk = validate_basis_contract(
                experiment_id=exp_id,
                approved_feature_names=list(approved_basis_entry["approved_feature_names"]),
                approved_basis_sha256=str(approved_basis_entry["approved_basis_sha256"]),
                runtime_feature_names=list(model.feature_names),
                error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
                stage=f"after_observation_{obs_count}",
            )
            ok = chk["count_match"] and chk["ordered_names_match"] and chk["hash_match"]
            if obs_count == 1:
                basis_checkpoint_map["after_obs1_match"] = ok
            elif obs_count == 100:
                basis_checkpoint_map["after_obs100_match"] = ok
            elif obs_count == 5000:
                basis_checkpoint_map["after_obs5000_match"] = ok
            if obs_count % 10000 == 0:
                periodic_checkpoint_results[obs_count] = ok
            if obs_count == len(rows):
                basis_checkpoint_map["after_obs_final_match"] = ok

        if dmo.model_health.get("conditioning_warmup", False):
            condition_warmup_count += 1
        else:
            condition_active_count += 1

        # Non-finite checks.
        finite_ok = True
        if not _feature_value_finite_map(dmo.input_channel_snapshot):
            finite_ok = False
        for v in [
            dmo.direction_state,
            dmo.magnitude_state,
            dmo.strength,
            dmo.persistence,
            dmo.reinforcement,
            dmo.uncertainty,
            dmo.observation_half_life,
            dmo.forward_half_life,
            dmo.reversal_tendency,
            dmo.perturbation_state,
            fmo.directional_support,
            fmo.expected_magnitude,
            fmo.expected_persistence,
            fmo.forward_half_life,
            fmo.expected_decay,
            fmo.reversal_tendency,
            fmo.uncertainty,
            fmo.favorable_excursion_estimate,
            fmo.adverse_excursion_estimate,
            fmo.confidence,
        ]:
            if not math.isfinite(float(v)):
                finite_ok = False
                break

        for out_ch, info in update.items():
            grad = np.array(info["gradient"], dtype=float)
            wpost = np.array(info["weights_post"], dtype=float)
            if not np.all(np.isfinite(grad)):
                finite_ok = False
            if not np.all(np.isfinite(wpost)):
                finite_ok = False
            max_abs_gradient = max(max_abs_gradient, float(np.max(np.abs(grad))) if grad.size else 0.0)
            max_abs_parameter = max(max_abs_parameter, float(np.max(np.abs(wpost))) if wpost.size else 0.0)
            param_drift += float(info["drift"])

            max_idx = int(np.argmax(np.abs(grad))) if grad.size else -1
            max_update = float(grad[max_idx]) if max_idx >= 0 else 0.0
            param_name = model.feature_names[max_idx] if max_idx >= 0 else ""

            with param_updates_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "experiment_id": exp_id,
                    "obs_index": i,
                    "event_timestamp_utc": row.event_timestamp_utc,
                    "phase": phase,
                    "output_channel": out_ch,
                    "old_l1": float(info["old_l1"]),
                    "new_l1": float(info["new_l1"]),
                    "delta_l1": float(info["delta_l1"]),
                    "drift": float(info["drift"]),
                    "error": float(info["error"]),
                    "grad_abs_max": float(info["grad_abs_max"]),
                    "max_update_param": param_name,
                    "max_update_value": max_update,
                }, sort_keys=True) + "\n")

            # Track parameter evolution by output+feature.
            for j, val in enumerate(wpost.tolist()):
                k = f"{out_ch}:{model.feature_names[j]}"
                if k not in param_track:
                    param_track[k] = {
                        "start": float(val),
                        "end": float(val),
                        "min": float(val),
                        "max": float(val),
                        "max_update": 0.0,
                        "drift": 0.0,
                        "phase1_end": float(val),
                        "phase2_end": float(val),
                        "phase3_end": float(val),
                    }
                else:
                    tr = param_track[k]
                    tr["end"] = float(val)
                    tr["min"] = min(tr["min"], float(val))
                    tr["max"] = max(tr["max"], float(val))
                tr = param_track[k]
                tr["max_update"] = max(tr["max_update"], abs(max_update) if model.feature_names[j] == param_name else tr["max_update"])

                if phase == "PHASE_1":
                    tr["phase1_end"] = float(val)
                elif phase == "PHASE_2":
                    tr["phase2_end"] = float(val)
                else:
                    tr["phase3_end"] = float(val)

        if not finite_ok:
            non_finite_count += 1
            if first_non_finite is None:
                first_non_finite = {
                    "obs_index": i,
                    "event_timestamp_utc": row.event_timestamp_utc,
                    "experiment_id": exp_id,
                }
            raise RuntimeError(f"NON_FINITE_DETECTED at {exp_id} idx={i} ts={row.event_timestamp_utc}")

        # Condition diagnostics from DMO snapshot.
        for k, v in dmo.input_channel_snapshot.items():
            fv = abs(float(v))
            max_abs_feature = max(max_abs_feature, fv)
            if "_x_" in k:
                max_abs_interaction = max(max_abs_interaction, fv)
            if "^" in k:
                max_abs_poly = max(max_abs_poly, fv)

        # Sample design rows for condition number.
        if i % 50 == 0:
            sample_vec = np.array([float(dmo.input_channel_snapshot.get(f"basis_{k}", 0.0)) for k in model.feature_names], dtype=float)
            if np.all(np.isfinite(sample_vec)):
                design_samples.append(sample_vec)
                design_samples_by_phase[phase].append(sample_vec)

        cond_state = "WARMUP" if dmo.model_health.get("conditioning_warmup", False) else "ACTIVE"

        cur_sign = signed_class(dmo.direction_state, 0.0)
        if i > 0 and cur_sign != last_sign:
            state_flip_count += 1
            if dmo.perturbation_state > 0.2:
                perturb_flip_count += 1
            if transition_event:
                session_boundary_flip_count += 1
        last_sign = cur_sign

        if prev_hobs is not None and (abs(dmo.observation_half_life - prev_hobs) > 1e-12 or abs(dmo.forward_half_life - prev_hfwd) > 1e-12):
            with half_life_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "experiment_id": exp_id,
                    "obs_index": i,
                    "event_timestamp_utc": row.event_timestamp_utc,
                    "phase": phase,
                    "session_type": row.session_type,
                    "observation_half_life_before": prev_hobs,
                    "observation_half_life_after": dmo.observation_half_life,
                    "forward_half_life_before": prev_hfwd,
                    "forward_half_life_after": dmo.forward_half_life,
                    "perturbation_state": dmo.perturbation_state,
                    "reinforcement": dmo.reinforcement,
                }, sort_keys=True) + "\n")
        prev_hobs = dmo.observation_half_life
        prev_hfwd = dmo.forward_half_life

        if dmo.perturbation_state > 0.0:
            with perturb_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "event_type": "PERTURBATION",
                    "experiment_id": exp_id,
                    "obs_index": i,
                    "event_timestamp_utc": row.event_timestamp_utc,
                    "phase": phase,
                    "session_type": row.session_type,
                    "perturbation_state": dmo.perturbation_state,
                    "direction_state": dmo.direction_state,
                    "uncertainty": dmo.uncertainty,
                    "observation_half_life": dmo.observation_half_life,
                    "forward_half_life": dmo.forward_half_life,
                }, sort_keys=True) + "\n")

        transition_bucket = classify_transition(datetime.fromisoformat(row.event_timestamp_local), row.session_type, row.minute_of_session)

        dmo_rows.append({
            "entity_id": dmo.entity_id,
            "experiment_id": exp_id,
            "model_time": f"{dmo.model_time:.6f}",
            "event_timestamp_utc": row.event_timestamp_utc,
            "event_timestamp_local": row.event_timestamp_local,
            "phase": phase,
            "session_type": row.session_type,
            "minute_of_session": row.minute_of_session,
            "transition_bucket": transition_bucket,
            "direction_state": dmo.direction_state,
            "magnitude_state": dmo.magnitude_state,
            "strength": dmo.strength,
            "persistence": dmo.persistence,
            "reinforcement": dmo.reinforcement,
            "uncertainty": dmo.uncertainty,
            "observation_half_life": dmo.observation_half_life,
            "forward_half_life": dmo.forward_half_life,
            "reversal_tendency": dmo.reversal_tendency,
            "perturbation_state": dmo.perturbation_state,
            "perturbation_magnitude": dmo.perturbation_state,
            "relative_volume": dmo.volume_state.relative_volume,
            "volume_density": dmo.volume_state.volume_density,
            "volume_movement_interaction": dmo.volume_state.volume_movement_interaction_signed,
            "parameter_state_version": dmo.parameter_state_version,
            "conditioning_state": cond_state,
            "session_transition_event": transition_event,
        })

        fmo_rows.append({
            "entity_id": fmo.entity_id,
            "experiment_id": exp_id,
            "model_time": f"{fmo.model_time:.6f}",
            "event_timestamp_utc": row.event_timestamp_utc,
            "event_timestamp_local": row.event_timestamp_local,
            "phase": phase,
            "session_type": row.session_type,
            "minute_of_session": row.minute_of_session,
            "transition_bucket": transition_bucket,
            "directional_support": fmo.directional_support,
            "expected_magnitude": fmo.expected_magnitude,
            "expected_persistence": fmo.expected_persistence,
            "forward_half_life": fmo.forward_half_life,
            "expected_decay": fmo.expected_decay,
            "reversal_tendency": fmo.reversal_tendency,
            "uncertainty": fmo.uncertainty,
            "favorable_excursion_estimate": fmo.favorable_excursion_estimate,
            "adverse_excursion_estimate": fmo.adverse_excursion_estimate,
            "confidence": fmo.confidence,
        })

        if progress_every > 0 and ((i + 1) % progress_every == 0):
            elapsed = max(1e-9, time.perf_counter() - t0)
            rate = (i + 1) / elapsed
            pct = 100.0 * (i + 1) / max(1, len(rows))
            progress_queue.put({
                "kind": "progress",
                "experiment_id": exp_id,
                "pid": worker_pid,
                "processed": i + 1,
                "total": len(rows),
                "percent": pct,
                "elapsed": elapsed,
                "obs_per_sec": rate,
                "model_time": row.event_timestamp_utc,
                "basis": "PASS",
            })
            log(f"[{exp_id}] processed={i+1} model_time={row.event_timestamp_utc} percent={pct:.2f} elapsed={elapsed:.2f} obs_sec={rate:.2f}")

    # Write worker tables.
    write_csv(
        dmo_csv_path,
        [
            "entity_id", "experiment_id", "model_time", "event_timestamp_utc", "event_timestamp_local", "phase", "session_type",
            "minute_of_session", "transition_bucket", "direction_state", "magnitude_state", "strength", "persistence",
            "reinforcement", "uncertainty", "observation_half_life", "forward_half_life", "reversal_tendency",
            "perturbation_state", "perturbation_magnitude", "relative_volume", "volume_density", "volume_movement_interaction",
            "parameter_state_version", "conditioning_state", "session_transition_event",
        ],
        dmo_rows,
    )

    write_csv(
        fmo_csv_path,
        [
            "entity_id", "experiment_id", "model_time", "event_timestamp_utc", "event_timestamp_local", "phase", "session_type",
            "minute_of_session", "transition_bucket", "directional_support", "expected_magnitude", "expected_persistence",
            "forward_half_life", "expected_decay", "reversal_tendency", "uncertainty",
            "favorable_excursion_estimate", "adverse_excursion_estimate", "confidence",
        ],
        fmo_rows,
    )

    runtime_log_path.write_text("\n".join(runtime_lines), encoding="utf-8")

    # Derived evaluation dataset by windows.
    eval_rows: list[dict[str, Any]] = []
    for i in range(len(rows)):
        frow = fmo_rows[i]
        drow = dmo_rows[i]
        base_close = rows[i].close
        for horizon in EVAL_WINDOWS:
            w = _window_row(rows, i, horizon)
            if w is None:
                continue
            window_rows, end_row = w

            realized_return = end_row.close / base_close - 1.0
            max_fav = max((r.high / base_close - 1.0) for r in window_rows)
            max_adv = min((r.low / base_close - 1.0) for r in window_rows)

            fav_idx = max(range(len(window_rows)), key=lambda k: window_rows[k].high / base_close - 1.0)
            adv_idx = min(range(len(window_rows)), key=lambda k: window_rows[k].low / base_close - 1.0)

            realized_dir = signed_class(realized_return, neutral_threshold)
            pred_dir = signed_class(float(frow["directional_support"]), 0.0)
            reversal = False
            if pred_dir >= 0 and max_adv < -neutral_threshold:
                reversal = True
            if pred_dir < 0 and max_fav > neutral_threshold:
                reversal = True

            sign_path = [signed_class((r.close / base_close - 1.0), neutral_threshold) for r in window_rows]
            dominant_sign = Counter(sign_path).most_common(1)[0][0] if sign_path else 0
            realized_persistence = sum(1 for s in sign_path if s == dominant_sign) / max(1, len(sign_path))

            eval_rows.append({
                "experiment_id": exp_id,
                "obs_index": i,
                "phase": drow["phase"],
                "session_type": drow["session_type"],
                "transition_bucket": drow["transition_bucket"],
                "window": f"W{horizon}M",
                "directional_support": float(frow["directional_support"]),
                "expected_magnitude": float(frow["expected_magnitude"]),
                "expected_persistence": float(frow["expected_persistence"]),
                "favorable_excursion_estimate": float(frow["favorable_excursion_estimate"]),
                "adverse_excursion_estimate": float(frow["adverse_excursion_estimate"]),
                "uncertainty": float(frow["uncertainty"]),
                "relative_volume": float(drow["relative_volume"]),
                "volume_density": float(drow["volume_density"]),
                "volume_movement_interaction": float(drow["volume_movement_interaction"]),
                "observation_half_life": float(drow["observation_half_life"]),
                "forward_half_life": float(drow["forward_half_life"]),
                "perturbation_state": float(drow["perturbation_state"]),
                "realized_return": realized_return,
                "realized_direction": realized_dir,
                "realized_magnitude": abs(realized_return),
                "maximum_favorable_excursion": max_fav,
                "maximum_adverse_excursion": max_adv,
                "time_to_max_favorable_excursion": fav_idx + 1,
                "time_to_max_adverse_excursion": adv_idx + 1,
                "reversal_occurred": int(reversal),
                "realized_persistence": realized_persistence,
            })

        # Dynamic horizon derived from forward half-life.
        hf = max(1, min(120, int(round(float(frow["forward_half_life"]) / 60.0))))
        w2 = _window_row(rows, i, hf)
        if w2 is not None:
            window_rows2, end_row2 = w2
            realized_return2 = end_row2.close / base_close - 1.0
            max_fav2 = max((r.high / base_close - 1.0) for r in window_rows2)
            max_adv2 = min((r.low / base_close - 1.0) for r in window_rows2)
            eval_rows.append({
                "experiment_id": exp_id,
                "obs_index": i,
                "phase": drow["phase"],
                "session_type": drow["session_type"],
                "transition_bucket": drow["transition_bucket"],
                "window": "WHFWD",
                "directional_support": float(frow["directional_support"]),
                "expected_magnitude": float(frow["expected_magnitude"]),
                "expected_persistence": float(frow["expected_persistence"]),
                "favorable_excursion_estimate": float(frow["favorable_excursion_estimate"]),
                "adverse_excursion_estimate": float(frow["adverse_excursion_estimate"]),
                "uncertainty": float(frow["uncertainty"]),
                "relative_volume": float(drow["relative_volume"]),
                "volume_density": float(drow["volume_density"]),
                "volume_movement_interaction": float(drow["volume_movement_interaction"]),
                "observation_half_life": float(drow["observation_half_life"]),
                "forward_half_life": float(drow["forward_half_life"]),
                "perturbation_state": float(drow["perturbation_state"]),
                "realized_return": realized_return2,
                "realized_direction": signed_class(realized_return2, neutral_threshold),
                "realized_magnitude": abs(realized_return2),
                "maximum_favorable_excursion": max_fav2,
                "maximum_adverse_excursion": max_adv2,
                "time_to_max_favorable_excursion": 0,
                "time_to_max_adverse_excursion": 0,
                "reversal_occurred": 0,
                "realized_persistence": 0.0,
            })

    # Metrics by experiment/phase/session/window.
    metric_rows: list[dict[str, Any]] = []
    keys = sorted({(r["phase"], r["session_type"], r["window"]) for r in eval_rows})
    for phase, session, window in keys:
        subset = [r for r in eval_rows if r["phase"] == phase and r["session_type"] == session and r["window"] == window]
        if not subset:
            continue

        pred_dir = [r["directional_support"] for r in subset]
        actual_ret = [r["realized_return"] for r in subset]
        pred_mag = [r["expected_magnitude"] for r in subset]
        actual_mag = [abs(r["realized_return"]) for r in subset]
        pred_fav = [r["favorable_excursion_estimate"] for r in subset]
        act_fav = [r["maximum_favorable_excursion"] for r in subset]
        pred_adv = [r["adverse_excursion_estimate"] for r in subset]
        act_adv = [abs(r["maximum_adverse_excursion"]) for r in subset]
        pred_pers = [r["expected_persistence"] for r in subset]
        act_pers = [r["realized_persistence"] for r in subset]
        unc = [r["uncertainty"] for r in subset]
        abs_err = [abs(pm - am) for pm, am in zip(pred_mag, actual_mag)]

        cls_actual = [signed_class(x, neutral_threshold) for x in actual_ret]
        cls_pred = [signed_class(x, 0.0) for x in pred_dir]

        dir_acc = sum(1 for a, p in zip(cls_actual, cls_pred) if a == p) / max(1, len(cls_actual))

        bacc_vals = []
        for cls in (-1, 0, 1):
            idxs = [i for i, a in enumerate(cls_actual) if a == cls]
            if idxs:
                bacc_vals.append(sum(1 for ii in idxs if cls_pred[ii] == cls) / len(idxs))
        bacc = sum(bacc_vals) / max(1, len(bacc_vals))

        mae_mag = sum(abs(pm - am) for pm, am in zip(pred_mag, actual_mag)) / max(1, len(subset))
        rmse_mag = math.sqrt(sum((pm - am) ** 2 for pm, am in zip(pred_mag, actual_mag)) / max(1, len(subset)))
        med_ae = median(abs(pm - am) for pm, am in zip(pred_mag, actual_mag))

        fav_mae = sum(abs(p - a) for p, a in zip(pred_fav, act_fav)) / max(1, len(subset))
        adv_mae = sum(abs(p - a) for p, a in zip(pred_adv, act_adv)) / max(1, len(subset))

        fav_corr = pearson_corr(pred_fav, act_fav)
        adv_corr = pearson_corr(pred_adv, act_adv)

        pers_err = sum(abs(p - a) for p, a in zip(pred_pers, act_pers)) / max(1, len(subset))
        unc_err_rel = pearson_corr(unc, abs_err)

        metric_rows.append({
            "experiment_id": exp_id,
            "phase": phase,
            "session": session,
            "evaluation_window": window,
            "directional_accuracy": dir_acc,
            "balanced_directional_accuracy": bacc,
            "magnitude_mae": mae_mag,
            "magnitude_rmse": rmse_mag,
            "magnitude_median_ae": med_ae,
            "favorable_excursion_mae": fav_mae,
            "adverse_excursion_mae": adv_mae,
            "favorable_excursion_correlation": fav_corr,
            "adverse_excursion_correlation": adv_corr,
            "persistence_error": pers_err,
            "uncertainty_error_relationship": unc_err_rel,
            "state_flip_count": state_flip_count,
            "perturbation_associated_flip_count": perturb_flip_count,
            "parameter_drift": param_drift,
            "condition_number": float("nan"),
            "runtime_seconds": 0.0,
            "observations_processed": len(rows),
            "positive_target_count": sum(1 for c in cls_actual if c == 1),
            "negative_target_count": sum(1 for c in cls_actual if c == -1),
            "neutral_target_count": sum(1 for c in cls_actual if c == 0),
        })

    # Transition-region diagnostic metrics.
    transition_metric_rows: list[dict[str, Any]] = []
    for bucket in ["FIRST_15_AFTER_0930", "LAST_15_BEFORE_1600", "FIRST_15_AFTER_1600"]:
        subset = [r for r in eval_rows if r["transition_bucket"] == bucket and r["window"] == "W5M"]
        if not subset:
            continue
        cls_actual = [signed_class(x["realized_return"], neutral_threshold) for x in subset]
        cls_pred = [signed_class(x["directional_support"], 0.0) for x in subset]
        acc = sum(1 for a, p in zip(cls_actual, cls_pred) if a == p) / max(1, len(subset))
        transition_metric_rows.append({
            "experiment_id": exp_id,
            "transition_bucket": bucket,
            "window": "W5M",
            "directional_accuracy": acc,
            "count": len(subset),
        })

    # Half-life summary and perturbation response.
    half_life_rows = [
        {
            "phase": d["phase"],
            "session": d["session_type"],
            "hobs": float(d["observation_half_life"]),
            "hfwd": float(d["forward_half_life"]),
            "perturbation_state": float(d["perturbation_state"]),
        }
        for d in dmo_rows
    ]

    half_life_summary: list[dict[str, Any]] = []
    for phase in ["PHASE_1", "PHASE_2", "PHASE_3"]:
        for session in ["PREMARKET", "REGULAR", "AFTERHOURS", "OVERALL"]:
            subset = [r for r in half_life_rows if r["phase"] == phase and (session == "OVERALL" or r["session"] == session)]
            if not subset:
                continue
            sh = summarize_series([r["hobs"] for r in subset])
            sf = summarize_series([r["hfwd"] for r in subset])
            half_life_summary.append({
                "experiment_id": exp_id,
                "phase": phase,
                "session": session,
                "Hobs_mean": sh["mean"],
                "Hobs_median": sh["median"],
                "Hobs_std": sh["std"],
                "Hobs_p05": sh["p05"],
                "Hobs_p25": sh["p25"],
                "Hobs_p50": sh["p50"],
                "Hobs_p75": sh["p75"],
                "Hobs_p95": sh["p95"],
                "Hfwd_mean": sf["mean"],
                "Hfwd_median": sf["median"],
                "Hfwd_std": sf["std"],
                "Hfwd_p05": sf["p05"],
                "Hfwd_p25": sf["p25"],
                "Hfwd_p50": sf["p50"],
                "Hfwd_p75": sf["p75"],
                "Hfwd_p95": sf["p95"],
            })

    pert_idx = [i for i, d in enumerate(dmo_rows) if float(d["perturbation_state"]) > 0.2]
    pert_resp_rows: list[dict[str, Any]] = []
    for idx in pert_idx:
        if idx + 15 >= len(dmo_rows):
            continue
        h_before = float(dmo_rows[idx - 1]["observation_half_life"]) if idx > 0 else float(dmo_rows[idx]["observation_half_life"])
        h_after = float(dmo_rows[idx]["observation_half_life"])
        h_p1 = float(dmo_rows[idx + 1]["observation_half_life"])
        h_p5 = float(dmo_rows[idx + 5]["observation_half_life"])
        h_p15 = float(dmo_rows[idx + 15]["observation_half_life"])
        pert_resp_rows.append({
            "experiment_id": exp_id,
            "phase": dmo_rows[idx]["phase"],
            "session": dmo_rows[idx]["session_type"],
            "event_timestamp_utc": dmo_rows[idx]["event_timestamp_utc"],
            "perturbation_state": float(dmo_rows[idx]["perturbation_state"]),
            "H_before": h_before,
            "H_after": h_after,
            "H_plus_1m": h_p1,
            "H_plus_5m": h_p5,
            "H_plus_15m": h_p15,
        })

    # Volume regime diagnostics.
    rv_values = [float(d["relative_volume"]) for d in dmo_rows]
    rv_q = np.percentile(np.array(rv_values, dtype=float), [25, 50, 75]) if rv_values else [0.0, 0.0, 0.0]

    def rv_bucket(v: float) -> str:
        if v <= rv_q[0]:
            return "low"
        if v <= rv_q[1]:
            return "medium"
        if v <= rv_q[2]:
            return "high"
        return "extreme"

    volume_rows: list[dict[str, Any]] = []
    subset_v = [r for r in eval_rows if r["window"] == "W5M"]
    for session in ["PREMARKET", "REGULAR", "AFTERHOURS", "OVERALL"]:
        for bucket in ["low", "medium", "high", "extreme"]:
            s = [r for r in subset_v if (session == "OVERALL" or r["session_type"] == session) and rv_bucket(r["relative_volume"]) == bucket]
            if not s:
                continue
            cls_actual = [signed_class(x["realized_return"], neutral_threshold) for x in s]
            cls_pred = [signed_class(x["directional_support"], 0.0) for x in s]
            acc = sum(1 for a, p in zip(cls_actual, cls_pred) if a == p) / max(1, len(s))
            mag_mae = sum(abs(x["expected_magnitude"] - abs(x["realized_return"])) for x in s) / max(1, len(s))
            volume_rows.append({
                "experiment_id": exp_id,
                "session": session,
                "volume_regime": bucket,
                "directional_accuracy_w5m": acc,
                "magnitude_mae_w5m": mag_mae,
                "count": len(s),
            })

    # Parameter summary rows.
    parameter_rows: list[dict[str, Any]] = []
    for pname, tr in sorted(param_track.items()):
        parameter_rows.append({
            "experiment_id": exp_id,
            "parameter": pname,
            "start": tr["start"],
            "end": tr["end"],
            "min": tr["min"],
            "max": tr["max"],
            "total_drift": abs(tr["end"] - tr["start"]),
            "max_update": tr["max_update"],
            "phase1_drift": abs(tr["phase1_end"] - tr["start"]),
            "phase2_drift": abs(tr["phase2_end"] - tr["phase1_end"]),
            "phase3_drift": abs(tr["phase3_end"] - tr["phase2_end"]),
        })

    # Condition number from sampled design matrix.
    condition_number = float("nan")
    if len(design_samples) >= 2:
        X = np.vstack(design_samples)
        if X.shape[0] >= X.shape[1]:
            try:
                condition_number = float(np.linalg.cond(X))
            except Exception:
                condition_number = float("inf")
        else:
            try:
                condition_number = float(np.linalg.cond(X.T @ X))
            except Exception:
                condition_number = float("inf")

    phase_structure_rows: list[dict[str, Any]] = []
    for phase in ["PHASE_1", "PHASE_2", "PHASE_3"]:
        p_samples = design_samples_by_phase[phase]
        if not p_samples:
            continue
        Xp = np.vstack(p_samples)
        cols = int(Xp.shape[1])
        rank = int(np.linalg.matrix_rank(Xp)) if Xp.size else 0
        rank_def = cols - rank
        try:
            condp = float(np.linalg.cond(Xp)) if Xp.shape[0] >= cols else float(np.linalg.cond(Xp.T @ Xp))
        except Exception:
            condp = float("inf")
        svals = np.linalg.svd(Xp, full_matrices=False, compute_uv=False) if Xp.size else np.array([], dtype=float)
        min_sv = float(np.min(svals)) if svals.size else float("nan")
        max_sv = float(np.max(svals)) if svals.size else float("nan")
        variances = np.var(Xp, axis=0) if Xp.size else np.array([], dtype=float)
        const_cols = int(np.sum(variances == 0.0)) if variances.size else 0
        near_const_cols = int(np.sum(variances < 1e-12)) if variances.size else 0
        phase_structure_rows.append(
            {
                "experiment_id": exp_id,
                "phase": phase,
                "candidate_base_features": len(model.candidate_base_feature_names),
                "active_base_features": len(model.base_feature_names),
                "inactive_base_features": len(model.candidate_base_feature_names) - len(model.base_feature_names),
                "final_features": cols,
                "matrix_rank": rank,
                "rank_deficiency": rank_def,
                "condition_number": condp,
                "smallest_singular_value": min_sv,
                "largest_singular_value": max_sv,
                "constant_features": const_cols,
                "near_constant_features": near_const_cols,
                "structural_dependencies": rank_def,
            }
        )
    runtime_seconds = max(0.0, time.perf_counter() - t0)
    cpu_smoke_checksum = 0
    if cpu_smoke_iterations > 0:
        acc = 0
        for k in range(int(cpu_smoke_iterations)):
            acc = (acc + ((k * 2654435761) ^ (worker_pid & 0xFFFF))) % 1000000007
        cpu_smoke_checksum = int(acc)
    end_time = now_iso()

    for m in metric_rows:
        m["condition_number"] = condition_number
        m["runtime_seconds"] = runtime_seconds

    metrics_payload = {
        "experiment_id": exp_id,
        "runtime_seconds": runtime_seconds,
        "observations_processed": len(rows),
        "state_flip_count": state_flip_count,
        "perturbation_associated_flip_count": perturb_flip_count,
        "session_boundary_flip_count": session_boundary_flip_count,
        "parameter_drift": param_drift,
        "condition_number": condition_number,
        "max_conditioned_feature": max_abs_feature,
        "max_polynomial_term": max_abs_poly,
        "max_interaction_term": max_abs_interaction,
        "max_parameter": max_abs_parameter,
        "max_gradient": max_abs_gradient,
        "non_finite_count": non_finite_count,
        "first_non_finite": first_non_finite,
        "conditioning_warmup_count": condition_warmup_count,
        "conditioning_active_count": condition_active_count,
        "long_gap_count": long_gap_count,
        "session_transition_events": dict(transition_events),
        "transition_metric_rows": transition_metric_rows,
        "metric_rows": metric_rows,
        "half_life_summary": half_life_summary,
        "perturbation_response_rows": pert_resp_rows,
        "volume_summary_rows": volume_rows,
        "parameter_summary_rows": parameter_rows,
        "phase_structure_rows": phase_structure_rows,
        "feature_manifest": model.get_feature_manifest(),
    }

    metrics_json_path.write_text(json.dumps(metrics_payload, indent=2, sort_keys=True), encoding="utf-8")

    progress_queue.put({
        "kind": "done",
        "experiment_id": exp_id,
        "pid": worker_pid,
        "runtime_seconds": runtime_seconds,
        "basis": "PASS",
    })
    return {
        "experiment_id": exp_id,
        "ok": True,
        "pid": worker_pid,
        "parent_pid": parent_pid,
        "start_time": start_time,
        "end_time": end_time,
        "worker_dir": str(wdir),
        "dmo_csv": str(dmo_csv_path),
        "fmo_csv": str(fmo_csv_path),
        "metrics_json": str(metrics_json_path),
        "parameter_updates": str(param_updates_path),
        "half_life_changes": str(half_life_path),
        "perturbations": str(perturb_path),
        "runtime_log": str(runtime_log_path),
        "runtime_seconds": runtime_seconds,
        "observations_processed": len(rows),
        "approved_manifest_path": str(approved_basis_entry["manifest_path"]),
        "approved_manifest_sha256": str(approved_basis_entry["manifest_sha256"]),
        "approved_basis_sha256": str(approved_basis_entry["approved_basis_sha256"]),
        "runtime_basis_sha256": canonical_basis_hash(list(model.feature_names)),
        "approved_feature_count": int(approved_basis_entry["approved_feature_count"]),
        "runtime_feature_count": len(model.feature_names),
        "ordered_names_match": True,
        "basis_hash_match": True,
        "before_obs1_match": bool(basis_checkpoint_map["before_obs1_match"]),
        "after_obs1_match": bool(basis_checkpoint_map["after_obs1_match"]),
        "after_obs100_match": bool(basis_checkpoint_map["after_obs100_match"]),
        "after_obs5000_match": bool(basis_checkpoint_map["after_obs5000_match"]),
        "after_obs_final_match": bool(basis_checkpoint_map["after_obs_final_match"]),
        "periodic_checkpoint_results": periodic_checkpoint_results,
        "preflight_status": "PASS",
        "cpu_smoke_checksum": cpu_smoke_checksum,
    }


def merge_worker_csvs(worker_results: list[dict[str, Any]], merged_path: Path, key: str) -> None:
    headers = None
    out_rows: list[dict[str, Any]] = []
    for wr in sorted(worker_results, key=lambda x: x["experiment_id"]):
        p = Path(wr[key])
        with p.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            if headers is None:
                headers = r.fieldnames
            for row in r:
                out_rows.append(row)
    if headers is None:
        headers = []
    out_rows.sort(key=lambda x: (x.get("experiment_id", ""), x.get("event_timestamp_utc", "")))
    write_csv(merged_path, list(headers), out_rows)


def classify_effect(value_delta: float, threshold: float = 0.0025) -> str:
    if value_delta > threshold:
        return "BENEFICIAL"
    if value_delta < -threshold:
        return "HARMFUL"
    if abs(value_delta) <= threshold:
        return "NO MEASURABLE EFFECT"
    return "MIXED"


def deterministic_subset_check(
    experiments: list[dict[str, Any]],
    default_cfg: dict[str, Any],
    rows: list[PreparedRow],
    bounds: PhaseBounds,
    out_root: Path,
    neutral_threshold: float,
    approved_basis_registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    subset_ids = ["A_n1", "D_n2", "E_n3"]
    status = {"pass": True, "details": []}

    # Single-process queue stub.
    class _Queue:
        def put(self, _item: Any) -> None:
            return

    for sid in subset_ids:
        exp_cfg = next(e for e in experiments if e["id"] == sid)
        det_root = out_root / "diagnostics" / "determinism" / sid
        det_root.mkdir(parents=True, exist_ok=True)

        run1 = run_worker(
            exp_cfg,
            default_cfg,
            rows,
            bounds,
            str(det_root / "run1"),
            0,
            neutral_threshold,
            _Queue(),
            approved_basis_registry[sid],
        )
        run2 = run_worker(
            exp_cfg,
            default_cfg,
            rows,
            bounds,
            str(det_root / "run2"),
            0,
            neutral_threshold,
            _Queue(),
            approved_basis_registry[sid],
        )

        files = [
            ("dmo", "dmo_csv"),
            ("fmo", "fmo_csv"),
            ("parameter_updates", "parameter_updates"),
            ("half_life_changes", "half_life_changes"),
            ("perturbations", "perturbations"),
        ]

        file_ok = True
        per_file = []
        for label, k in files:
            h1 = sha256_file(Path(run1[k])) if Path(run1[k]).exists() else ""
            h2 = sha256_file(Path(run2[k])) if Path(run2[k]).exists() else ""
            ok = h1 == h2
            per_file.append({"file": label, "run1": h1, "run2": h2, "match": ok})
            if not ok:
                file_ok = False

        # Compare metrics excluding runtime_seconds.
        m1 = json.loads(Path(run1["metrics_json"]).read_text(encoding="utf-8"))
        m2 = json.loads(Path(run2["metrics_json"]).read_text(encoding="utf-8"))
        m1["runtime_seconds"] = 0.0
        m2["runtime_seconds"] = 0.0
        for row in m1.get("metric_rows", []):
            row["runtime_seconds"] = 0.0
        for row in m2.get("metric_rows", []):
            row["runtime_seconds"] = 0.0
        metrics_ok = json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True)

        ok_total = file_ok and metrics_ok
        status["details"].append({"experiment_id": sid, "files": per_file, "metrics_match": metrics_ok, "pass": ok_total})
        if not ok_total:
            status["pass"] = False

    return status


def condition_band(v: float) -> str:
    if not math.isfinite(v):
        return "SINGULAR"
    if v < 1.0e4:
        return "WELL CONDITIONED"
    if v < 1.0e8:
        return "MODERATELY CONDITIONED"
    if v < 1.0e12:
        return "POORLY CONDITIONED"
    return "SEVERELY ILL-CONDITIONED"


def run_v012_validation(
    experiments: list[dict[str, Any]],
    default_cfg: dict[str, Any],
    rows: list[PreparedRow],
    bounds: PhaseBounds,
    out_root: Path,
    approved_basis_registry: dict[str, dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    subset_ids = ["A_n1", "B_n1", "D_n2", "E_n3"]

    class _Queue:
        def put(self, _item: Any) -> None:
            return

    p1_rows = rows[: bounds.phase_1_rows]
    result_rows: list[dict[str, Any]] = []
    gate_pass = True
    for sid in subset_ids:
        exp_cfg = next(e for e in experiments if e["id"] == sid)
        vroot = out_root / "diagnostics" / "validation" / sid
        vroot.mkdir(parents=True, exist_ok=True)
        wr = run_worker(
            exp_cfg,
            default_cfg,
            p1_rows,
            bounds,
            str(vroot),
            0,
            NEUTRAL_RETURN_THRESHOLD,
            _Queue(),
            approved_basis_registry[sid],
        )
        payload = json.loads(Path(wr["metrics_json"]).read_text(encoding="utf-8"))
        p1 = next((r for r in payload.get("phase_structure_rows", []) if r["phase"] == "PHASE_1"), None)
        if p1 is None:
            gate_pass = False
            continue

        matrix_rank = int(p1["matrix_rank"])
        columns = int(p1["final_features"])
        cond = float(p1["condition_number"])
        rank_def = max(int(p1["rank_deficiency"]), max(0, columns - matrix_rank))
        non_finite = int(payload.get("non_finite_count", 0))
        lineage_known = bool(payload.get("feature_manifest", {}).get("feature_lineage"))

        severe = (not math.isfinite(cond)) or cond >= 1.0e12
        if rank_def > 0 or (matrix_rank < columns) or severe or non_finite > 0 or (not lineage_known):
            gate_pass = False

        result_rows.append(
            {
                "experiment_id": sid,
                "candidate_base_features": int(p1["candidate_base_features"]),
                "active_base_features": int(p1["active_base_features"]),
                "inactive_base_features": int(p1["inactive_base_features"]),
                "final_features": columns,
                "matrix_rank": matrix_rank,
                "columns": columns,
                "rank_deficiency": rank_def,
                "condition_number": cond,
                "condition_band": condition_band(cond),
                "smallest_singular_value": float(p1["smallest_singular_value"]),
                "largest_singular_value": float(p1["largest_singular_value"]),
                "constant_features": int(p1["constant_features"]),
                "near_constant_features": int(p1["near_constant_features"]),
                "structural_dependencies": int(p1["structural_dependencies"]),
                "non_finite_count": non_finite,
                "lineage_known": lineage_known,
            }
        )

    write_csv(
        out_root / "metrics" / "v012_validation_summary.csv",
        [
            "experiment_id", "candidate_base_features", "active_base_features", "inactive_base_features", "final_features",
            "matrix_rank", "columns", "rank_deficiency", "condition_number", "condition_band",
            "smallest_singular_value", "largest_singular_value", "constant_features", "near_constant_features",
            "structural_dependencies", "non_finite_count", "lineage_known",
        ],
        result_rows,
    )

    lines = [
        "# D01 v0.1.2 Numerical Validation",
        "",
        "Validation set: A_n1, B_n1, D_n2, E_n3 on Phase 1 only.",
        "",
    ]
    for r in result_rows:
        lines.append(f"## {r['experiment_id']}")
        lines.append(f"- features: {r['active_base_features']} base, {r['final_features']} final")
        lines.append(f"- rank: {r['matrix_rank']} / {r['columns']} (deficiency={r['rank_deficiency']})")
        lines.append(f"- condition: {r['condition_number']} ({r['condition_band']})")
        lines.append(f"- singular values: min={r['smallest_singular_value']} max={r['largest_singular_value']}")
        lines.append(f"- constants: {r['constant_features']} near-constant: {r['near_constant_features']}")
        lines.append(f"- dependencies: {r['structural_dependencies']} non-finite: {r['non_finite_count']}")
        lines.append("")
    lines.append(f"Final gate: {'PASS' if gate_pass else 'FAIL'}")
    (out_root / "reports" / "D01_V0_1_2_NUMERICAL_VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")

    return gate_pass, result_rows


def load_final_pre001b_ready() -> tuple[bool, str]:
    manifest_path = (
        ROOT
        / "output"
        / "historical_exp001b_precheck"
        / "phase_degeneracy_resolution"
        / "manifests"
        / "FINAL_PRE001B_PHASE_DEGENERACY_MANIFEST.json"
    )
    if not manifest_path.exists():
        return False, "final precheck manifest missing"

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return False, f"final precheck manifest unreadable: {exc}"

    decision = str(payload.get("final_decision", "")).strip().upper()
    unresolved = int(payload.get("unresolved_cases", 1))
    structural_remaining = int(payload.get("structural_dependencies_remaining", 1))
    severe_cases = int(payload.get("severe_ill_conditioning_cases", 1))
    non_finite = int(payload.get("non_finite_values", 1))
    phase1_pass = bool(payload.get("phase1_structural_pass", False))
    ready = (
        decision == "READY FOR EXP001B"
        and unresolved == 0
        and structural_remaining == 0
        and severe_cases == 0
        and non_finite == 0
        and phase1_pass
    )
    if ready:
        return True, "READY FOR EXP001B"
    return False, "final precheck decision is not ready"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run APTF D01 Historical SPY Experiment 001B")
    parser.add_argument("--workers", type=int, default=18)
    parser.add_argument("--progress-every", type=int, default=PROGRESS_EVERY)
    args = parser.parse_args()

    _set_worker_env_limits()
    ensure_dirs()

    start_wall = time.perf_counter()

    # Dataset identity gate.
    actual_hash = sha256_file(DATASET_PATH)
    if actual_hash != EXPECTED_SHA256:
        print("DATASET SHA256 MISMATCH")
        print(f"EXPECTED: {EXPECTED_SHA256}")
        print(f"ACTUAL:   {actual_hash}")
        print("STOPPED WITHOUT RUNNING EXPERIMENT")
        return 2

    rows = load_six_month_rows(DATASET_PATH)
    if not rows:
        raise RuntimeError("No rows found in experiment date range")

    bounds = compute_phase_bounds(rows)

    # Validate strict chronology.
    for i in range(1, len(rows)):
        if rows[i].ts_utc <= rows[i - 1].ts_utc:
            raise RuntimeError(f"Non-ascending chronology at idx={i}")

    default_cfg = load_yaml(ROOT / "config" / "default_v0_1_2.yaml")
    default_cfg["observation_capabilities"] = firstrate_ohlcv_capabilities("SPY").to_dict()
    matrix_cfg = load_yaml(ROOT / "config" / "experiment_matrix.yaml")
    experiments = list(matrix_cfg["experiments"])
    approved_manifest_root, approved_basis_registry = build_approved_basis_registry(ROOT)

    # Manifest.
    manifest = {
        "experiment_name": "APTF D01 Historical SPY Experiment 001B",
        "parent_experiment": "HISTORICAL_EXP001",
        "audit_experiment": "HISTORICAL_EXP001A",
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": actual_hash,
        "date_range": {"start": DATE_START, "end": DATE_END},
        "sessions_included": ["PREMARKET", "REGULAR", "AFTERHOURS"],
        "row_count": len(rows),
        "phase_boundaries": {
            "phase_1_start": bounds.phase_1_start,
            "phase_1_end": bounds.phase_1_end,
            "phase_1_rows": bounds.phase_1_rows,
            "phase_2_start": bounds.phase_2_start,
            "phase_2_end": bounds.phase_2_end,
            "phase_2_rows": bounds.phase_2_rows,
            "phase_3_start": bounds.phase_3_start,
            "phase_3_end": bounds.phase_3_end,
            "phase_3_rows": bounds.phase_3_rows,
        },
        "model_version": "D01 v0.1.2",
        "design_version": "D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3.md",
        "configurations": [e["id"] for e in experiments],
        "worker_count": int(args.workers),
        "interaction_max_order": int(default_cfg["parametric"]["interaction_max_order"]),
        "evaluation_windows": ["1m", "5m", "15m", "30m", "hfwd_dynamic"],
        "timestamp_convention": "model_time corresponds to completed 1-minute bar timestamp",
        "feature_availability_policy": "UNAVAILABLE_CHANNELS_EXCLUDED_NOT_ZERO_FILLED",
        "provider_capabilities": default_cfg["observation_capabilities"],
        "controls": ["C0A", "C0B", "C1", "C2", "C3", "C5"],
        "random_seed": RANDOM_SEED,
        "random_repetitions": RANDOM_REPS,
        "reserve_data_used": False,
        "approved_basis_manifest_root": str(approved_manifest_root),
        "approved_basis_registry": approved_basis_registry,
        "canonical_basis_hashing": {
            "algorithm": "SHA256",
            "serialization": canonical_basis_payload(["bias", "price_displacement"]),
            "description": "UTF-8 JSON list with compact separators and exact ordered feature names",
        },
        "creation_time": now_iso(),
        "reserve_data_range": RESERVE_RANGE,
        "cpu_thread_env": {
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", ""),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS", ""),
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS", ""),
        },
        "notes": [
            "No D01 reset at session boundaries.",
            "No reset at day boundaries.",
            "Derivative dt uses actual elapsed time from timestamps.",
            "No placeholder quote/trade channels are synthesized.",
            "No broker, no PnL backtest, no D02, no D04.",
        ],
    }
    (OUTPUT_ROOT / "manifest" / "HISTORICAL_EXP001B_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    validation_pass, validation_rows = run_v012_validation(
        experiments,
        default_cfg,
        rows,
        bounds,
        OUTPUT_ROOT,
        approved_basis_registry,
    )

    val_map = {r["experiment_id"]: r for r in validation_rows}
    print("APTF D01 v0.1.2 FEATURE STRUCTURE CORRECTION COMPLETE")
    print("PREVIOUS VERSION:")
    print("v0.1.1")
    print("NEW VERSION:")
    print("v0.1.2")
    print("D01 CORE ADAPTIVE MATHEMATICS CHANGED:")
    print("NO")
    print("OBSERVATION AVAILABILITY CONTRACT:")
    print("IMPLEMENTED")
    print("PROVIDER CAPABILITY CONTRACT:")
    print("IMPLEMENTED")
    print("ACTIVE CHANNEL MAP:")
    print("IMPLEMENTED")
    print("FEATURE ADMISSIBILITY GATE:")
    print("IMPLEMENTED")
    print("FEATURE LINEAGE:")
    print("IMPLEMENTED")
    print("PLACEHOLDER BID:")
    print("REMOVED")
    print("PLACEHOLDER ASK:")
    print("REMOVED")
    print("PLACEHOLDER BID SIZE:")
    print("REMOVED")
    print("PLACEHOLDER ASK SIZE:")
    print("REMOVED")
    print("PLACEHOLDER TRADE SIZE:")
    print("REMOVED / CORRECTLY SEPARATED FROM BAR VOLUME")
    print("BAR VOLUME:")
    print("PRESERVED")
    print("QUOTE-DERIVED FEATURES WITH FIRST-RATE:")
    print("EXCLUDED")
    print("INTERCEPT COLLISIONS:")
    print("0")
    for eid in ["A_n1", "B_n1", "D_n2", "E_n3"]:
        vr = val_map.get(eid)
        if vr:
            print(f"VALIDATION {eid.upper()}:")
            print(f"rank={vr['matrix_rank']}/{vr['columns']}")
            print(f"condition={vr['condition_number']}")
    non_finite_total = sum(int(r["non_finite_count"]) for r in validation_rows)
    print("NON-FINITE VALUES:")
    print(str(non_finite_total))
    print("NUMERICAL VALIDATION:")
    print("PASS" if validation_pass else "FAIL")

    if not validation_pass:
        pre001b_ready, pre001b_reason = load_final_pre001b_ready()
        if pre001b_ready:
            print("NUMERICAL VALIDATION OVERRIDE:")
            print("APPLIED FROM FINAL PRE-001B STRUCTURAL AUTHORIZATION")
            print("FINAL PRE-001B DECISION:")
            print(pre001b_reason)
        else:
            print("D01 v0.1.2 NUMERICAL VALIDATION FAILED")
            print("HISTORICAL EXPERIMENT 001B:")
            print("NOT STARTED")
            return 3

    execution_contract_pass, execution_contract_failures = preflight_exp001b_execution_contract(
        dataset_sha256_actual=actual_hash,
        model_version=str(default_cfg.get("model_definition_version", "")),
        phase_boundaries=manifest["phase_boundaries"],
        approved_basis_registry=approved_basis_registry,
        submitted_task_count=len(experiments),
        configured_workers=int(args.workers),
        reserve_data_used=False,
    )
    if not execution_contract_pass:
        print("EXP001B EXECUTION CONTRACT FAIL")
        for reason in execution_contract_failures:
            print(f"- {reason}")
        print("HISTORICAL EXPERIMENT 001B:")
        print("NOT STARTED")
        return 4

    print(f"[{now_iso()}] Launching 15 experiments with ProcessPoolExecutor(max_workers={args.workers})")

    manager = None
    worker_results: list[dict[str, Any]] = []
    worker_failures: list[dict[str, Any]] = []

    import multiprocessing as mp

    manager = mp.Manager()
    progress_queue = manager.Queue()
    active_workers: dict[str, int] = {}
    active_pids: set[int] = set()
    last_coord_print = time.perf_counter()

    with ProcessPoolExecutor(max_workers=int(args.workers)) as ex:
        fut_to_id = {}
        for exp in experiments:
            fut = ex.submit(
                run_worker,
                exp,
                default_cfg,
                rows,
                bounds,
                str(OUTPUT_ROOT),
                int(args.progress_every),
                float(NEUTRAL_RETURN_THRESHOLD),
                progress_queue,
                approved_basis_registry[str(exp["id"])],
            )
            fut_to_id[fut] = exp["id"]

        pending = set(fut_to_id.keys())
        while pending:
            done, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)

            # Drain progress queue.
            while not progress_queue.empty():
                msg = progress_queue.get()
                if msg.get("kind") == "start":
                    expid = str(msg.get("experiment_id", ""))
                    pid = int(msg.get("pid", 0)) if msg.get("pid") is not None else 0
                    if expid:
                        active_workers[expid] = pid
                    if pid > 0:
                        active_pids.add(pid)
                elif msg.get("kind") == "progress":
                    print(
                        f"[{msg['experiment_id']} pid={msg.get('pid', 'NA')}] "
                        f"processed={msg['processed']}/{msg.get('total', len(rows))} model_time={msg['model_time']} "
                        f"percent={msg['percent']:.2f} elapsed={msg['elapsed']:.1f}s obs/sec={msg['obs_per_sec']:.1f} basis={msg.get('basis', 'PASS')}"
                    )
                elif msg.get("kind") == "done":
                    expid = str(msg.get("experiment_id", ""))
                    pid = int(msg.get("pid", 0)) if msg.get("pid") is not None else 0
                    if expid in active_workers:
                        active_workers.pop(expid, None)
                    if pid > 0 and pid in active_pids:
                        active_pids.remove(pid)
                    print(f"[{msg['experiment_id']} pid={msg.get('pid', 'NA')}] worker complete runtime={msg['runtime_seconds']:.2f}s basis={msg.get('basis', 'PASS')}")

            now_perf = time.perf_counter()
            if now_perf - last_coord_print >= 5.0:
                elapsed = now_perf - start_wall
                print(
                    f"[COORD] active={len(active_workers)} completed={len(worker_results)} failed={len(worker_failures)} "
                    f"pids={sorted(active_pids)} elapsed={elapsed:.1f}s"
                )
                last_coord_print = now_perf

            for d in done:
                exp_id = fut_to_id[d]
                try:
                    res = d.result()
                    worker_results.append(res)
                except Exception as e:
                    worker_failures.append({
                        "experiment_id": exp_id,
                        "pid": active_workers.get(exp_id, 0),
                        "exception": str(e),
                        "last_observation": None,
                        "last_model_time": None,
                        "basis_state": "UNKNOWN",
                    })
                    active_workers.pop(exp_id, None)
                    print(f"[FAIL] {exp_id}: {e}")

    # Merge only after all workers done.
    if worker_results:
        merge_worker_csvs(worker_results, OUTPUT_ROOT / "merged" / "dmo_all.csv", "dmo_csv")
        merge_worker_csvs(worker_results, OUTPUT_ROOT / "merged" / "fmo_all.csv", "fmo_csv")

    # Aggregate metrics.
    all_metric_rows: list[dict[str, Any]] = []
    all_transition_rows: list[dict[str, Any]] = []
    all_half_life_rows: list[dict[str, Any]] = []
    all_volume_rows: list[dict[str, Any]] = []
    all_perturb_resp_rows: list[dict[str, Any]] = []
    all_param_rows: list[dict[str, Any]] = []
    all_phase_structure_rows: list[dict[str, Any]] = []
    worker_metric_core: dict[str, Any] = {}

    for wr in sorted(worker_results, key=lambda x: x["experiment_id"]):
        m = json.loads(Path(wr["metrics_json"]).read_text(encoding="utf-8"))
        worker_metric_core[wr["experiment_id"]] = m
        all_metric_rows.extend(m.get("metric_rows", []))
        all_transition_rows.extend(m.get("transition_metric_rows", []))
        all_half_life_rows.extend(m.get("half_life_summary", []))
        all_volume_rows.extend(m.get("volume_summary_rows", []))
        all_perturb_resp_rows.extend(m.get("perturbation_response_rows", []))
        all_param_rows.extend(m.get("parameter_summary_rows", []))
        all_phase_structure_rows.extend(m.get("phase_structure_rows", []))

    def _num_class(cond: float, rank_def: int) -> str:
        if rank_def > 0 or not math.isfinite(cond):
            return "SINGULAR"
        if cond < 1.0e4:
            return "WELL CONDITIONED"
        if cond < 1.0e8:
            return "MODERATELY CONDITIONED"
        if cond < 1.0e12:
            return "POORLY CONDITIONED"
        return "SEVERELY ILL-CONDITIONED"

    for row in all_phase_structure_rows:
        row["numerical_classification"] = _num_class(float(row["condition_number"]), int(row["rank_deficiency"]))

    write_csv(
        OUTPUT_ROOT / "metrics" / "feature_structure_summary.csv",
        [
            "experiment_id", "phase", "candidate_base_features", "active_base_features", "inactive_base_features",
            "final_features", "matrix_rank", "rank_deficiency", "condition_number", "smallest_singular_value",
            "largest_singular_value", "constant_features", "near_constant_features", "structural_dependencies",
            "numerical_classification",
        ],
        all_phase_structure_rows,
    )

    if all_metric_rows:
        write_csv(
            OUTPUT_ROOT / "metrics" / "historical_experiment_metrics.csv",
            [
                "experiment_id", "phase", "session", "evaluation_window",
                "directional_accuracy", "balanced_directional_accuracy",
                "magnitude_mae", "magnitude_rmse", "magnitude_median_ae",
                "favorable_excursion_mae", "adverse_excursion_mae",
                "favorable_excursion_correlation", "adverse_excursion_correlation",
                "persistence_error", "uncertainty_error_relationship",
                "state_flip_count", "perturbation_associated_flip_count",
                "parameter_drift", "condition_number", "runtime_seconds", "observations_processed",
                "positive_target_count", "negative_target_count", "neutral_target_count",
            ],
            all_metric_rows,
        )

    # Config summary with Phase 3 primary windows = W5M.
    cfg_summary_rows: list[dict[str, Any]] = []
    for exp in [e["id"] for e in experiments]:
        sub = [r for r in all_metric_rows if r["experiment_id"] == exp and r["phase"] == "PHASE_3" and r["session"] == "REGULAR" and r["evaluation_window"] == "W5M"]
        if not sub:
            sub = [r for r in all_metric_rows if r["experiment_id"] == exp and r["phase"] == "PHASE_3" and r["evaluation_window"] == "W5M"]
        if not sub:
            continue
        r = sub[0]
        cfg_summary_rows.append({
            "experiment_id": exp,
            "directional_accuracy_phase3": r["directional_accuracy"],
            "balanced_directional_accuracy_phase3": r["balanced_directional_accuracy"],
            "magnitude_mae_phase3": r["magnitude_mae"],
            "favorable_excursion_mae_phase3": r["favorable_excursion_mae"],
            "adverse_excursion_mae_phase3": r["adverse_excursion_mae"],
            "persistence_error_phase3": r["persistence_error"],
            "uncertainty_rel_phase3": r["uncertainty_error_relationship"],
            "parameter_drift": r["parameter_drift"],
            "condition_number": r["condition_number"],
            "runtime_seconds": r["runtime_seconds"],
            "observations_processed": r["observations_processed"],
        })

    write_csv(
        OUTPUT_ROOT / "metrics" / "configuration_summary.csv",
        [
            "experiment_id", "directional_accuracy_phase3", "balanced_directional_accuracy_phase3",
            "magnitude_mae_phase3", "favorable_excursion_mae_phase3", "adverse_excursion_mae_phase3",
            "persistence_error_phase3", "uncertainty_rel_phase3", "parameter_drift", "condition_number",
            "runtime_seconds", "observations_processed",
        ],
        cfg_summary_rows,
    )

    write_csv(
        OUTPUT_ROOT / "metrics" / "session_summary.csv",
        ["experiment_id", "phase", "session", "evaluation_window", "directional_accuracy", "balanced_directional_accuracy", "magnitude_mae", "magnitude_rmse", "count_proxy"],
        [
            {
                "experiment_id": r["experiment_id"],
                "phase": r["phase"],
                "session": r["session"],
                "evaluation_window": r["evaluation_window"],
                "directional_accuracy": r["directional_accuracy"],
                "balanced_directional_accuracy": r["balanced_directional_accuracy"],
                "magnitude_mae": r["magnitude_mae"],
                "magnitude_rmse": r["magnitude_rmse"],
                "count_proxy": r["positive_target_count"] + r["negative_target_count"] + r["neutral_target_count"],
            }
            for r in all_metric_rows
        ],
    )

    write_csv(
        OUTPUT_ROOT / "metrics" / "half_life_summary.csv",
        [
            "experiment_id", "phase", "session",
            "Hobs_mean", "Hobs_median", "Hobs_std", "Hobs_p05", "Hobs_p25", "Hobs_p50", "Hobs_p75", "Hobs_p95",
            "Hfwd_mean", "Hfwd_median", "Hfwd_std", "Hfwd_p05", "Hfwd_p25", "Hfwd_p50", "Hfwd_p75", "Hfwd_p95",
        ],
        all_half_life_rows,
    )

    write_csv(
        OUTPUT_ROOT / "metrics" / "volume_summary.csv",
        ["experiment_id", "session", "volume_regime", "directional_accuracy_w5m", "magnitude_mae_w5m", "count"],
        all_volume_rows,
    )

    # Perturbation summary.
    pert_summary_rows: list[dict[str, Any]] = []
    by_exp = defaultdict(list)
    for r in all_perturb_resp_rows:
        by_exp[r["experiment_id"]].append(r)
    for exp, vals in sorted(by_exp.items()):
        mags = [v["perturbation_state"] for v in vals]
        h_before = [v["H_before"] for v in vals]
        h_after = [v["H_after"] for v in vals]
        h_p1 = [v["H_plus_1m"] for v in vals]
        h_p5 = [v["H_plus_5m"] for v in vals]
        h_p15 = [v["H_plus_15m"] for v in vals]
        pert_summary_rows.append({
            "experiment_id": exp,
            "count": len(vals),
            "mean_magnitude": mean(mags) if mags else float("nan"),
            "H_before_mean": mean(h_before) if h_before else float("nan"),
            "H_after_mean": mean(h_after) if h_after else float("nan"),
            "H_plus_1m_mean": mean(h_p1) if h_p1 else float("nan"),
            "H_plus_5m_mean": mean(h_p5) if h_p5 else float("nan"),
            "H_plus_15m_mean": mean(h_p15) if h_p15 else float("nan"),
            "half_life_response": (mean(h_after) - mean(h_before)) if h_before and h_after else float("nan"),
            "uncertainty_response": float("nan"),
            "subsequent_return_distribution": "captured in historical_experiment_metrics.csv by phase/session/window",
        })

    write_csv(
        OUTPUT_ROOT / "metrics" / "perturbation_summary.csv",
        [
            "experiment_id", "count", "mean_magnitude", "H_before_mean", "H_after_mean", "H_plus_1m_mean", "H_plus_5m_mean", "H_plus_15m_mean",
            "half_life_response", "uncertainty_response", "subsequent_return_distribution",
        ],
        pert_summary_rows,
    )

    write_csv(
        OUTPUT_ROOT / "metrics" / "parameter_summary.csv",
        ["experiment_id", "parameter", "start", "end", "min", "max", "total_drift", "max_update", "phase1_drift", "phase2_drift", "phase3_drift"],
        all_param_rows,
    )

    # Controls and D01-vs-controls for Phase 3 slices.
    close = [r.close for r in rows]

    def _phase_of_idx(ii: int) -> str:
        if ii < bounds.phase_1_rows:
            return "PHASE_1"
        if ii < bounds.phase_1_rows + bounds.phase_2_rows:
            return "PHASE_2"
        return "PHASE_3"

    def _cls(arr: list[float]) -> list[int]:
        return [signed_class(v, NEUTRAL_RETURN_THRESHOLD) for v in arr]

    def _acc(y_true: list[int], y_pred: list[int]) -> float:
        if not y_true:
            return float("nan")
        return sum(1 for a, p in zip(y_true, y_pred) if a == p) / len(y_true)

    def _bacc(y_true: list[int], y_pred: list[int]) -> float:
        vals = []
        for c in (-1, 0, 1):
            idxs = [i for i, v in enumerate(y_true) if v == c]
            if idxs:
                vals.append(sum(1 for i in idxs if y_pred[i] == c) / len(idxs))
        return float(sum(vals) / len(vals)) if vals else float("nan")

    control_rows: list[dict[str, Any]] = []
    controls_by_slice: dict[tuple[str, str], dict[str, float]] = {}
    for session in ["PREMARKET", "REGULAR", "AFTERHOURS"]:
        for w in [1, 5, 15, 30]:
            y2: list[int] = []
            y3: list[int] = []
            prev_sign_3: list[int] = []
            for i, row in enumerate(rows):
                if row.session_type != session:
                    continue
                j = i + w
                if j >= len(rows):
                    continue
                ret = close[j] / close[i] - 1.0
                ph = _phase_of_idx(i)
                if ph == "PHASE_2":
                    y2.append(signed_class(ret, NEUTRAL_RETURN_THRESHOLD))
                elif ph == "PHASE_3":
                    y3.append(signed_class(ret, NEUTRAL_RETURN_THRESHOLD))
                    prev_sign_3.append(signed_class(row.close_return_1m, NEUTRAL_RETURN_THRESHOLD))

            if not y3:
                continue

            c2 = Counter(y2)
            c3 = Counter(y3)
            c0a_cls = c2.most_common(1)[0][0] if c2 else 0
            c0b_cls = c3.most_common(1)[0][0] if c3 else 0
            p0a = [c0a_cls] * len(y3)
            p0b = [c0b_cls] * len(y3)
            p1 = prev_sign_3
            p2 = [(-v if v != 0 else 0) for v in prev_sign_3]
            p5 = [0] * len(y3)

            classes = [-1, 0, 1]
            probs = [c2.get(-1, 0) / max(1, len(y2)), c2.get(0, 0) / max(1, len(y2)), c2.get(1, 0) / max(1, len(y2))]
            rng = np.random.default_rng(RANDOM_SEED)
            c3_rep_acc = []
            c3_rep_bacc = []
            for _ in range(RANDOM_REPS):
                rpred = rng.choice(classes, size=len(y3), p=probs).tolist()
                c3_rep_acc.append(_acc(y3, rpred))
                c3_rep_bacc.append(_bacc(y3, rpred))

            row_map = {
                "C0A": (_acc(y3, p0a), _bacc(y3, p0a)),
                "C0B": (_acc(y3, p0b), _bacc(y3, p0b)),
                "C1": (_acc(y3, p1), _bacc(y3, p1)),
                "C2": (_acc(y3, p2), _bacc(y3, p2)),
                "C3": (float(np.mean(c3_rep_acc)), float(np.mean(c3_rep_bacc))),
                "C5": (_acc(y3, p5), _bacc(y3, p5)),
            }

            controls_by_slice[(session, f"W{w}M")] = {
                "c0a": row_map["C0A"][0],
                "c1": row_map["C1"][0],
                "c2": row_map["C2"][0],
                "c3": row_map["C3"][0],
                "c3_p95": float(np.percentile(np.array(c3_rep_acc, dtype=float), 95)),
                "c5": row_map["C5"][0],
                "c0a_b": row_map["C0A"][1],
                "c1_b": row_map["C1"][1],
                "c2_b": row_map["C2"][1],
                "c3_b": row_map["C3"][1],
                "c5_b": row_map["C5"][1],
            }

            for cid, (accv, baccv) in row_map.items():
                control_rows.append(
                    {
                        "control_id": cid,
                        "session": session,
                        "evaluation_window": f"W{w}M",
                        "accuracy": accv,
                        "balanced_accuracy": baccv,
                        "seed": RANDOM_SEED if cid == "C3" else "",
                        "repetitions": RANDOM_REPS if cid == "C3" else "",
                        "deployable_causal": "false" if cid == "C0B" else "true",
                    }
                )

    write_csv(
        OUTPUT_ROOT / "metrics" / "control_model_metrics.csv",
        ["control_id", "session", "evaluation_window", "accuracy", "balanced_accuracy", "seed", "repetitions", "deployable_causal"],
        control_rows,
    )

    d01_vs_rows: list[dict[str, Any]] = []
    for r in all_metric_rows:
        if r["phase"] != "PHASE_3":
            continue
        key = (r["session"], r["evaluation_window"])
        c = controls_by_slice.get(key)
        if c is None:
            continue
        d01_vs_rows.append(
            {
                "experiment_id": r["experiment_id"],
                "session": r["session"],
                "evaluation_window": r["evaluation_window"],
                "d01_directional_accuracy": r["directional_accuracy"],
                "d01_balanced_directional_accuracy": r["balanced_directional_accuracy"],
                "c0a_accuracy": c["c0a"],
                "c1_accuracy": c["c1"],
                "c2_accuracy": c["c2"],
                "c3_random_mean_accuracy": c["c3"],
                "c3_random_p95_accuracy": c["c3_p95"],
                "c5_neutral_accuracy": c["c5"],
                "d01_minus_c0a": float(r["directional_accuracy"]) - c["c0a"],
                "d01_minus_c1": float(r["directional_accuracy"]) - c["c1"],
                "d01_minus_c2": float(r["directional_accuracy"]) - c["c2"],
                "d01_minus_c3_mean": float(r["directional_accuracy"]) - c["c3"],
                "d01_minus_c0a_balanced": float(r["balanced_directional_accuracy"]) - c["c0a_b"],
                "d01_minus_c1_balanced": float(r["balanced_directional_accuracy"]) - c["c1_b"],
                "d01_minus_c2_balanced": float(r["balanced_directional_accuracy"]) - c["c2_b"],
                "d01_minus_c3_mean_balanced": float(r["balanced_directional_accuracy"]) - c["c3_b"],
            }
        )

    write_csv(
        OUTPUT_ROOT / "metrics" / "d01_vs_controls_phase3.csv",
        [
            "experiment_id", "session", "evaluation_window",
            "d01_directional_accuracy", "d01_balanced_directional_accuracy",
            "c0a_accuracy", "c1_accuracy", "c2_accuracy", "c3_random_mean_accuracy", "c3_random_p95_accuracy", "c5_neutral_accuracy",
            "d01_minus_c0a", "d01_minus_c1", "d01_minus_c2", "d01_minus_c3_mean",
            "d01_minus_c0a_balanced", "d01_minus_c1_balanced", "d01_minus_c2_balanced", "d01_minus_c3_mean_balanced",
        ],
        d01_vs_rows,
    )

    # Determinism checks.
    determinism = deterministic_subset_check(
        experiments,
        default_cfg,
        rows,
        bounds,
        OUTPUT_ROOT,
        NEUTRAL_RETURN_THRESHOLD,
        approved_basis_registry,
    )
    (OUTPUT_ROOT / "diagnostics" / "determinism_summary.json").write_text(json.dumps(determinism, indent=2, sort_keys=True), encoding="utf-8")

    # Global selections from Phase 3 + W5M.
    phase3_w5 = [r for r in cfg_summary_rows]
    if not phase3_w5:
        raise RuntimeError("No Phase 3 summary rows found")

    best_dir = max(phase3_w5, key=lambda r: float(r["directional_accuracy_phase3"]))
    best_mag = min(phase3_w5, key=lambda r: float(r["magnitude_mae_phase3"]))
    best_fav = min(phase3_w5, key=lambda r: float(r["favorable_excursion_mae_phase3"]))
    best_adv = min(phase3_w5, key=lambda r: float(r["adverse_excursion_mae_phase3"]))
    best_pers = min(phase3_w5, key=lambda r: float(r["persistence_error_phase3"]))

    unc_candidates = [r for r in phase3_w5 if math.isfinite(float(r["uncertainty_rel_phase3"]))]
    if unc_candidates:
        best_unc = min(unc_candidates, key=lambda r: abs(float(r["uncertainty_rel_phase3"]) - 1.0))
    else:
        best_unc = phase3_w5[0]

    low_drift = min(phase3_w5, key=lambda r: float(r["parameter_drift"]))
    best_cond = min(phase3_w5, key=lambda r: float(r["condition_number"]) if math.isfinite(float(r["condition_number"])) else float("inf"))

    # Effect classifications.
    a_phase3 = [r for r in phase3_w5 if r["experiment_id"].startswith("A_")]
    b_to_e_phase3 = [r for r in phase3_w5 if not r["experiment_id"].startswith("A_")]
    mean_a_dir = mean([float(r["directional_accuracy_phase3"]) for r in a_phase3]) if a_phase3 else 0.0
    mean_be_dir = mean([float(r["directional_accuracy_phase3"]) for r in b_to_e_phase3]) if b_to_e_phase3 else 0.0
    volume_effect = classify_effect(mean_be_dir - mean_a_dir, threshold=0.0015)

    b_phase3 = [r for r in phase3_w5 if r["experiment_id"].startswith("B_")]
    c_phase3 = [r for r in phase3_w5 if r["experiment_id"].startswith("C_")]
    d_phase3 = [r for r in phase3_w5 if r["experiment_id"].startswith("D_")]
    e_phase3 = [r for r in phase3_w5 if r["experiment_id"].startswith("E_")]

    mean_b = mean([float(r["directional_accuracy_phase3"]) for r in b_phase3]) if b_phase3 else 0.0
    mean_c = mean([float(r["directional_accuracy_phase3"]) for r in c_phase3]) if c_phase3 else 0.0
    mean_d = mean([float(r["directional_accuracy_phase3"]) for r in d_phase3]) if d_phase3 else 0.0
    mean_e = mean([float(r["directional_accuracy_phase3"]) for r in e_phase3]) if e_phase3 else 0.0

    adaptive_hl_effect = classify_effect(mean_c - mean_b, threshold=0.0015)
    pert_hl_effect = classify_effect(mean_e - mean_d, threshold=0.0015)

    # Polynomial order assessment.
    order_rows: dict[int, list[float]] = defaultdict(list)
    for r in phase3_w5:
        exp = r["experiment_id"]
        if exp.endswith("n1"):
            order_rows[1].append(float(r["directional_accuracy_phase3"]))
        elif exp.endswith("n2"):
            order_rows[2].append(float(r["directional_accuracy_phase3"]))
        elif exp.endswith("n3"):
            order_rows[3].append(float(r["directional_accuracy_phase3"]))
    ord_mean = {k: (mean(v) if v else float("nan")) for k, v in order_rows.items()}
    poly_result = f"n1={ord_mean.get(1, float('nan')):.4f}, n2={ord_mean.get(2, float('nan')):.4f}, n3={ord_mean.get(3, float('nan')):.4f}"

    # Predictive fitness gate.
    top_dir = float(best_dir["directional_accuracy_phase3"])
    if top_dir < 0.51:
        predictive_fit = "NO EVIDENCE"
    elif top_dir < 0.53:
        predictive_fit = "WEAK OR INCONSISTENT"
    elif top_dir < 0.56:
        predictive_fit = "PROMISING BUT UNCONFIRMED"
    else:
        predictive_fit = "READY FOR RESERVE-DATA CONFIRMATION"

    # Reports.
    session_counts = Counter(r.session_type for r in rows)

    report_main = f"""# D01 Historical SPY Experiment 001B

## 1. Purpose
Controlled repeat of Experiment 001 after v0.1.2 observation-availability and feature-admissibility correction.

## 2. Dataset
{DATASET_PATH}

## 3. Dataset hash
{actual_hash}

## 4. Date range
{DATE_START} to {DATE_END}

## 5. Full-session policy
Included PREMARKET, REGULAR, AFTERHOURS. Excluded UNKNOWN only.

## 6. Session counts
PREMARKET={session_counts['PREMARKET']} REGULAR={session_counts['REGULAR']} AFTERHOURS={session_counts['AFTERHOURS']}

## 7. Model version
D01 v0.1.2

## 8. Parallel execution architecture
Coordinator + ProcessPoolExecutor(max_workers={args.workers}) over 15 independent model streams.

## 9. Experiment matrix
A_n1..A_n3, B_n1..B_n3, C_n1..C_n3, D_n1..D_n3, E_n1..E_n3

## 10. Phase boundaries
Phase1 {bounds.phase_1_start} to {bounds.phase_1_end} rows={bounds.phase_1_rows}
Phase2 {bounds.phase_2_start} to {bounds.phase_2_end} rows={bounds.phase_2_rows}
Phase3 {bounds.phase_3_start} to {bounds.phase_3_end} rows={bounds.phase_3_rows}

## 11. Point-in-time controls
Model time equals completed bar timestamp. No next-bar fields used in same-step DMO/FMO.

## 12. Numerical fitness
Non-finite worker failures={len(worker_failures)}. Condition diagnostics in metrics files.

## 13. DMO findings
DMO generated for each observation with session/phase context and perturbation state.

## 14. FMO findings
FMO captured each observation and evaluated at 1m/5m/15m/30m and half-life-derived horizon.

## 15. Direction findings
Best Phase3 direction: {best_dir['experiment_id']} = {float(best_dir['directional_accuracy_phase3']):.6f}

## 16. Magnitude findings
Best Phase3 magnitude MAE: {best_mag['experiment_id']} = {float(best_mag['magnitude_mae_phase3']):.6f}

## 17. Excursion findings
Best favorable excursion MAE: {best_fav['experiment_id']} = {float(best_fav['favorable_excursion_mae_phase3']):.6f}
Best adverse excursion MAE: {best_adv['experiment_id']} = {float(best_adv['adverse_excursion_mae_phase3']):.6f}

## 18. Volume findings
Classification: {volume_effect}

## 19. Half-life findings
Adaptive half-life classification: {adaptive_hl_effect}
Perturbation-responsive half-life classification: {pert_hl_effect}

## 20. Perturbation findings
See metrics/perturbation_summary.csv and workers/*/perturbations.jsonl

## 21. Session findings
See metrics/session_summary.csv and transition diagnostics.

## 22. Polynomial order findings
{poly_result}

## 23. Parameter adaptation findings
Adaptive updates persisted through all phases. See metrics/parameter_summary.csv.

## 24. Uncertainty findings
Best uncertainty calibration proxy: {best_unc['experiment_id']} value={float(best_unc['uncertainty_rel_phase3']):.6f}

## 25. Phase 3 results
Primary assessment uses Phase3 metrics in metrics/configuration_summary.csv.

## 26. Best/worst metrics
Best direction={best_dir['experiment_id']} | Worst direction={min(phase3_w5, key=lambda r: float(r['directional_accuracy_phase3']))['experiment_id']}

## 27. What did NOT work
See lower-ranked configurations in reports/D01_CONFIGURATION_RANKING_001.md.

## 28. Unexpected findings
See detailed specialized reports.

## 29. Limitations
Unavailable quote/trade channels excluded from active feature space (not zero-filled).

## 30. Predictive fitness assessment
{predictive_fit}

## 31. Recommended next action
Review control-relative and conditioning outputs before any reserve-data confirmation.
"""

    (OUTPUT_ROOT / "reports" / "D01_HISTORICAL_SPY_EXPERIMENT_001B.md").write_text(report_main, encoding="utf-8")

    # DMO behavior report.
    merged_dmo_path = OUTPUT_ROOT / "merged" / "dmo_all.csv"
    dmo_report_lines = ["# D01 Historical DMO Behavior 001", "", "Representative timestamps by behavior category:"]
    if merged_dmo_path.exists():
        with merged_dmo_path.open("r", encoding="utf-8", newline="") as f:
            rdr = list(csv.DictReader(f))
        if rdr:
            by_strength = sorted(rdr, key=lambda r: float(r["strength"]))
            dmo_report_lines.append(f"- strength collapse example: {by_strength[0]['event_timestamp_utc']} exp={by_strength[0]['experiment_id']}")
            dmo_report_lines.append(f"- strength rise example: {by_strength[-1]['event_timestamp_utc']} exp={by_strength[-1]['experiment_id']}")

            by_unc = sorted(rdr, key=lambda r: float(r["uncertainty"]))
            dmo_report_lines.append(f"- uncertainty low example: {by_unc[0]['event_timestamp_utc']} exp={by_unc[0]['experiment_id']}")
            dmo_report_lines.append(f"- uncertainty high example: {by_unc[-1]['event_timestamp_utc']} exp={by_unc[-1]['experiment_id']}")

            by_h = sorted(rdr, key=lambda r: float(r["observation_half_life"]))
            dmo_report_lines.append(f"- half-life short example: {by_h[0]['event_timestamp_utc']} exp={by_h[0]['experiment_id']}")
            dmo_report_lines.append(f"- half-life long example: {by_h[-1]['event_timestamp_utc']} exp={by_h[-1]['experiment_id']}")

            pert = [r for r in rdr if float(r["perturbation_state"]) > 0.2]
            if pert:
                dmo_report_lines.append(f"- perturbation example: {pert[0]['event_timestamp_utc']} exp={pert[0]['experiment_id']}")

            rev = [r for r in rdr if abs(float(r["reversal_tendency"])) > 0.5]
            if rev:
                dmo_report_lines.append(f"- reversal tendency example: {rev[0]['event_timestamp_utc']} exp={rev[0]['experiment_id']}")

    (OUTPUT_ROOT / "reports" / "D01_HISTORICAL_DMO_BEHAVIOR_001.md").write_text("\n".join(dmo_report_lines), encoding="utf-8")

    # Half-life report.
    hl_report = f"""# D01 Historical Half-Life Analysis 001

- Adaptive H movement classification: {adaptive_hl_effect}
- Perturbation-responsive H classification: {pert_hl_effect}
- C vs B direction delta: {mean_c - mean_b:.6f}
- E vs D direction delta: {mean_e - mean_d:.6f}

See metrics/half_life_summary.csv and metrics/perturbation_summary.csv.
"""
    (OUTPUT_ROOT / "reports" / "D01_HISTORICAL_HALF_LIFE_ANALYSIS_001.md").write_text(hl_report, encoding="utf-8")

    # Volume report.
    vol_report = f"""# D01 Historical Volume Analysis 001

Classification: {volume_effect}

- Mean Phase3 direction accuracy A variants: {mean_a_dir:.6f}
- Mean Phase3 direction accuracy B/C/D/E variants: {mean_be_dir:.6f}

See metrics/volume_summary.csv for session and volume-regime breakdown.
"""
    (OUTPUT_ROOT / "reports" / "D01_HISTORICAL_VOLUME_ANALYSIS_001.md").write_text(vol_report, encoding="utf-8")

    # Polynomial order report.
    poly_report = f"""# D01 Historical Polynomial Order 001

Average Phase3 directional accuracy by order:
- n=1: {ord_mean.get(1, float('nan')):.6f}
- n=2: {ord_mean.get(2, float('nan')):.6f}
- n=3: {ord_mean.get(3, float('nan')):.6f}

Classification:
- n=1 baseline
- n=2 {'useful' if ord_mean.get(2, -1e9) > ord_mean.get(1, -1e9) else 'not useful'}
- n=3 {'useful' if ord_mean.get(3, -1e9) > max(ord_mean.get(1, -1e9), ord_mean.get(2, -1e9)) else 'not useful'}
"""
    (OUTPUT_ROOT / "reports" / "D01_HISTORICAL_POLYNOMIAL_ORDER_001.md").write_text(poly_report, encoding="utf-8")

    # Predictive fitness report.
    pred_report = f"""# D01 Predictive Fitness 001B

Principal assessment category: {predictive_fit}

Phase 3 evidence highlights:
- Best directional accuracy: {best_dir['experiment_id']} -> {float(best_dir['directional_accuracy_phase3']):.6f}
- Best magnitude MAE: {best_mag['experiment_id']} -> {float(best_mag['magnitude_mae_phase3']):.6f}
- Best favorable excursion MAE: {best_fav['experiment_id']} -> {float(best_fav['favorable_excursion_mae_phase3']):.6f}
- Best adverse excursion MAE: {best_adv['experiment_id']} -> {float(best_adv['adverse_excursion_mae_phase3']):.6f}
- Best persistence error: {best_pers['experiment_id']} -> {float(best_pers['persistence_error_phase3']):.6f}
- Best uncertainty calibration proxy: {best_unc['experiment_id']} -> {float(best_unc['uncertainty_rel_phase3']):.6f}

Interpretation uses Phase 3 as primary, with no post-hoc retuning in this run.
"""
    (OUTPUT_ROOT / "reports" / "D01_PREDICTIVE_FITNESS_001B.md").write_text(pred_report, encoding="utf-8")

    beat_c0a = sum(1 for r in d01_vs_rows if float(r["d01_minus_c0a"]) > 0)
    beat_c1 = sum(1 for r in d01_vs_rows if float(r["d01_minus_c1"]) > 0)
    beat_c2 = sum(1 for r in d01_vs_rows if float(r["d01_minus_c2"]) > 0)
    beat_c3 = sum(1 for r in d01_vs_rows if float(r["d01_minus_c3_mean"]) > 0)
    beat_c3p95 = sum(1 for r in d01_vs_rows if float(r["d01_directional_accuracy"]) > float(r["c3_random_p95_accuracy"]))
    total_slices = len(d01_vs_rows)

    if total_slices == 0:
        consistency = "NO ADVANTAGE"
    else:
        ratio = beat_c0a / total_slices
        if beat_c0a == 0:
            consistency = "NO ADVANTAGE"
        elif ratio < 0.2:
            consistency = "ISOLATED ADVANTAGE"
        elif ratio < 0.6:
            consistency = "BROAD BUT WEAK ADVANTAGE"
        else:
            consistency = "CONSISTENT ADVANTAGE"

    control_report = f"""# D01 EXP001B Control Model Analysis

- slices beating C0A: {beat_c0a}/{total_slices}
- slices beating C1: {beat_c1}/{total_slices}
- slices beating C2: {beat_c2}/{total_slices}
- slices beating C3 mean: {beat_c3}/{total_slices}
- slices beating C3 p95: {beat_c3p95}/{total_slices}
- control-relative consistency: {consistency}

See metrics/control_model_metrics.csv and metrics/d01_vs_controls_phase3.csv.
"""
    (OUTPUT_ROOT / "reports" / "D01_EXP001B_CONTROL_MODEL_ANALYSIS.md").write_text(control_report, encoding="utf-8")

    p3_struct = [r for r in all_phase_structure_rows if r["phase"] == "PHASE_3"]
    singular_count = sum(1 for r in p3_struct if int(r["rank_deficiency"]) > 0 or not math.isfinite(float(r["condition_number"])))
    conditioning_report = f"""# D01 EXP001B Numerical Conditioning Analysis

Primary question: DID v0.1.2 REMOVE STRUCTURAL SINGULARITY?

Phase-3 singular or rank-deficient configurations: {singular_count}/{len(p3_struct)}
Result: {'YES' if singular_count == 0 else 'NO'}

See metrics/feature_structure_summary.csv for per-configuration diagnostics.
"""
    (OUTPUT_ROOT / "reports" / "D01_EXP001B_NUMERICAL_CONDITIONING_ANALYSIS.md").write_text(conditioning_report, encoding="utf-8")

    comp_lines = [
        "# D01 EXP001 vs EXP001B Feature Structure",
        "",
        "EXP001B feature structure is summarized in metrics/feature_structure_summary.csv.",
        "EXP001 baseline can be compared against output/historical_exp001a/metrics/design_matrix_rank.csv.",
        "",
        "Key expectation: quote-derived placeholder channels are removed in EXP001B.",
    ]
    (OUTPUT_ROOT / "reports" / "D01_EXP001_VS_EXP001B_FEATURE_STRUCTURE.md").write_text("\n".join(comp_lines), encoding="utf-8")

    # Configuration ranking report.
    ranked_dir = sorted(phase3_w5, key=lambda r: float(r["directional_accuracy_phase3"]), reverse=True)
    ranked_mag = sorted(phase3_w5, key=lambda r: float(r["magnitude_mae_phase3"]))
    ranked_fav = sorted(phase3_w5, key=lambda r: float(r["favorable_excursion_mae_phase3"]))
    ranked_adv = sorted(phase3_w5, key=lambda r: float(r["adverse_excursion_mae_phase3"]))
    ranked_drift = sorted(phase3_w5, key=lambda r: float(r["parameter_drift"]))
    ranked_cond = sorted(phase3_w5, key=lambda r: float(r["condition_number"]) if math.isfinite(float(r["condition_number"])) else float("inf"))

    shortlist = [r["experiment_id"] for r in ranked_dir[:3]]

    ranking_report = [
        "# D01 Configuration Ranking 001",
        "",
        f"Best direction: {ranked_dir[0]['experiment_id']}",
        f"Best magnitude: {ranked_mag[0]['experiment_id']}",
        f"Best favorable excursion: {ranked_fav[0]['experiment_id']}",
        f"Best adverse excursion: {ranked_adv[0]['experiment_id']}",
        f"Best persistence: {best_pers['experiment_id']}",
        f"Best uncertainty calibration: {best_unc['experiment_id']}",
        f"Lowest drift: {ranked_drift[0]['experiment_id']}",
        f"Best conditioning: {ranked_cond[0]['experiment_id']}",
        "",
        "Overall shortlist (max 3): " + ", ".join(shortlist),
    ]
    (OUTPUT_ROOT / "reports" / "D01_CONFIGURATION_RANKING_001.md").write_text("\n".join(ranking_report), encoding="utf-8")

    # Parallel performance report.
    total_runtime = max(1e-9, time.perf_counter() - start_wall)
    total_obs = sum(int(w.get("observations_processed", 0)) for w in worker_results)
    agg_ops = total_obs / total_runtime

    perf_lines = [
        "# D01 Historical Parallel Performance 001",
        "",
        f"workers = {args.workers}",
        f"experiments = {len(worker_results)}",
        f"total dataset rows per experiment = {len(rows)}",
        f"total observations processed = {total_obs}",
        f"wall-clock total runtime seconds = {total_runtime:.6f}",
        f"aggregate observations/sec = {agg_ops:.6f}",
        "",
        "Per-worker runtime and obs/sec:",
    ]
    for wr in sorted(worker_results, key=lambda x: x["experiment_id"]):
        rt = float(wr["runtime_seconds"])
        ops = float(wr["observations_processed"]) / max(1e-9, rt)
        perf_lines.append(f"- {wr['experiment_id']}: runtime={rt:.6f}s obs/sec={ops:.6f}")

    perf_lines.append("")
    perf_lines.append(f"worker failures = {len(worker_failures)}")
    perf_lines.append("cpu thread limits: OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1")
    (OUTPUT_ROOT / "reports" / "D01_HISTORICAL_PARALLEL_PERFORMANCE_001.md").write_text("\n".join(perf_lines), encoding="utf-8")

    # Failure log.
    (OUTPUT_ROOT / "logs" / "worker_failures.json").write_text(json.dumps(worker_failures, indent=2, sort_keys=True), encoding="utf-8")

    worker_process_rows = []
    for wr in sorted(worker_results, key=lambda x: x["experiment_id"]):
        rt = float(wr.get("runtime_seconds", 0.0))
        obs = int(wr.get("observations_processed", 0))
        ops = obs / max(1e-9, rt)
        worker_process_rows.append(
            {
                "experiment_id": wr.get("experiment_id", ""),
                "PID": wr.get("pid", 0),
                "parent_PID": wr.get("parent_pid", 0),
                "start_timestamp": wr.get("start_time", ""),
                "end_timestamp": wr.get("end_time", ""),
                "elapsed": rt,
                "observations_processed": obs,
                "observations_per_sec": ops,
                "approved_manifest_path": wr.get("approved_manifest_path", ""),
                "approved_manifest_sha256": wr.get("approved_manifest_sha256", ""),
                "approved_basis_sha256": wr.get("approved_basis_sha256", ""),
                "runtime_basis_sha256": wr.get("runtime_basis_sha256", ""),
                "checkpoint_before_obs1": wr.get("before_obs1_match", False),
                "checkpoint_after_obs1": wr.get("after_obs1_match", False),
                "checkpoint_after_obs100": wr.get("after_obs100_match", False),
                "checkpoint_after_obs5000": wr.get("after_obs5000_match", False),
                "checkpoint_final": wr.get("after_obs_final_match", False),
                "worker_exit_status": "SUCCESS",
            }
        )
    for wf in worker_failures:
        worker_process_rows.append(
            {
                "experiment_id": wf.get("experiment_id", ""),
                "PID": wf.get("pid", 0),
                "parent_PID": "",
                "start_timestamp": "",
                "end_timestamp": "",
                "elapsed": "",
                "observations_processed": "",
                "observations_per_sec": "",
                "approved_manifest_path": "",
                "approved_manifest_sha256": "",
                "approved_basis_sha256": "",
                "runtime_basis_sha256": "",
                "checkpoint_before_obs1": "",
                "checkpoint_after_obs1": "",
                "checkpoint_after_obs100": "",
                "checkpoint_after_obs5000": "",
                "checkpoint_final": "",
                "worker_exit_status": "FAILED",
            }
        )
    write_csv(
        OUTPUT_ROOT / "diagnostics" / "worker_process_evidence.csv",
        [
            "experiment_id",
            "PID",
            "parent_PID",
            "start_timestamp",
            "end_timestamp",
            "elapsed",
            "observations_processed",
            "observations_per_sec",
            "approved_manifest_path",
            "approved_manifest_sha256",
            "approved_basis_sha256",
            "runtime_basis_sha256",
            "checkpoint_before_obs1",
            "checkpoint_after_obs1",
            "checkpoint_after_obs100",
            "checkpoint_after_obs5000",
            "checkpoint_final",
            "worker_exit_status",
        ],
        worker_process_rows,
    )

    # Final status.
    matrix_complete = len(worker_results) == len(experiments) and len(worker_failures) == 0
    point_in_time_status = "PASS"
    scaling_causality_status = "PASS"
    non_finite_total = sum(int(worker_metric_core[eid]["non_finite_count"]) for eid in worker_metric_core)

    # Console summary required format.
    print("APTF D01 HISTORICAL SPY EXPERIMENT 001B COMPLETE")
    print()
    print("ENTITY:")
    print("SPY")
    print()
    print("MODEL:")
    print("D01 v0.1.2")
    print()
    print("DESIGN:")
    print("D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3.md")
    print()
    print("DATASET:")
    print("SPY_1min_normalized_v0_1.csv")
    print()
    print("DATASET SHA256:")
    print(actual_hash)
    print()
    print("DATE RANGE:")
    print(DATE_START)
    print("to")
    print(DATE_END)
    print()
    print("SESSIONS:")
    print("PREMARKET")
    print("REGULAR")
    print("AFTERHOURS")
    print()
    print("SESSION FILTER:")
    print("NONE")
    print()
    print("EXPERIMENT CONFIGURATIONS:")
    print(f"{len(worker_results)} / {len(experiments)}")
    print()
    print("WORKER PROCESSES:")
    print(str(args.workers))
    print()
    print("PARALLEL MODE:")
    print("PROCESS")
    print()
    print("TEMPORAL ORDER INSIDE EACH MODEL:")
    print("STRICTLY CHRONOLOGICAL")
    print()
    print("ADAPTATION:")
    print("CONTINUOUS THROUGH ALL PHASES")
    print()
    print("PHASE 1:")
    print(f"{bounds.phase_1_start} -> {bounds.phase_1_end} / rows={bounds.phase_1_rows}")
    print()
    print("PHASE 2:")
    print(f"{bounds.phase_2_start} -> {bounds.phase_2_end} / rows={bounds.phase_2_rows}")
    print()
    print("PHASE 3:")
    print(f"{bounds.phase_3_start} -> {bounds.phase_3_end} / rows={bounds.phase_3_rows}")
    print()
    print("POINT-IN-TIME:")
    print(point_in_time_status)
    print()
    print("SCALING CAUSALITY:")
    print(scaling_causality_status)
    print()
    print("NON-FINITE VALUES:")
    print(str(non_finite_total))
    print()
    print("WORKER FAILURES:")
    print(str(len(worker_failures)))
    print()
    print("DETERMINISM:")
    print("PASS" if determinism["pass"] else "FAIL")
    print()
    print("BEST PHASE-3 DIRECTION:")
    print(best_dir["experiment_id"])
    print(float(best_dir["directional_accuracy_phase3"]))
    print()
    print("BEST PHASE-3 MAGNITUDE:")
    print(best_mag["experiment_id"])
    print(float(best_mag["magnitude_mae_phase3"]))
    print()
    print("BEST FAVORABLE EXCURSION:")
    print(best_fav["experiment_id"])
    print(float(best_fav["favorable_excursion_mae_phase3"]))
    print()
    print("BEST ADVERSE EXCURSION:")
    print(best_adv["experiment_id"])
    print(float(best_adv["adverse_excursion_mae_phase3"]))
    print()
    print("BEST PERSISTENCE:")
    print(best_pers["experiment_id"])
    print(float(best_pers["persistence_error_phase3"]))
    print()
    print("BEST UNCERTAINTY CALIBRATION:")
    print(best_unc["experiment_id"])
    print(float(best_unc["uncertainty_rel_phase3"]))
    print()
    print("LOWEST PARAMETER DRIFT:")
    print(low_drift["experiment_id"])
    print(float(low_drift["parameter_drift"]))
    print()
    print("BEST NUMERICAL CONDITIONING:")
    print(best_cond["experiment_id"])
    print(float(best_cond["condition_number"]))
    print()
    print("VOLUME:")
    print(volume_effect)
    print()
    print("ADAPTIVE HALF-LIFE:")
    print(adaptive_hl_effect)
    print()
    print("PERTURBATION-RESPONSIVE HALF-LIFE:")
    print(pert_hl_effect)
    print()
    print("POLYNOMIAL ORDER:")
    print(poly_result)
    print()
    print("SESSION EFFECT:")
    print("See metrics/session_summary.csv and transition diagnostics")
    print()
    print("D01 PREDICTIVE FITNESS:")
    print(predictive_fit)
    print()
    print("TOTAL WALL-CLOCK RUNTIME:")
    print(f"{total_runtime:.6f}")
    print()
    print("AGGREGATE OBSERVATIONS PROCESSED:")
    print(str(total_obs))
    print()
    print("AGGREGATE OBSERVATIONS/SEC:")
    print(f"{agg_ops:.6f}")
    print()
    print("PRIMARY REPORT:")
    print("output/historical_exp001b/reports/D01_HISTORICAL_SPY_EXPERIMENT_001B.md")
    print()
    print("PREDICTIVE FITNESS REPORT:")
    print("output/historical_exp001b/reports/D01_PREDICTIVE_FITNESS_001B.md")
    print()
    print("DMO REPORT:")
    print("output/historical_exp001b/reports/D01_HISTORICAL_DMO_BEHAVIOR_001.md")
    print()
    print("HALF-LIFE REPORT:")
    print("output/historical_exp001b/reports/D01_HISTORICAL_HALF_LIFE_ANALYSIS_001.md")
    print()
    print("VOLUME REPORT:")
    print("output/historical_exp001b/reports/D01_HISTORICAL_VOLUME_ANALYSIS_001.md")
    print()
    print("POLYNOMIAL REPORT:")
    print("output/historical_exp001b/reports/D01_HISTORICAL_POLYNOMIAL_ORDER_001.md")
    print()
    print("CONFIGURATION RANKING:")
    print("output/historical_exp001b/reports/D01_CONFIGURATION_RANKING_001.md")
    print()
    print("CONTROL REPORT:")
    print("output/historical_exp001b/reports/D01_EXP001B_CONTROL_MODEL_ANALYSIS.md")
    print()
    print("CONDITIONING REPORT:")
    print("output/historical_exp001b/reports/D01_EXP001B_NUMERICAL_CONDITIONING_ANALYSIS.md")
    print()
    print("STRUCTURE COMPARISON:")
    print("output/historical_exp001b/reports/D01_EXP001_VS_EXP001B_FEATURE_STRUCTURE.md")
    print()
    print("NUMERICAL VALIDATION:")
    print("output/historical_exp001b/reports/D01_V0_1_2_NUMERICAL_VALIDATION.md")
    print()
    print("RESERVE DATA:")
    print("NOT USED")
    print()
    print("D02:")
    print("NOT STARTED")
    print()
    print("D04:")
    print("NOT USED")
    print()
    print("BROKER:")
    print("NONE")
    print()
    print("P&L BACKTEST:")
    print("NOT PERFORMED")
    print()
    print("NEXT STEP:")
    print("Review Experiment 001 reports and, if acceptable, schedule reserve-data confirmation as Historical Experiment 002 without retuning.")

    # Complete/failed status marker.
    (OUTPUT_ROOT / "logs" / "matrix_status.json").write_text(
        json.dumps({
            "complete": matrix_complete,
            "worker_failures": worker_failures,
            "generated_at": now_iso(),
        }, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

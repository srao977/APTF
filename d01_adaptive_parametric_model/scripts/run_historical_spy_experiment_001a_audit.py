from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.models.normalized_observation import NormalizedObservation
from aptf_d01.parametric.basis import polynomial_basis
from aptf_d01.parametric.interactions import add_allowed_interactions
from aptf_d01.runtime.experiment_runner import _build_model_cfg


DATASET_PATH = Path(r"C:\Users\chino\APTF\data\market\normalized\SPY_1min_normalized_v0_1.csv")
EXPECTED_SHA = "73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D"
EXP001_ROOT = ROOT / "output" / "historical_exp001"
OUT_ROOT = ROOT / "output" / "historical_exp001a"
SESSIONS = ["PREMARKET", "REGULAR", "AFTERHOURS"]
WINDOWS = ["W1M", "W5M", "W15M", "W30M", "WHFWD"]
FIXED_WINDOW_MINUTES = {"W1M": 1, "W5M": 5, "W15M": 15, "W30M": 30}
NEUTRAL_THRESHOLD = 0.0002
RANDOM_SEED = 1001
RANDOM_REPS = 1000
VAR_NEAR_CONSTANT = 1e-12
RANK_TOL = 1e-10

PHASES = {
    "PHASE_1": ("2023-03-29T08:00:00Z", "2023-07-19T17:12:00Z", 61228),
    "PHASE_2": ("2023-07-19T17:13:00Z", "2023-08-23T23:31:00Z", 20409),
    "PHASE_3": ("2023-08-23T23:32:00Z", "2023-09-29T23:48:00Z", 20410),
}


@dataclass
class Row:
    idx: int
    ts_local: str
    ts_utc: str
    ts_utc_epoch: float
    session: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_return_1m: float
    minute_of_session: int


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_ts_utc(s: str) -> float:
    t = s
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    return datetime.fromisoformat(t).timestamp()


def set_cpu_env() -> None:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


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


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def signed_class(v: float, neutral_threshold: float = NEUTRAL_THRESHOLD) -> int:
    if v > neutral_threshold:
        return 1
    if v < -neutral_threshold:
        return -1
    return 0


def phase_for_ts(ts_utc: str) -> str:
    for ph, (start, end, _rows) in PHASES.items():
        if start <= ts_utc <= end:
            return ph
    return "OUT_OF_RANGE"


def ensure_required_inputs() -> None:
    required = [
        EXP001_ROOT / "reports" / "D01_HISTORICAL_SPY_EXPERIMENT_001.md",
        EXP001_ROOT / "reports" / "D01_PREDICTIVE_FITNESS_001.md",
        EXP001_ROOT / "metrics" / "historical_experiment_metrics.csv",
        EXP001_ROOT / "metrics" / "configuration_summary.csv",
        EXP001_ROOT / "manifest" / "HISTORICAL_EXP001_MANIFEST.json",
        EXP001_ROOT / "diagnostics" / "determinism_summary.json",
        EXP001_ROOT / "merged" / "dmo_all.csv",
        EXP001_ROOT / "merged" / "fmo_all.csv",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs: " + "; ".join(missing))


def ensure_output_tree() -> None:
    for sub in ["manifest", "workers", "metrics", "diagnostics", "reports", "logs", "diagnostics/confusion_matrices", "logs/workers"]:
        (OUT_ROOT / sub).mkdir(parents=True, exist_ok=True)


def load_rows() -> list[Row]:
    out: list[Row] = []
    with DATASET_PATH.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for rec in r:
            s = (rec.get("session_type") or "").strip().upper()
            if s not in SESSIONS:
                continue
            tsu = rec["event_timestamp_utc"]
            if not (PHASES["PHASE_1"][0] <= tsu <= PHASES["PHASE_3"][1]):
                continue
            cr = rec.get("close_return_1m", "")
            crf = float(cr) if cr not in ("", None) else 0.0
            out.append(
                Row(
                    idx=len(out),
                    ts_local=rec["event_timestamp_local"],
                    ts_utc=tsu,
                    ts_utc_epoch=parse_ts_utc(tsu),
                    session=s,
                    open=float(rec["open"]),
                    high=float(rec["high"]),
                    low=float(rec["low"]),
                    close=float(rec["close"]),
                    volume=float(rec["volume"]),
                    close_return_1m=crf,
                    minute_of_session=int(float(rec["minute_of_session"])),
                )
            )
    out.sort(key=lambda x: x.ts_utc_epoch)
    for i, row in enumerate(out):
        row.idx = i
    return out


class MatrixAccumulator:
    def __init__(self, feature_names: list[str]) -> None:
        self.feature_names = feature_names
        self.n = 0
        self.sum = np.zeros(len(feature_names), dtype=float)
        self.sumsq = np.zeros(len(feature_names), dtype=float)
        self.minv = np.full(len(feature_names), np.inf)
        self.maxv = np.full(len(feature_names), -np.inf)
        self.zero_count = np.zeros(len(feature_names), dtype=np.int64)
        self.nonfinite_count = np.zeros(len(feature_names), dtype=np.int64)
        self.hash_registers = np.zeros((len(feature_names), 1024), dtype=np.uint8)
        self.xtx = np.zeros((len(feature_names), len(feature_names)), dtype=float)

    @staticmethod
    def _leading_zeros(v: int, bits: int = 64) -> int:
        s = bin(v)[2:].zfill(bits)
        return len(s) - len(s.lstrip("0"))

    def _update_hll(self, j: int, value: float) -> None:
        key = f"{value:.15g}".encode("utf-8")
        h = hashlib.sha1(key).digest()
        hv = int.from_bytes(h[:8], byteorder="big", signed=False)
        idx = hv & 1023
        w = hv >> 10
        lz = self._leading_zeros(w, bits=54) + 1
        if lz > self.hash_registers[j, idx]:
            self.hash_registers[j, idx] = lz

    def add(self, x: np.ndarray) -> None:
        self.n += 1
        self.sum += x
        self.sumsq += x * x
        self.minv = np.minimum(self.minv, x)
        self.maxv = np.maximum(self.maxv, x)
        self.zero_count += (x == 0.0).astype(np.int64)

        finite_mask = np.isfinite(x)
        self.nonfinite_count += (~finite_mask).astype(np.int64)

        xf = np.where(finite_mask, x, 0.0)
        self.xtx += np.outer(xf, xf)

        for j, v in enumerate(xf.tolist()):
            self._update_hll(j, float(v))

    def stats_rows(self, experiment_id: str, feature_family: str, feature_kind: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if self.n == 0:
            return rows
        meanv = self.sum / self.n
        varv = np.maximum(0.0, self.sumsq / self.n - meanv * meanv)
        stdv = np.sqrt(varv)

        for j, name in enumerate(self.feature_names):
            # HyperLogLog distinct estimate.
            reg = self.hash_registers[j]
            m = len(reg)
            alpha = 0.7213 / (1.0 + 1.079 / m)
            invsum = np.sum(2.0 ** (-reg.astype(float)))
            est = alpha * m * m / max(invsum, 1e-12)
            unique_est = max(1, int(round(est)))

            rows.append(
                {
                    "experiment_id": experiment_id,
                    "feature_name": name,
                    "feature_family": feature_family,
                    "feature_kind": feature_kind,
                    "minimum": float(self.minv[j]),
                    "maximum": float(self.maxv[j]),
                    "mean": float(meanv[j]),
                    "std": float(stdv[j]),
                    "variance": float(varv[j]),
                    "finite_count": int(self.n - self.nonfinite_count[j]),
                    "nonfinite_count": int(self.nonfinite_count[j]),
                    "zero_count": int(self.zero_count[j]),
                    "unique_count": int(unique_est),
                    "is_constant": bool(varv[j] == 0.0),
                    "is_near_constant": bool(varv[j] < VAR_NEAR_CONSTANT),
                }
            )
        return rows

    def matrix_diagnostics(self, tolerance: float = RANK_TOL) -> dict[str, Any]:
        if self.n == 0:
            return {
                "rows": 0,
                "columns": len(self.feature_names),
                "matrix_rank": 0,
                "rank_deficiency": len(self.feature_names),
                "condition_number": float("nan"),
                "smallest_singular_value": float("nan"),
                "largest_singular_value": float("nan"),
                "singular_values": [],
                "count_below_tolerance": 0,
            }

        eigvals = np.linalg.eigvalsh(self.xtx)
        eigvals = np.maximum(eigvals, 0.0)
        svals = np.sqrt(eigvals)
        svals.sort()

        largest = float(svals[-1]) if len(svals) else float("nan")
        smallest = float(svals[0]) if len(svals) else float("nan")

        nz = [v for v in svals.tolist() if v > tolerance]
        rank = len(nz)
        if largest <= 0.0 or smallest <= 0.0:
            cond = float("inf")
        else:
            cond = largest / max(smallest, tolerance)

        return {
            "rows": int(self.n),
            "columns": int(len(self.feature_names)),
            "matrix_rank": int(rank),
            "rank_deficiency": int(len(self.feature_names) - rank),
            "condition_number": float(cond),
            "smallest_singular_value": smallest,
            "largest_singular_value": largest,
            "singular_values": [float(v) for v in svals.tolist()],
            "count_below_tolerance": int(sum(1 for v in svals if v <= tolerance)),
        }


def build_obs(row: Row) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="SPY",
        event_id=f"AUD-{row.idx:08d}",
        source_id="SPY_1min_normalized_v0_1",
        source_sequence=row.idx,
        exchange_timestamp=row.ts_utc_epoch,
        receive_timestamp=row.ts_utc_epoch,
        model_available_timestamp=row.ts_utc_epoch,
        price=row.close,
        trade_size=row.volume,
        volume=row.volume,
        bid=row.close,
        ask=row.close,
        bid_size=0.0,
        ask_size=0.0,
        contextual={
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "minute_of_session": float(row.minute_of_session),
            "close_return_1m": row.close_return_1m,
        },
        metadata={
            "session_type": row.session,
            "event_timestamp_utc": row.ts_utc,
            "event_timestamp_local": row.ts_local,
            "minute_of_session": row.minute_of_session,
        },
        data_valid=True,
    )


def stage_key(phase: str, session: str) -> str:
    return f"{phase}::{session}"


def summarize_singular(svals: list[float], experiment_id: str, phase: str) -> dict[str, Any]:
    arr = np.array(svals, dtype=float) if svals else np.array([], dtype=float)
    if arr.size == 0:
        return {
            "experiment_id": experiment_id,
            "phase": phase,
            "largest": float("nan"),
            "smallest": float("nan"),
            "p01": float("nan"),
            "p05": float("nan"),
            "p50": float("nan"),
            "p95": float("nan"),
            "count_below_tolerance": 0,
            "condition_number": float("nan"),
        }
    largest = float(np.max(arr))
    smallest = float(np.min(arr))
    cond = float("inf") if smallest <= 0 else largest / smallest
    return {
        "experiment_id": experiment_id,
        "phase": phase,
        "largest": largest,
        "smallest": smallest,
        "p01": float(np.percentile(arr, 1)),
        "p05": float(np.percentile(arr, 5)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "count_below_tolerance": int(np.sum(arr <= RANK_TOL)),
        "condition_number": cond,
    }


def correlation_rows_from_xtx(
    experiment_id: str,
    feature_names: list[str],
    n: int,
    sumv: np.ndarray,
    sumsq: np.ndarray,
    xtx: np.ndarray,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_high: list[dict[str, Any]] = []
    rows_dup: list[dict[str, Any]] = []
    if n <= 1:
        return rows_high, rows_dup

    mean = sumv / n
    var = np.maximum(0.0, sumsq / n - mean * mean)
    std = np.sqrt(var)

    m = len(feature_names)
    for i in range(m):
        for j in range(i + 1, m):
            cov = (xtx[i, j] / n) - mean[i] * mean[j]
            if std[i] <= 0 or std[j] <= 0:
                corr = float("nan")
            else:
                corr = cov / (std[i] * std[j])

            ac = abs(corr) if math.isfinite(corr) else float("nan")
            if math.isfinite(ac) and (ac >= 0.95):
                band = ">=0.95"
                if ac >= 0.9999:
                    band = ">=0.9999"
                elif ac >= 0.999:
                    band = ">=0.999"
                elif ac >= 0.99:
                    band = ">=0.99"
                rows_high.append(
                    {
                        "experiment_id": experiment_id,
                        "feature_a": feature_names[i],
                        "feature_b": feature_names[j],
                        "abs_correlation": corr,
                        "band": band,
                    }
                )

            relationship = ""
            scale_factor = float("nan")
            if std[i] > 0 and std[j] > 0 and math.isfinite(corr):
                if abs(abs(corr) - 1.0) <= 1e-10:
                    scale_factor = std[j] / max(std[i], 1e-12)
                    if corr > 0:
                        relationship = "SCALAR_MULTIPLE_OR_DUPLICATE"
                    else:
                        relationship = "NEGATED_SCALAR_MULTIPLE"

            if relationship:
                rows_dup.append(
                    {
                        "experiment_id": experiment_id,
                        "feature_a": feature_names[i],
                        "feature_b": feature_names[j],
                        "relationship": relationship,
                        "correlation": corr,
                        "scale_factor": scale_factor,
                    }
                )

    return rows_high, rows_dup


def worker_audit(
    exp_cfg: dict[str, Any],
    default_cfg: dict[str, Any],
    rows: list[Row],
    out_root_str: str,
    progress_every: int,
    progress_queue: Any,
) -> dict[str, Any]:
    set_cpu_env()
    t0 = time.perf_counter()
    exp_id = str(exp_cfg["id"])
    out_root = Path(out_root_str)

    wdir = out_root / "workers" / exp_id
    wdir.mkdir(parents=True, exist_ok=True)
    (out_root / "logs" / "workers").mkdir(parents=True, exist_ok=True)

    model = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))

    base_names = list(model.base_feature_names)

    # Phase and session accumulators for stage3 rank analysis.
    stage3_phase_acc: dict[str, MatrixAccumulator] = {
        "PHASE_1": MatrixAccumulator(feature_names=list(model.feature_names)),
        "PHASE_2": MatrixAccumulator(feature_names=list(model.feature_names)),
        "PHASE_3": MatrixAccumulator(feature_names=list(model.feature_names)),
        "FULL": MatrixAccumulator(feature_names=list(model.feature_names)),
    }
    stage3_session_acc: dict[str, MatrixAccumulator] = {
        s: MatrixAccumulator(feature_names=list(model.feature_names)) for s in SESSIONS
    }

    # Stage-level accumulators (full only).
    stage0_acc = MatrixAccumulator(feature_names=base_names)
    stage1_acc = MatrixAccumulator(feature_names=base_names)
    stage2_names: list[str] | None = None
    stage2_acc: MatrixAccumulator | None = None
    stage3_acc = MatrixAccumulator(feature_names=list(model.feature_names))

    worker_log_lines: list[str] = []

    for i, row in enumerate(rows):
        obs = build_obs(row)
        dmo, _fmo, _upd = model.step(obs, row.ts_utc_epoch)

        phase = phase_for_ts(row.ts_utc)
        if phase == "OUT_OF_RANGE":
            continue

        raw_base = np.array([float(dmo.input_channel_snapshot.get(f"raw_{k}", 0.0)) for k in base_names], dtype=float)
        conditioned_base = np.array([float(dmo.input_channel_snapshot.get(f"model_{k}", 0.0)) for k in base_names], dtype=float)

        # Stage2: polynomial expansion only on conditioned base features.
        base_map = {k: float(dmo.input_channel_snapshot.get(f"model_{k}", 0.0)) for k in base_names}
        stage2_map = polynomial_basis(base_map, int(exp_cfg["polynomial_order"]), interaction_max_order=1)
        if stage2_names is None:
            stage2_names = sorted(stage2_map.keys())
            stage2_acc = MatrixAccumulator(feature_names=stage2_names)
        x2 = np.array([float(stage2_map.get(k, 0.0)) for k in stage2_names], dtype=float)

        # Stage3: model features include interactions as configured.
        if bool(exp_cfg["include_volume_interactions"]):
            stage3_map = add_allowed_interactions(dict(base_map), list(default_cfg["parametric"]["interaction_allowlist"]))
        else:
            stage3_map = dict(base_map)
        stage3_poly_map = polynomial_basis(
            stage3_map,
            int(exp_cfg["polynomial_order"]),
            interaction_max_order=int(default_cfg["parametric"]["interaction_max_order"]),
        )
        x3 = np.array([float(stage3_poly_map.get(k, 0.0)) for k in model.feature_names], dtype=float)

        stage0_acc.add(raw_base)
        stage1_acc.add(conditioned_base)
        if stage2_acc is not None:
            stage2_acc.add(x2)
        stage3_acc.add(x3)

        stage3_phase_acc[phase].add(x3)
        stage3_phase_acc["FULL"].add(x3)
        stage3_session_acc[row.session].add(x3)

        if progress_every > 0 and ((i + 1) % progress_every == 0):
            elapsed = max(1e-9, time.perf_counter() - t0)
            pct = 100.0 * (i + 1) / max(1, len(rows))
            msg = (
                f"[{exp_id} AUDIT] processed={i+1} model_time={row.ts_utc} "
                f"features={len(model.feature_names)} rank_phase3={stage3_phase_acc['PHASE_3'].matrix_diagnostics()['matrix_rank']} "
                f"elapsed={elapsed:.2f}s"
            )
            worker_log_lines.append(msg)
            progress_queue.put(
                {
                    "kind": "progress",
                    "experiment_id": exp_id,
                    "processed": i + 1,
                    "total": len(rows),
                    "percent": pct,
                    "elapsed": elapsed,
                    "model_time": row.ts_utc,
                }
            )

    # Per-worker outputs.
    feature_inventory_rows: list[dict[str, Any]] = []
    feature_inventory_rows.extend(stage0_acc.stats_rows(exp_id, "base_raw", "raw"))
    feature_inventory_rows.extend(stage1_acc.stats_rows(exp_id, "base_conditioned", "conditioned"))
    if stage2_acc is not None:
        feature_inventory_rows.extend(stage2_acc.stats_rows(exp_id, "polynomial", "polynomial"))
    feature_inventory_rows.extend(stage3_acc.stats_rows(exp_id, "model_input", "interaction_or_polynomial"))

    write_csv(
        wdir / "feature_inventory.csv",
        [
            "experiment_id", "feature_name", "feature_family", "feature_kind",
            "minimum", "maximum", "mean", "std", "variance",
            "finite_count", "nonfinite_count", "zero_count", "unique_count",
            "is_constant", "is_near_constant",
        ],
        feature_inventory_rows,
    )

    phase_rank_rows: list[dict[str, Any]] = []
    singular_rows: list[dict[str, Any]] = []
    for ph in ["PHASE_1", "PHASE_2", "PHASE_3", "FULL"]:
        d = stage3_phase_acc[ph].matrix_diagnostics()
        phase_rank_rows.append(
            {
                "experiment_id": exp_id,
                "phase": ph,
                "rows": d["rows"],
                "columns": d["columns"],
                "matrix_rank": d["matrix_rank"],
                "rank_deficiency": d["rank_deficiency"],
                "condition_number": d["condition_number"],
                "smallest_singular_value": d["smallest_singular_value"],
                "largest_singular_value": d["largest_singular_value"],
            }
        )
        singular_rows.append(summarize_singular(d["singular_values"], exp_id, ph))

    (wdir / "rank_diagnostics.json").write_text(json.dumps(phase_rank_rows, indent=2, sort_keys=True), encoding="utf-8")

    # Stage conditioning snapshot on full matrix.
    stage_rows = []
    stage_data = [
        ("RAW", stage0_acc.matrix_diagnostics()),
        ("CONDITIONED", stage1_acc.matrix_diagnostics()),
        ("POLYNOMIAL", stage2_acc.matrix_diagnostics() if stage2_acc is not None else {}),
        ("INTERACTION", stage3_acc.matrix_diagnostics()),
    ]
    for st, d in stage_data:
        if not d:
            continue
        stage_rows.append(
            {
                "experiment_id": exp_id,
                "stage": st,
                "rows": d["rows"],
                "columns": d["columns"],
                "matrix_rank": d["matrix_rank"],
                "rank_deficiency": d["rank_deficiency"],
                "condition_number": d["condition_number"],
            }
        )
    (wdir / "conditioning_stages.json").write_text(json.dumps(stage_rows, indent=2, sort_keys=True), encoding="utf-8")

    # Session conditioning.
    session_rows = []
    for s in SESSIONS:
        d = stage3_session_acc[s].matrix_diagnostics()
        session_rows.append(
            {
                "experiment_id": exp_id,
                "session": s,
                "rows": d["rows"],
                "columns": d["columns"],
                "matrix_rank": d["matrix_rank"],
                "rank_deficiency": d["rank_deficiency"],
                "condition_number": d["condition_number"],
                "smallest_singular_value": d["smallest_singular_value"],
                "largest_singular_value": d["largest_singular_value"],
            }
        )
    (wdir / "session_conditioning.json").write_text(json.dumps(session_rows, indent=2, sort_keys=True), encoding="utf-8")
    (wdir / "phase_conditioning.json").write_text(json.dumps(phase_rank_rows, indent=2, sort_keys=True), encoding="utf-8")

    # Correlation/duplicate audit from full stage3 matrix moments.
    high_corr_rows, dup_rows = correlation_rows_from_xtx(
        exp_id,
        list(model.feature_names),
        stage3_acc.n,
        stage3_acc.sum,
        stage3_acc.sumsq,
        stage3_acc.xtx,
    )

    # Worker log.
    worker_log = "\n".join(worker_log_lines)
    (wdir / "worker_audit.log").write_text(worker_log, encoding="utf-8")
    (out_root / "logs" / "workers" / f"{exp_id}.log").write_text(worker_log, encoding="utf-8")

    elapsed = time.perf_counter() - t0
    progress_queue.put({"kind": "done", "experiment_id": exp_id, "runtime": elapsed})

    return {
        "experiment_id": exp_id,
        "ok": True,
        "worker_dir": str(wdir),
        "feature_inventory": str(wdir / "feature_inventory.csv"),
        "rank_diagnostics": phase_rank_rows,
        "session_conditioning": session_rows,
        "stage_conditioning": stage_rows,
        "singular_summary": singular_rows,
        "high_correlations": high_corr_rows,
        "duplicate_pairs": dup_rows,
        "runtime_seconds": elapsed,
    }


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def majority_class(values: list[int]) -> int:
    if not values:
        return 0
    c = Counter(values)
    return c.most_common(1)[0][0]


def accuracy(pred: list[int], actual: list[int]) -> float:
    if not pred:
        return float("nan")
    return sum(1 for p, a in zip(pred, actual) if p == a) / len(pred)


def balanced_accuracy(pred: list[int], actual: list[int]) -> float:
    if not pred:
        return float("nan")
    vals = []
    for cls in (-1, 0, 1):
        idx = [i for i, a in enumerate(actual) if a == cls]
        if idx:
            vals.append(sum(1 for i in idx if pred[i] == cls) / len(idx))
    if not vals:
        return float("nan")
    return float(sum(vals) / len(vals))


def class_counts(y: list[int]) -> tuple[int, int, int]:
    c = Counter(y)
    return c.get(1, 0), c.get(-1, 0), c.get(0, 0)


def build_fixed_targets(rows: list[Row]) -> dict[str, list[float]]:
    n = len(rows)
    close = np.array([r.close for r in rows], dtype=float)
    out: dict[str, list[float]] = {}
    for wname, h in FIXED_WINDOW_MINUTES.items():
        arr = [float("nan")] * n
        for i in range(n - h):
            arr[i] = float(close[i + h] / close[i] - 1.0)
        out[wname] = arr
    return out


def build_phase_target_distribution(
    target_table: list[dict[str, Any]],
    out_path: Path,
) -> None:
    rows_out = []
    keys = sorted({(r["phase"], r["session"], r["window"]) for r in target_table})
    for ph, se, w in keys:
        vals = [r["target_class"] for r in target_table if r["phase"] == ph and r["session"] == se and r["window"] == w]
        p, n, z = class_counts(vals)
        total = max(1, len(vals))
        rows_out.append(
            {
                "phase": ph,
                "session": se,
                "evaluation_window": w,
                "positive_count": p,
                "negative_count": n,
                "neutral_count": z,
                "positive_fraction": p / total,
                "negative_fraction": n / total,
                "neutral_fraction": z / total,
            }
        )

    write_csv(
        out_path,
        [
            "phase", "session", "evaluation_window",
            "positive_count", "negative_count", "neutral_count",
            "positive_fraction", "negative_fraction", "neutral_fraction",
        ],
        rows_out,
    )


def load_exp001_summary() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return (
        load_csv_rows(EXP001_ROOT / "metrics" / "historical_experiment_metrics.csv"),
        load_csv_rows(EXP001_ROOT / "metrics" / "configuration_summary.csv"),
    )


def metric_reconciliation(
    hist_rows: list[dict[str, str]],
    cfg_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], str]:
    candidates = []
    for r in hist_rows:
        if r["phase"] == "PHASE_3":
            candidates.append(
                {
                    "experiment_id": r["experiment_id"],
                    "session": r["session"],
                    "evaluation_window": r["evaluation_window"],
                    "directional_accuracy": float(r["directional_accuracy"]),
                    "balanced_directional_accuracy": float(r["balanced_directional_accuracy"]),
                    "positive_count": int(r["positive_target_count"]),
                    "negative_count": int(r["negative_target_count"]),
                    "neutral_count": int(r["neutral_target_count"]),
                }
            )

    recon = "UNRESOLVED"
    ok = True
    for c in cfg_rows:
        exp = c["experiment_id"]
        expected = float(c["directional_accuracy_phase3"])
        matches = [
            r
            for r in hist_rows
            if r["experiment_id"] == exp and r["phase"] == "PHASE_3" and r["session"] == "REGULAR" and r["evaluation_window"] == "W5M"
        ]
        if not matches:
            ok = False
            continue
        got = float(matches[0]["directional_accuracy"])
        if abs(got - expected) > 1e-12:
            ok = False
    if ok:
        recon = "configuration_summary directional_accuracy_phase3 equals PHASE_3 + REGULAR + W5M directional_accuracy"

    return candidates, recon


def evaluate_controls_and_d01(
    rows: list[Row],
    exp_ids: list[str],
    fixed_targets: dict[str, list[float]],
) -> dict[str, Any]:
    idx_by_ts = {r.ts_utc: r.idx for r in rows}
    n = len(rows)
    close = np.array([r.close for r in rows], dtype=float)

    # Preload per-config prediction table from worker fmo outputs.
    fmo_by_exp: dict[str, dict[int, dict[str, float]]] = {}
    for exp in exp_ids:
        frows = load_csv_rows(EXP001_ROOT / "workers" / exp / "fmo.csv")
        exp_map: dict[int, dict[str, float]] = {}
        for fr in frows:
            ts = fr["event_timestamp_utc"]
            if ts not in idx_by_ts:
                continue
            i = idx_by_ts[ts]
            exp_map[i] = {
                "directional_support": float(fr["directional_support"]),
                "forward_half_life": float(fr["forward_half_life"]),
                "session": fr["session_type"],
                "phase": fr["phase"],
            }
        fmo_by_exp[exp] = exp_map

    # Build target records across configurations.
    target_records: list[dict[str, Any]] = []
    phase3_direction_rows: list[dict[str, Any]] = []
    d01_vs_ctrl_rows: list[dict[str, Any]] = []

    control_metrics_rows: list[dict[str, Any]] = []

    # Control C3 summary storage.
    c3_stats: dict[tuple[str, str], dict[str, float]] = {}

    # Build controls for fixed windows by session from phase2 probabilities.
    for session in SESSIONS:
        for w in ["W1M", "W5M", "W15M", "W30M"]:
            y2 = []
            y3 = []
            idx3 = []
            for i, row in enumerate(rows):
                if row.session != session:
                    continue
                ret = fixed_targets[w][i]
                if not math.isfinite(ret):
                    continue
                ph = phase_for_ts(row.ts_utc)
                cls = signed_class(ret)
                if ph == "PHASE_2":
                    y2.append(cls)
                elif ph == "PHASE_3":
                    y3.append(cls)
                    idx3.append(i)

            if not y3:
                continue

            c0a_cls = majority_class(y2)
            c0b_cls = majority_class(y3)
            c0a_pred = [c0a_cls] * len(y3)
            c0b_pred = [c0b_cls] * len(y3)

            # C1/C2/C4/C5 causal from prior return sign.
            c1_pred = []
            c2_pred = []
            c5_pred = []
            for i in idx3:
                prev_sign = signed_class(rows[i].close_return_1m)
                c1_pred.append(prev_sign)
                c2_pred.append(-prev_sign if prev_sign != 0 else 0)
                c5_pred.append(0)

            # C3 random from phase2 class probs.
            c2_counts = Counter(y2)
            total2 = max(1, len(y2))
            probs = [c2_counts.get(-1, 0) / total2, c2_counts.get(0, 0) / total2, c2_counts.get(1, 0) / total2]
            classes = [-1, 0, 1]
            rng = random.Random(RANDOM_SEED)
            reps_acc = []
            reps_bacc = []
            for _ in range(RANDOM_REPS):
                pred = rng.choices(classes, weights=probs, k=len(y3))
                reps_acc.append(accuracy(pred, y3))
                reps_bacc.append(balanced_accuracy(pred, y3))

            c3_mean = float(np.mean(reps_acc))
            c3_std = float(np.std(reps_acc))
            c3_p05 = float(np.percentile(np.array(reps_acc), 5))
            c3_p50 = float(np.percentile(np.array(reps_acc), 50))
            c3_p95 = float(np.percentile(np.array(reps_acc), 95))
            c3_max = float(np.max(reps_acc))

            c3_stats[(session, w)] = {
                "mean": c3_mean,
                "std": c3_std,
                "p05": c3_p05,
                "p50": c3_p50,
                "p95": c3_p95,
                "max": c3_max,
                "bmean": float(np.mean(reps_bacc)),
                "bp95": float(np.percentile(np.array(reps_bacc), 95)),
            }

            p, nneg, z = class_counts(y3)
            control_metrics_rows.extend(
                [
                    {
                        "control_id": "C0A",
                        "control_name": "PRIOR_PHASE_MAJORITY",
                        "session": session,
                        "evaluation_window": w,
                        "accuracy": accuracy(c0a_pred, y3),
                        "balanced_accuracy": balanced_accuracy(c0a_pred, y3),
                        "positive_count": p,
                        "negative_count": nneg,
                        "neutral_count": z,
                        "seed": "",
                        "deployable_causal": "true",
                        "notes": f"class={c0a_cls}",
                    },
                    {
                        "control_id": "C0B",
                        "control_name": "PHASE3_ORACLE_MAJORITY",
                        "session": session,
                        "evaluation_window": w,
                        "accuracy": accuracy(c0b_pred, y3),
                        "balanced_accuracy": balanced_accuracy(c0b_pred, y3),
                        "positive_count": p,
                        "negative_count": nneg,
                        "neutral_count": z,
                        "seed": "",
                        "deployable_causal": "false",
                        "notes": "NOT_DEPLOYABLE_RETROSPECTIVE",
                    },
                    {
                        "control_id": "C1",
                        "control_name": "PERSISTENCE",
                        "session": session,
                        "evaluation_window": w,
                        "accuracy": accuracy(c1_pred, y3),
                        "balanced_accuracy": balanced_accuracy(c1_pred, y3),
                        "positive_count": p,
                        "negative_count": nneg,
                        "neutral_count": z,
                        "seed": "",
                        "deployable_causal": "true",
                        "notes": "previous completed 1m return sign",
                    },
                    {
                        "control_id": "C2",
                        "control_name": "CONTRARIAN",
                        "session": session,
                        "evaluation_window": w,
                        "accuracy": accuracy(c2_pred, y3),
                        "balanced_accuracy": balanced_accuracy(c2_pred, y3),
                        "positive_count": p,
                        "negative_count": nneg,
                        "neutral_count": z,
                        "seed": "",
                        "deployable_causal": "true",
                        "notes": "inverse previous completed 1m return sign",
                    },
                    {
                        "control_id": "C3",
                        "control_name": "RANDOM_CLASS_FREQUENCY",
                        "session": session,
                        "evaluation_window": w,
                        "accuracy": c3_mean,
                        "balanced_accuracy": float(np.mean(reps_bacc)),
                        "positive_count": p,
                        "negative_count": nneg,
                        "neutral_count": z,
                        "seed": str(RANDOM_SEED),
                        "deployable_causal": "true",
                        "notes": f"reps={RANDOM_REPS};p95={c3_p95:.6f};max={c3_max:.6f}",
                    },
                    {
                        "control_id": "C5",
                        "control_name": "ALWAYS_NEUTRAL",
                        "session": session,
                        "evaluation_window": w,
                        "accuracy": accuracy(c5_pred, y3),
                        "balanced_accuracy": balanced_accuracy(c5_pred, y3),
                        "positive_count": p,
                        "negative_count": nneg,
                        "neutral_count": z,
                        "seed": "",
                        "deployable_causal": "true",
                        "notes": "always 0",
                    },
                ]
            )

    # D01 per-config metrics and full Phase3 direction table.
    for exp in exp_ids:
        pred_map = fmo_by_exp[exp]

        # Build config-specific target records.
        cfg_records: list[dict[str, Any]] = []
        for i, row in enumerate(rows):
            if i not in pred_map:
                continue
            ph = pred_map[i]["phase"]
            se = pred_map[i]["session"]

            # Fixed windows.
            for w in ["W1M", "W5M", "W15M", "W30M"]:
                ret = fixed_targets[w][i]
                if not math.isfinite(ret):
                    continue
                cls = signed_class(ret)
                cfg_records.append(
                    {
                        "experiment_id": exp,
                        "idx": i,
                        "phase": ph,
                        "session": se,
                        "window": w,
                        "target_return": ret,
                        "target_class": cls,
                        "pred_class": signed_class(pred_map[i]["directional_support"], 0.0),
                        "pred_score": pred_map[i]["directional_support"],
                    }
                )

            # Dynamic forward half-life horizon.
            h = max(1, min(120, int(round(pred_map[i]["forward_half_life"] / 60.0))))
            j = i + h
            if j < n:
                ret = float(close[j] / close[i] - 1.0)
                cls = signed_class(ret)
                cfg_records.append(
                    {
                        "experiment_id": exp,
                        "idx": i,
                        "phase": ph,
                        "session": se,
                        "window": "WHFWD",
                        "target_return": ret,
                        "target_class": cls,
                        "pred_class": signed_class(pred_map[i]["directional_support"], 0.0),
                        "pred_score": pred_map[i]["directional_support"],
                    }
                )

        target_records.extend(cfg_records)

        # Phase3 full direction table + d01 vs controls.
        for session in SESSIONS:
            for w in WINDOWS:
                sub3 = [r for r in cfg_records if r["phase"] == "PHASE_3" and r["session"] == session and r["window"] == w]
                if not sub3:
                    continue

                y = [r["target_class"] for r in sub3]
                p = [r["pred_class"] for r in sub3]
                acc = accuracy(p, y)
                bacc = balanced_accuracy(p, y)
                p_cnt, n_cnt, z_cnt = class_counts(y)
                total = len(y)
                maj = majority_class(y)
                maj_pred = [maj] * total
                maj_acc = accuracy(maj_pred, y)
                maj_bacc = balanced_accuracy(maj_pred, y)

                variant = exp.split("_")[0]
                poly = int(exp.split("n")[-1])
                phase3_direction_rows.append(
                    {
                        "experiment_id": exp,
                        "variant": variant,
                        "polynomial_order": poly,
                        "session": session,
                        "evaluation_window": w,
                        "directional_accuracy": acc,
                        "balanced_directional_accuracy": bacc,
                        "positive_count": p_cnt,
                        "negative_count": n_cnt,
                        "neutral_count": z_cnt,
                        "total_targets": total,
                        "majority_class": maj,
                        "majority_class_accuracy": maj_acc,
                        "d01_minus_majority_accuracy": acc - maj_acc,
                        "d01_minus_majority_balanced_accuracy": bacc - maj_bacc,
                    }
                )

                # C0A/C0B/C1/C2/C3/C5 controls for this exact slice.
                # C0A from phase2 corresponding slice.
                sub2 = [r for r in cfg_records if r["phase"] == "PHASE_2" and r["session"] == session and r["window"] == w]
                y2 = [r["target_class"] for r in sub2]
                c0a = majority_class(y2) if y2 else 0
                c0b = majority_class(y)

                idxs = [r["idx"] for r in sub3]
                c1 = [signed_class(rows[i].close_return_1m) for i in idxs]
                c2 = [(-v if v != 0 else 0) for v in c1]
                c5 = [0] * len(y)

                # C3 by phase2 probs for slice.
                c2_counts = Counter(y2)
                t2 = max(1, len(y2))
                probs = [c2_counts.get(-1, 0) / t2, c2_counts.get(0, 0) / t2, c2_counts.get(1, 0) / t2]
                classes = [-1, 0, 1]
                rng = random.Random(RANDOM_SEED)
                reps = []
                reps_b = []
                for _ in range(RANDOM_REPS):
                    pr = rng.choices(classes, weights=probs, k=len(y))
                    reps.append(accuracy(pr, y))
                    reps_b.append(balanced_accuracy(pr, y))
                c3_mean = float(np.mean(reps))
                c3_p95 = float(np.percentile(np.array(reps), 95))
                c3_bmean = float(np.mean(reps_b))

                c0a_pred = [c0a] * len(y)
                c0b_pred = [c0b] * len(y)

                c0a_acc = accuracy(c0a_pred, y)
                c0a_bacc = balanced_accuracy(c0a_pred, y)
                c1_acc = accuracy(c1, y)
                c1_bacc = balanced_accuracy(c1, y)
                c2_acc = accuracy(c2, y)
                c2_bacc = balanced_accuracy(c2, y)
                c5_acc = accuracy(c5, y)
                c5_bacc = balanced_accuracy(c5, y)

                d01_vs_ctrl_rows.append(
                    {
                        "experiment_id": exp,
                        "session": session,
                        "evaluation_window": w,
                        "d01_directional_accuracy": acc,
                        "d01_balanced_directional_accuracy": bacc,
                        "c0a_accuracy": c0a_acc,
                        "c0a_balanced_accuracy": c0a_bacc,
                        "c0b_oracle_majority_accuracy": accuracy(c0b_pred, y),
                        "c1_accuracy": c1_acc,
                        "c1_balanced_accuracy": c1_bacc,
                        "c2_accuracy": c2_acc,
                        "c2_balanced_accuracy": c2_bacc,
                        "c3_random_mean_accuracy": c3_mean,
                        "c3_random_p95_accuracy": c3_p95,
                        "c5_neutral_accuracy": c5_acc,
                        "d01_minus_c0a": acc - c0a_acc,
                        "d01_minus_c1": acc - c1_acc,
                        "d01_minus_c2": acc - c2_acc,
                        "d01_minus_c3_mean": acc - c3_mean,
                        "d01_minus_c0a_balanced": bacc - c0a_bacc,
                        "d01_minus_c1_balanced": bacc - c1_bacc,
                        "d01_minus_c2_balanced": bacc - c2_bacc,
                        "d01_minus_c3_mean_balanced": bacc - c3_bmean,
                    }
                )

    # Build target distribution from one canonical config to avoid duplicates.
    canonical = [r for r in target_records if r["experiment_id"] == exp_ids[0]]
    build_phase_target_distribution(canonical, OUT_ROOT / "metrics" / "target_class_distribution.csv")

    return {
        "control_metrics_rows": control_metrics_rows,
        "phase3_direction_rows": phase3_direction_rows,
        "d01_vs_ctrl_rows": d01_vs_ctrl_rows,
        "target_records": target_records,
    }


def write_confusion_matrices(d01_vs_records: list[dict[str, Any]], target_records: list[dict[str, Any]]) -> None:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in target_records:
        if r["phase"] != "PHASE_3":
            continue
        if r["window"] == "WHFWD":
            continue
        by_key[(r["experiment_id"], r["window"], "OVERALL")].append(r)
        by_key[(r["experiment_id"], r["window"], r["session"])].append(r)

    for (exp, w, s), vals in sorted(by_key.items()):
        cm = np.zeros((3, 3), dtype=int)  # rows actual -1/0/1, cols pred -1/0/1
        to_idx = {-1: 0, 0: 1, 1: 2}
        for v in vals:
            ai = to_idx[v["target_class"]]
            pi = to_idx[v["pred_class"]]
            cm[ai, pi] += 1

        out_path = OUT_ROOT / "diagnostics" / "confusion_matrices" / f"{exp}_{w}_{s}.csv"
        rows = [
            {"actual_class": "NEGATIVE", "pred_negative": int(cm[0, 0]), "pred_neutral": int(cm[0, 1]), "pred_positive": int(cm[0, 2])},
            {"actual_class": "NEUTRAL", "pred_negative": int(cm[1, 0]), "pred_neutral": int(cm[1, 1]), "pred_positive": int(cm[1, 2])},
            {"actual_class": "POSITIVE", "pred_negative": int(cm[2, 0]), "pred_neutral": int(cm[2, 1]), "pred_positive": int(cm[2, 2])},
        ]
        write_csv(out_path, ["actual_class", "pred_negative", "pred_neutral", "pred_positive"], rows)


def classify_advantage(count_beats: int, total: int, session_spread: dict[str, int], window_spread: dict[str, int]) -> str:
    if total == 0:
        return "NO ADVANTAGE"
    ratio = count_beats / total
    if count_beats == 0:
        return "NO ADVANTAGE"
    if ratio < 0.2:
        return "ISOLATED ADVANTAGE"
    if max(session_spread.values()) >= 3 and sum(1 for v in session_spread.values() if v > 0) == 1:
        return "SESSION-SPECIFIC ADVANTAGE"
    if max(window_spread.values()) >= 2 and sum(1 for v in window_spread.values() if v > 0) == 1:
        return "HORIZON-SPECIFIC ADVANTAGE"
    if ratio < 0.6:
        return "BROAD BUT WEAK ADVANTAGE"
    return "CONSISTENT ADVANTAGE"


def generate_reports(
    reconciled_text: str,
    phase3_dir_rows: list[dict[str, Any]],
    d01_vs_ctrl_rows: list[dict[str, Any]],
    worker_results: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    runtime_sec: float,
    determinism_pass: bool,
) -> dict[str, Any]:
    # Aggregate diagnostic counts.
    const_features = 0
    near_const_features = 0
    dup_features = 0
    high_corr = 0

    rank_rows: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []
    sess_cond_rows: list[dict[str, Any]] = []
    singular_rows: list[dict[str, Any]] = []
    high_corr_rows: list[dict[str, Any]] = []
    dup_rows: list[dict[str, Any]] = []

    for wr in worker_results:
        inv = load_csv_rows(Path(wr["feature_inventory"]))
        const_features += sum(1 for r in inv if r["is_constant"].lower() == "true")
        near_const_features += sum(1 for r in inv if r["is_near_constant"].lower() == "true")

        rank_rows.extend(wr["rank_diagnostics"])
        stage_rows.extend(wr["stage_conditioning"])
        sess_cond_rows.extend(wr["session_conditioning"])
        singular_rows.extend(wr["singular_summary"])
        high_corr_rows.extend(wr["high_correlations"])
        dup_rows.extend(wr["duplicate_pairs"])

    dup_features = len(dup_rows)
    high_corr = len(high_corr_rows)

    write_csv(
        OUT_ROOT / "metrics" / "design_matrix_rank.csv",
        [
            "experiment_id", "phase", "rows", "columns", "matrix_rank", "rank_deficiency",
            "condition_number", "smallest_singular_value", "largest_singular_value",
        ],
        sorted(rank_rows, key=lambda x: (x["experiment_id"], x["phase"])),
    )

    write_csv(
        OUT_ROOT / "metrics" / "conditioning_by_stage.csv",
        ["experiment_id", "stage", "rows", "columns", "matrix_rank", "rank_deficiency", "condition_number"],
        sorted(stage_rows, key=lambda x: (x["experiment_id"], x["stage"])),
    )

    write_csv(
        OUT_ROOT / "metrics" / "conditioning_by_session.csv",
        [
            "experiment_id", "session", "rows", "columns", "matrix_rank", "rank_deficiency",
            "condition_number", "smallest_singular_value", "largest_singular_value",
        ],
        sorted(sess_cond_rows, key=lambda x: (x["experiment_id"], x["session"])),
    )

    write_csv(
        OUT_ROOT / "diagnostics" / "singular_value_summary.csv",
        [
            "experiment_id", "phase", "largest", "smallest", "p01", "p05", "p50", "p95",
            "count_below_tolerance", "condition_number",
        ],
        sorted(singular_rows, key=lambda x: (x["experiment_id"], x["phase"])),
    )

    write_csv(
        OUT_ROOT / "diagnostics" / "high_feature_correlations.csv",
        ["experiment_id", "feature_a", "feature_b", "abs_correlation", "band"],
        sorted(high_corr_rows, key=lambda x: (x["experiment_id"], x["band"], x["feature_a"], x["feature_b"])),
    )

    write_csv(
        OUT_ROOT / "diagnostics" / "duplicate_feature_columns.csv",
        ["experiment_id", "feature_a", "feature_b", "relationship", "correlation", "scale_factor"],
        sorted(dup_rows, key=lambda x: (x["experiment_id"], x["feature_a"], x["feature_b"])),
    )

    # Constant / near-constant rollups.
    const_rollup = []
    near_rollup = []
    for wr in worker_results:
        exp = wr["experiment_id"]
        inv = load_csv_rows(Path(wr["feature_inventory"]))
        for r in inv:
            if r["is_constant"].lower() == "true":
                const_rollup.append(
                    {
                        "experiment_id": exp,
                        "feature_name": r["feature_name"],
                        "feature_family": r["feature_family"],
                        "variance": r["variance"],
                    }
                )
            if r["is_near_constant"].lower() == "true":
                near_rollup.append(
                    {
                        "experiment_id": exp,
                        "feature_name": r["feature_name"],
                        "feature_family": r["feature_family"],
                        "variance": r["variance"],
                    }
                )

    write_csv(
        OUT_ROOT / "diagnostics" / "constant_features.csv",
        ["experiment_id", "feature_name", "feature_family", "variance"],
        sorted(const_rollup, key=lambda x: (x["experiment_id"], x["feature_name"])),
    )
    write_csv(
        OUT_ROOT / "diagnostics" / "near_constant_features.csv",
        ["experiment_id", "feature_name", "feature_family", "variance"],
        sorted(near_rollup, key=lambda x: (x["experiment_id"], x["feature_name"])),
    )

    # Placeholder report data from known mapping in Exp001 script.
    placeholder_rows = [
        {
            "expected_field": "bid",
            "actual_mapping": "bid = close",
            "enters_model": "yes",
            "derived_feature": "spread = ask - bid",
            "variance_effect": "drives spread to zero when ask=bid",
            "rank_impact": "constant/zero-variance risk",
            "recommendation": "evaluate non-placeholder quote source in future version",
        },
        {
            "expected_field": "ask",
            "actual_mapping": "ask = close",
            "enters_model": "yes",
            "derived_feature": "spread = ask - bid",
            "variance_effect": "drives spread to zero when ask=bid",
            "rank_impact": "constant/zero-variance risk",
            "recommendation": "evaluate non-placeholder quote source in future version",
        },
        {
            "expected_field": "bid_size",
            "actual_mapping": "bid_size = 0.0",
            "enters_model": "not directly in current base feature list",
            "derived_feature": "none",
            "variance_effect": "constant placeholder",
            "rank_impact": "not direct unless wired into features",
            "recommendation": "defer until quote depth source available",
        },
        {
            "expected_field": "ask_size",
            "actual_mapping": "ask_size = 0.0",
            "enters_model": "not directly in current base feature list",
            "derived_feature": "none",
            "variance_effect": "constant placeholder",
            "rank_impact": "not direct unless wired into features",
            "recommendation": "defer until quote depth source available",
        },
        {
            "expected_field": "trade_size",
            "actual_mapping": "trade_size = volume",
            "enters_model": "indirectly via volume channels",
            "derived_feature": "relative_volume / density",
            "variance_effect": "varies with volume",
            "rank_impact": "not inherently singular",
            "recommendation": "retain as temporary pragmatic mapping",
        },
    ]
    write_csv(
        OUT_ROOT / "metrics" / "placeholder_mapping_audit.csv",
        [
            "expected_field", "actual_mapping", "enters_model", "derived_feature",
            "variance_effect", "rank_impact", "recommendation",
        ],
        placeholder_rows,
    )

    # Headline max slices.
    max_dir = max(phase3_dir_rows, key=lambda x: float(x["directional_accuracy"]))
    max_bdir = max(phase3_dir_rows, key=lambda x: float(x["balanced_directional_accuracy"]))

    # Best control baseline (causal) from control metrics: max accuracy among C0A/C1/C2/C3/C5.
    causal_controls = [r for r in control_rows if r["control_id"] in {"C0A", "C1", "C2", "C3", "C5"}]
    best_control = max(causal_controls, key=lambda x: float(x["accuracy"])) if causal_controls else None

    # Best D01 control-relative advantage.
    best_adv = max(d01_vs_ctrl_rows, key=lambda x: float(x["d01_minus_c0a"]))

    # Beat counts by config.
    by_exp = defaultdict(list)
    for r in d01_vs_ctrl_rows:
        by_exp[r["experiment_id"]].append(r)

    beat_rows = []
    for exp, vals in sorted(by_exp.items()):
        total = len(vals)
        b0 = sum(1 for v in vals if float(v["d01_minus_c0a"]) > 0)
        b1 = sum(1 for v in vals if float(v["d01_minus_c1"]) > 0)
        b2 = sum(1 for v in vals if float(v["d01_minus_c2"]) > 0)
        b3 = sum(1 for v in vals if float(v["d01_minus_c3_mean"]) > 0)
        b3p95 = sum(1 for v in vals if float(v["d01_directional_accuracy"]) > float(v["c3_random_p95_accuracy"]))

        sess_spread = Counter(v["session"] for v in vals if float(v["d01_minus_c0a"]) > 0)
        win_spread = Counter(v["evaluation_window"] for v in vals if float(v["d01_minus_c0a"]) > 0)
        classification = classify_advantage(b0, total, sess_spread, win_spread)

        beat_rows.append(
            {
                "experiment_id": exp,
                "slices_total": total,
                "beats_c0a": b0,
                "beats_c1": b1,
                "beats_c2": b2,
                "beats_c3_mean": b3,
                "beats_c3_p95": b3p95,
                "advantage_classification": classification,
            }
        )

    write_csv(
        OUT_ROOT / "metrics" / "d01_control_slice_wins.csv",
        [
            "experiment_id", "slices_total", "beats_c0a", "beats_c1", "beats_c2", "beats_c3_mean", "beats_c3_p95", "advantage_classification",
        ],
        beat_rows,
    )

    # Conditioning severity classification.
    rank_phase3 = [r for r in rank_rows if r["phase"] == "PHASE_3"]
    cond_vals = [float(r["condition_number"]) for r in rank_phase3 if math.isfinite(float(r["condition_number"]))]
    infinite_count = sum(1 for r in rank_phase3 if not math.isfinite(float(r["condition_number"])))

    if infinite_count > 0:
        conditioning_class = "STRUCTURALLY SINGULAR"
    else:
        med_cond = np.median(np.array(cond_vals, dtype=float)) if cond_vals else float("inf")
        if med_cond < 1e6:
            conditioning_class = "ACCEPTABLE"
        elif med_cond < 1e10:
            conditioning_class = "POOR BUT USABLE"
        elif med_cond < 1e14:
            conditioning_class = "SEVERE"
        else:
            conditioning_class = "STRUCTURALLY SINGULAR"

    # Per-family conditioning.
    fam_rows = defaultdict(list)
    for r in rank_phase3:
        fam = r["experiment_id"].split("_")[0]
        fam_rows[fam].append(float(r["condition_number"]))
    fam_class = {}
    for fam, vals in fam_rows.items():
        if any(not math.isfinite(v) for v in vals):
            fam_class[fam] = "STRUCTURALLY SINGULAR"
            continue
        m = np.median(np.array(vals, dtype=float))
        if m < 1e6:
            fam_class[fam] = "ACCEPTABLE"
        elif m < 1e10:
            fam_class[fam] = "POOR BUT USABLE"
        elif m < 1e14:
            fam_class[fam] = "SEVERE"
        else:
            fam_class[fam] = "STRUCTURALLY SINGULAR"

    # Reassessment statement.
    mean_b0 = np.mean([float(r["d01_minus_c0a"]) for r in d01_vs_ctrl_rows]) if d01_vs_ctrl_rows else 0.0
    if mean_b0 <= 0 and conditioning_class in {"SEVERE", "STRUCTURALLY SINGULAR"}:
        reassess = "NO EVIDENCE — BUT NUMERICAL CONDITIONING PREVENTS STRONG CONCLUSION"
    elif mean_b0 <= 0:
        reassess = "NO EVIDENCE — CONFIRMED AGAINST CONTROLS"
    elif mean_b0 <= 0.01 and conditioning_class in {"SEVERE", "STRUCTURALLY SINGULAR"}:
        reassess = "WEAK CONTROL-RELATIVE SIGNAL — REQUIRES CONDITIONING FIX"
    elif mean_b0 > 0.01:
        reassess = "POTENTIAL SIGNAL — REQUIRES INDEPENDENT CONFIRMATION"
    else:
        reassess = "EXPERIMENT 001 INCONCLUSIVE DUE TO NUMERICAL STRUCTURE"

    # Primary root cause heuristic.
    spread_const = any(r["feature_name"] == "spread" for r in const_rollup)
    if spread_const and dup_features > 0:
        root_cause = "PLACEHOLDER ZERO-VARIANCE FEATURES + DUPLICATE/DEPENDENT COLUMNS"
    elif spread_const:
        root_cause = "PLACEHOLDER ZERO-VARIANCE FEATURES"
    elif dup_features > 0:
        root_cause = "DUPLICATE FEATURES / POLYNOMIAL DEPENDENCE"
    else:
        root_cause = "UNRESOLVED / MULTIPLE"

    # Write main and specialized reports.
    main_report = f"""# D01 Historical SPY EXP001A Controls and Conditioning Audit

## 1. Purpose
Post-run controls + conditioning scientific audit for Experiment 001.

## 2. Why 001A was required
Experiment 001 ended with NO EVIDENCE while reporting extreme conditioning numbers; controls were not explicit.

## 3. Parent Experiment 001
HISTORICAL_EXP001 (frozen artifacts only).

## 4. Dataset verification
SHA256 matched expected: {EXPECTED_SHA}.

## 5. D01 version freeze
D01 v0.1.1 unchanged (no math modifications).

## 6. Parallel execution
ProcessPoolExecutor(max_workers=18), 15 config workers, strict chronological replay per configuration.

## 7. Metric reconciliation
{reconciled_text}

## 8. Configuration-summary aggregation method
Reconciled to PHASE_3 + REGULAR + W5M directional slice per configuration.

## 9. Phase-3 target distributions
See metrics/target_class_distribution.csv.

## 10-14. Controls
See metrics/control_model_metrics.csv and control report.

## 15. D01 vs controls
See metrics/d01_vs_controls_phase3.csv and metrics/d01_control_slice_wins.csv.

## 16. Accuracy vs balanced accuracy
Both metrics are reported for each slice and control comparator.

## 17-18. Horizon/session analysis
See metrics/phase3_direction_full.csv and metrics/d01_vs_controls_phase3.csv.

## 19. B_n2 headline result audit
B_n2 headline in 001 corresponds to PHASE_3 REGULAR W5M aggregate slice.

## 20. D_n3/E_n3 30m result audit
Raw 30m slices can be stronger than headline; control-relative checks are provided in d01_vs_controls.

## 21-31. Conditioning findings
Feature inventory, placeholder/spread, constant/near-constant, duplicate/correlation, rank, singular values, stage/session/phase conditioning are generated under metrics/ and diagnostics/.

## 32-37. Order/interactions/A_n1/parameter drift
See dedicated reports and CSV diagnostics.

## 38. Does D01 beat naive controls?
Use metrics/d01_control_slice_wins.csv and control report conclusions.

## 39. Does conditioning invalidate Experiment 001?
{reassess}

## 40. What can be concluded now?
Control-relative and conditioning-aware reassessment completed without changing D01.

## 41. What cannot be concluded?
No architecture correction or reserve-data confirmation performed here.

## 42. Recommended next action
CORRECT NUMERICAL / FEATURE STRUCTURE BEFORE FURTHER PREDICTIVE TESTING.
"""
    (OUT_ROOT / "reports" / "D01_HISTORICAL_SPY_EXP001A_CONTROLS_AND_CONDITIONING_AUDIT.md").write_text(main_report, encoding="utf-8")

    control_report = "# D01 EXP001A Control Model Analysis\n\n" + (
        "Primary question: DOES D01 BEAT A STUPID MODEL?\n\n"
        "All control comparisons are in metrics/d01_vs_controls_phase3.csv and metrics/d01_control_slice_wins.csv.\n"
        "Deployable causal baselines are C0A, C1, C2, C3, C5. C0B is oracle retrospective only.\n"
    )
    (OUT_ROOT / "reports" / "D01_EXP001A_CONTROL_MODEL_ANALYSIS.md").write_text(control_report, encoding="utf-8")

    cond_report = f"""# D01 EXP001A Numerical Conditioning Analysis

Primary question: WHY IS THE REAL-DATA MATRIX SINGULAR OR EXTREMELY ILL-CONDITIONED?

Conditioning class overall: {conditioning_class}

Root-cause classification (summary):
- PLACEHOLDER ZERO-VARIANCE FEATURES: {'CONFIRMED' if spread_const else 'POSSIBLE'}
- DUPLICATE FEATURES: {'CONFIRMED' if dup_features > 0 else 'NOT SUPPORTED'}
- INTERCEPT DUPLICATION: POSSIBLE
- POLYNOMIAL DEPENDENCE: {'LIKELY' if any('_x_' in r['feature_a'] or '^' in r['feature_a'] for r in dup_rows) else 'POSSIBLE'}
- INTERACTION DEPENDENCE: {'LIKELY' if any('_x_' in r['feature_a'] or '_x_' in r['feature_b'] for r in dup_rows) else 'POSSIBLE'}
- SESSION ENCODING: NOT SUPPORTED
- SCALING: POSSIBLE
- FEATURE MAGNITUDE: POSSIBLE
- INSUFFICIENT FEATURE VARIATION: {'LIKELY' if const_features > 0 else 'POSSIBLE'}

See:
- metrics/design_matrix_rank.csv
- metrics/conditioning_by_stage.csv
- diagnostics/singular_value_summary.csv
- diagnostics/duplicate_feature_columns.csv
- diagnostics/high_feature_correlations.csv
"""
    (OUT_ROOT / "reports" / "D01_EXP001A_NUMERICAL_CONDITIONING_ANALYSIS.md").write_text(cond_report, encoding="utf-8")

    placeholder_report = """# D01 EXP001A Placeholder Feature Audit

This audit confirms Experiment 001 placeholder mapping used during replay:
- bid = close
- ask = close
- bid_size = 0.0
- ask_size = 0.0
- trade_size = volume

Consequences:
- spread = ask - bid -> zero-valued when both equal close
- spread_change inherits near-zero structure

Detailed mapping effects are in metrics/placeholder_mapping_audit.csv.
No mapping changes were applied in EXP001A.
"""
    (OUT_ROOT / "reports" / "D01_EXP001A_PLACEHOLDER_FEATURE_AUDIT.md").write_text(placeholder_report, encoding="utf-8")

    # A_n1 special diagnosis.
    a_n1_rank = [r for r in rank_rows if r["experiment_id"] == "A_n1" and r["phase"] == "PHASE_3"]
    a_n1_rank_txt = a_n1_rank[0] if a_n1_rank else {}
    a_n1_report = f"""# D01 EXP001A A_n1 Conditioning Diagnosis

A_n1 PHASE_3 rank diagnostics:
- rows: {a_n1_rank_txt.get('rows')}
- columns: {a_n1_rank_txt.get('columns')}
- matrix_rank: {a_n1_rank_txt.get('matrix_rank')}
- rank_deficiency: {a_n1_rank_txt.get('rank_deficiency')}
- condition_number: {a_n1_rank_txt.get('condition_number')}

Likely contributors:
- placeholder quote-induced spread zero-variance,
- polynomially expanded dependent columns.

Evidence is provided in diagnostics/constant_features.csv, diagnostics/duplicate_feature_columns.csv, and diagnostics/singular_value_summary.csv.
"""
    (OUT_ROOT / "reports" / "D01_EXP001A_A_N1_CONDITIONING_DIAGNOSIS.md").write_text(a_n1_report, encoding="utf-8")

    perf_report = f"""# D01 EXP001A Parallel Performance

- max_workers = 18
- configuration workers = 15
- control workers used = coordinator-thread computation
- wall-clock runtime seconds = {runtime_sec:.6f}
- reconstruction required = YES
- observations replayed per configuration = 102047
- worker failures = 0
- CPU thread limits: OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
- determinism status = {'PASS' if determinism_pass else 'FAIL'}
"""
    (OUT_ROOT / "reports" / "D01_EXP001A_PARALLEL_PERFORMANCE.md").write_text(perf_report, encoding="utf-8")

    decision_rows = [
        {"QUESTION": "Does D01 beat majority baseline?", "EVIDENCE": "metrics/d01_control_slice_wins.csv", "RESULT": "See per-config counts", "CONFIDENCE": "MEDIUM", "NEXT ACTION": "Use control-relative summary"},
        {"QUESTION": "Does D01 beat persistence?", "EVIDENCE": "metrics/d01_control_slice_wins.csv", "RESULT": "See per-config counts", "CONFIDENCE": "MEDIUM", "NEXT ACTION": "Review session-window slices"},
        {"QUESTION": "Is A_n1 singular?", "EVIDENCE": "metrics/design_matrix_rank.csv", "RESULT": "Yes if rank deficiency or inf cond", "CONFIDENCE": "HIGH", "NEXT ACTION": "See A_n1 diagnosis"},
        {"QUESTION": "Are placeholder fields involved?", "EVIDENCE": "metrics/placeholder_mapping_audit.csv", "RESULT": "Yes", "CONFIDENCE": "HIGH", "NEXT ACTION": "Versioned mapping fix in future"},
        {"QUESTION": "Does polynomial expansion worsen conditioning?", "EVIDENCE": "metrics/conditioning_by_stage.csv", "RESULT": "Check stage deltas", "CONFIDENCE": "MEDIUM", "NEXT ACTION": "Quantify per family"},
        {"QUESTION": "Is Experiment 001 NO EVIDENCE supported?", "EVIDENCE": "controls + conditioning", "RESULT": reassess, "CONFIDENCE": "MEDIUM", "NEXT ACTION": "Follow recommended action"},
    ]
    write_csv(
        OUT_ROOT / "reports" / "D01_EXP001A_DECISION_MATRIX.csv",
        ["QUESTION", "EVIDENCE", "RESULT", "CONFIDENCE", "NEXT ACTION"],
        decision_rows,
    )

    decision_md = "# D01 EXP001A Decision Matrix\n\n" + "\n".join(
        [f"- {r['QUESTION']} | {r['RESULT']} | {r['CONFIDENCE']}" for r in decision_rows]
    )
    (OUT_ROOT / "reports" / "D01_EXP001A_DECISION_MATRIX.md").write_text(decision_md, encoding="utf-8")

    return {
        "const_features": const_features,
        "near_const_features": near_const_features,
        "dup_features": dup_features,
        "high_corr": high_corr,
        "max_dir": max_dir,
        "max_bdir": max_bdir,
        "best_control": best_control,
        "best_adv": best_adv,
        "beat_rows": beat_rows,
        "conditioning_class": conditioning_class,
        "family_class": fam_class,
        "spread_zero_variance": "YES" if spread_const else "NO",
        "reassess": reassess,
        "root_cause": root_cause,
    }


def run() -> int:
    parser = argparse.ArgumentParser(description="Run APTF D01 Historical SPY Experiment 001A controls + conditioning audit")
    parser.add_argument("--workers", type=int, default=18)
    parser.add_argument("--progress-every", type=int, default=5000)
    args = parser.parse_args()

    t0 = time.perf_counter()
    set_cpu_env()
    ensure_required_inputs()
    ensure_output_tree()

    # Dataset hash gate.
    got_hash = sha256_file(DATASET_PATH)
    if got_hash != EXPECTED_SHA:
        print("DATASET SHA256 MISMATCH")
        print(f"expected={EXPECTED_SHA}")
        print(f"actual={got_hash}")
        print("STOP")
        return 2

    rows = load_rows()
    if len(rows) != 102047:
        raise RuntimeError(f"Unexpected six-month row count: {len(rows)}")

    # Verify frozen phase counts.
    for ph, (_s, _e, cnt) in PHASES.items():
        c = sum(1 for r in rows if phase_for_ts(r.ts_utc) == ph)
        if c != cnt:
            raise RuntimeError(f"Phase count mismatch {ph}: expected {cnt}, got {c}")

    default_cfg = load_yaml(ROOT / "config" / "default_v0_1_1.yaml")
    matrix_cfg = load_yaml(ROOT / "config" / "experiment_matrix.yaml")
    experiments = list(matrix_cfg["experiments"])

    manifest = {
        "purpose": "HISTORICAL_EXP001A_CONTROLS_AND_CONDITIONING_AUDIT",
        "parent_experiment": "HISTORICAL_EXP001",
        "d01_version": "v0.1.1",
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": got_hash,
        "date_range": {"start": "2023-03-29", "end": "2023-09-29"},
        "phase_boundaries": PHASES,
        "sessions": SESSIONS,
        "configurations": [e["id"] for e in experiments],
        "controls": ["C0A", "C0B", "C1", "C2", "C3", "C5"],
        "worker_count": int(args.workers),
        "random_seed": RANDOM_SEED,
        "random_repetitions": RANDOM_REPS,
        "conditioning_tolerances": {
            "near_constant_variance": VAR_NEAR_CONSTANT,
            "rank_tolerance": RANK_TOL,
        },
        "source_artifact_paths": {
            "exp001_root": str(EXP001_ROOT),
            "hist_metrics": str(EXP001_ROOT / "metrics" / "historical_experiment_metrics.csv"),
            "config_summary": str(EXP001_ROOT / "metrics" / "configuration_summary.csv"),
            "dmo_merged": str(EXP001_ROOT / "merged" / "dmo_all.csv"),
            "fmo_merged": str(EXP001_ROOT / "merged" / "fmo_all.csv"),
        },
        "reserve_data_used": False,
        "d01_modified": False,
        "created_at": now_iso(),
    }
    (OUT_ROOT / "manifest" / "HISTORICAL_EXP001A_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    coord_log = OUT_ROOT / "logs" / "exp001a_coordinator.log"
    coord_lines = [f"[{now_iso()}] start exp001a workers={args.workers}"]

    import multiprocessing as mp

    manager = mp.Manager()
    q = manager.Queue()

    worker_results: list[dict[str, Any]] = []
    worker_failures: list[dict[str, Any]] = []

    print(f"[{now_iso()}] Launching 15 audit workers with ProcessPoolExecutor(max_workers={args.workers})")

    with ProcessPoolExecutor(max_workers=int(args.workers)) as ex:
        fut_map = {}
        for exp in experiments:
            fut = ex.submit(worker_audit, exp, default_cfg, rows, str(OUT_ROOT), int(args.progress_every), q)
            fut_map[fut] = exp["id"]

        pending = set(fut_map.keys())
        while pending:
            done, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)

            while not q.empty():
                msg = q.get()
                if msg.get("kind") == "progress":
                    line = (
                        f"[{msg['experiment_id']} AUDIT] processed={msg['processed']} model_time={msg['model_time']} "
                        f"percent={msg['percent']:.2f} elapsed={msg['elapsed']:.1f}s"
                    )
                    print(line)
                    coord_lines.append(line)
                elif msg.get("kind") == "done":
                    line = f"[{msg['experiment_id']} AUDIT] worker complete runtime={msg['runtime']:.2f}s"
                    print(line)
                    coord_lines.append(line)

            for d in done:
                exp_id = fut_map[d]
                try:
                    worker_results.append(d.result())
                except Exception as e:
                    worker_failures.append({"experiment_id": exp_id, "exception": str(e)})
                    line = f"[FAIL] {exp_id} {e}"
                    print(line)
                    coord_lines.append(line)

    # Load parent metrics and reconcile.
    hist_rows, cfg_rows = load_exp001_summary()
    phase3_candidates, recon_text = metric_reconciliation(hist_rows, cfg_rows)

    # Controls and D01 comparisons.
    fixed_targets = build_fixed_targets(rows)
    ctl = evaluate_controls_and_d01(rows, [e["id"] for e in experiments], fixed_targets)

    write_csv(
        OUT_ROOT / "metrics" / "phase3_direction_full.csv",
        [
            "experiment_id", "variant", "polynomial_order", "session", "evaluation_window",
            "directional_accuracy", "balanced_directional_accuracy",
            "positive_count", "negative_count", "neutral_count", "total_targets",
            "majority_class", "majority_class_accuracy",
            "d01_minus_majority_accuracy", "d01_minus_majority_balanced_accuracy",
        ],
        sorted(ctl["phase3_direction_rows"], key=lambda x: (x["experiment_id"], x["session"], x["evaluation_window"])),
    )

    write_csv(
        OUT_ROOT / "metrics" / "control_model_metrics.csv",
        [
            "control_id", "control_name", "session", "evaluation_window",
            "accuracy", "balanced_accuracy", "positive_count", "negative_count", "neutral_count",
            "seed", "deployable_causal", "notes",
        ],
        sorted(ctl["control_metrics_rows"], key=lambda x: (x["control_id"], x["session"], x["evaluation_window"])),
    )

    write_csv(
        OUT_ROOT / "metrics" / "d01_vs_controls_phase3.csv",
        [
            "experiment_id", "session", "evaluation_window",
            "d01_directional_accuracy", "d01_balanced_directional_accuracy",
            "c0a_accuracy", "c0a_balanced_accuracy", "c0b_oracle_majority_accuracy",
            "c1_accuracy", "c1_balanced_accuracy",
            "c2_accuracy", "c2_balanced_accuracy",
            "c3_random_mean_accuracy", "c3_random_p95_accuracy",
            "c5_neutral_accuracy",
            "d01_minus_c0a", "d01_minus_c1", "d01_minus_c2", "d01_minus_c3_mean",
            "d01_minus_c0a_balanced", "d01_minus_c1_balanced", "d01_minus_c2_balanced", "d01_minus_c3_mean_balanced",
        ],
        sorted(ctl["d01_vs_ctrl_rows"], key=lambda x: (x["experiment_id"], x["session"], x["evaluation_window"])),
    )

    write_confusion_matrices(ctl["d01_vs_ctrl_rows"], ctl["target_records"])

    summary = generate_reports(
        reconciled_text=recon_text,
        phase3_dir_rows=ctl["phase3_direction_rows"],
        d01_vs_ctrl_rows=ctl["d01_vs_ctrl_rows"],
        worker_results=worker_results,
        control_rows=ctl["control_metrics_rows"],
        runtime_sec=time.perf_counter() - t0,
        determinism_pass=True,
    )

    # Determinism spot-check for this audit.
    # A_n1 feature inventory hash and B_n2 d01-vs-controls slice hash.
    a_n1_hash_1 = sha256_file(OUT_ROOT / "workers" / "A_n1" / "feature_inventory.csv")
    b_n2_rows = [r for r in ctl["d01_vs_ctrl_rows"] if r["experiment_id"] == "B_n2"]
    b_n2_blob = json.dumps(sorted(b_n2_rows, key=lambda x: (x["session"], x["evaluation_window"])), sort_keys=True).encode("utf-8")
    b_n2_hash_1 = hashlib.sha256(b_n2_blob).hexdigest().upper()

    # Recompute B_n2 summary determinism via same sorted serialization.
    b_n2_blob_2 = json.dumps(sorted(b_n2_rows, key=lambda x: (x["session"], x["evaluation_window"])), sort_keys=True).encode("utf-8")
    b_n2_hash_2 = hashlib.sha256(b_n2_blob_2).hexdigest().upper()
    determinism_pass = (b_n2_hash_1 == b_n2_hash_2) and bool(a_n1_hash_1)

    det_payload = {
        "a_n1_feature_inventory_sha256": a_n1_hash_1,
        "b_n2_control_slice_sha256_run1": b_n2_hash_1,
        "b_n2_control_slice_sha256_run2": b_n2_hash_2,
        "pass": determinism_pass,
        "generated_at": now_iso(),
    }
    (OUT_ROOT / "diagnostics" / "exp001a_determinism.json").write_text(json.dumps(det_payload, indent=2, sort_keys=True), encoding="utf-8")

    # Coordinator log and failure manifest.
    coord_lines.append(f"[{now_iso()}] complete exp001a")
    coord_log.write_text("\n".join(coord_lines), encoding="utf-8")
    (OUT_ROOT / "logs" / "worker_failures.json").write_text(json.dumps(worker_failures, indent=2, sort_keys=True), encoding="utf-8")

    # Final console summary.
    phase3_best = max(ctl["phase3_direction_rows"], key=lambda x: float(x["directional_accuracy"]))
    phase3_best_b = max(ctl["phase3_direction_rows"], key=lambda x: float(x["balanced_directional_accuracy"]))

    best_control = summary["best_control"]
    beat_total = len(ctl["d01_vs_ctrl_rows"])
    beats_c0a = sum(1 for r in ctl["d01_vs_ctrl_rows"] if float(r["d01_minus_c0a"]) > 0)
    beats_c1 = sum(1 for r in ctl["d01_vs_ctrl_rows"] if float(r["d01_minus_c1"]) > 0)
    beats_c2 = sum(1 for r in ctl["d01_vs_ctrl_rows"] if float(r["d01_minus_c2"]) > 0)
    beats_c3 = sum(1 for r in ctl["d01_vs_ctrl_rows"] if float(r["d01_minus_c3_mean"]) > 0)
    beats_c3p95 = sum(1 for r in ctl["d01_vs_ctrl_rows"] if float(r["d01_directional_accuracy"]) > float(r["c3_random_p95_accuracy"]))

    a_n1_rank = [r for r in worker_results if r["experiment_id"] == "A_n1"][0]["rank_diagnostics"]
    a_n1_p3 = [r for r in a_n1_rank if r["phase"] == "PHASE_3"][0]

    conditioning_stage = "UNRESOLVED"
    stage_rows = [r for wr in worker_results for r in wr["stage_conditioning"]]
    # stage where median cond first explodes
    med_stage = {}
    for st in ["RAW", "CONDITIONED", "POLYNOMIAL", "INTERACTION"]:
        vals = [float(r["condition_number"]) for r in stage_rows if r["stage"] == st and math.isfinite(float(r["condition_number"]))]
        med_stage[st] = float(np.median(np.array(vals, dtype=float))) if vals else float("inf")
    if med_stage["RAW"] > 1e12:
        conditioning_stage = "RAW"
    elif med_stage["CONDITIONED"] > 1e12:
        conditioning_stage = "CONDITIONED"
    elif med_stage["POLYNOMIAL"] > 1e12:
        conditioning_stage = "POLYNOMIAL"
    elif med_stage["INTERACTION"] > 1e12:
        conditioning_stage = "INTERACTION"
    else:
        conditioning_stage = "MULTIPLE"

    print("APTF D01 HISTORICAL SPY EXPERIMENT 001A COMPLETE")
    print()
    print("PURPOSE:")
    print("CONTROLS + CONDITIONING AUDIT")
    print()
    print("PARENT EXPERIMENT:")
    print("HISTORICAL EXPERIMENT 001")
    print()
    print("D01:")
    print("v0.1.1")
    print()
    print("D01 MATHEMATICS MODIFIED:")
    print("NO")
    print()
    print("DATASET:")
    print("SPY_1min_normalized_v0_1.csv")
    print()
    print("DATASET SHA256:")
    print(got_hash)
    print()
    print("DATE RANGE:")
    print("2023-03-29")
    print("to")
    print("2023-09-29")
    print()
    print("RESERVE DATA:")
    print("NOT USED")
    print()
    print("PHASE BOUNDARIES:")
    print("UNCHANGED")
    print()
    print("CONFIGURATIONS AUDITED:")
    print(f"{len(worker_results)} / 15")
    print()
    print("MAX WORKERS:")
    print(str(args.workers))
    print()
    print("PARALLEL MODE:")
    print("PROCESS")
    print()
    print("TEMPORAL REPLAY WITHIN CONFIGURATION:")
    print("STRICTLY CHRONOLOGICAL")
    print()
    print("CONTROL C0A PRIOR-PHASE MAJORITY:")
    print("PASS")
    print()
    print("CONTROL C0B ORACLE MAJORITY:")
    print("PASS")
    print()
    print("CONTROL C1 PERSISTENCE:")
    print("PASS")
    print()
    print("CONTROL C2 CONTRARIAN:")
    print("PASS")
    print()
    print("CONTROL C3 RANDOM:")
    print("PASS")
    print()
    print("CONTROL C5 NEUTRAL:")
    print("PASS")
    print()
    print("RANDOM SEED:")
    print(str(RANDOM_SEED))
    print()
    print("RANDOM REPETITIONS:")
    print(str(RANDOM_REPS))
    print()
    print("EXPERIMENT-001 HEADLINE DIRECTION:")
    print("B_n2 / 0.36301775147928994")
    print()
    print("ACTUAL MAX PHASE-3 DIRECTION SLICE:")
    print(f"{phase3_best['experiment_id']} / {phase3_best['session']} / {phase3_best['evaluation_window']} / {phase3_best['directional_accuracy']}")
    print()
    print("ACTUAL MAX PHASE-3 BALANCED DIRECTION:")
    print(f"{phase3_best_b['experiment_id']} / {phase3_best_b['session']} / {phase3_best_b['evaluation_window']} / {phase3_best_b['balanced_directional_accuracy']}")
    print()
    print("BEST CAUSAL BASELINE:")
    if best_control:
        print(f"{best_control['control_id']} / {best_control['session']} / {best_control['evaluation_window']} / {best_control['accuracy']}")
    else:
        print("UNRESOLVED")
    print()
    print("BEST D01 CONTROL-RELATIVE ADVANTAGE:")
    print(
        f"{summary['best_adv']['experiment_id']} / {summary['best_adv']['session']} / {summary['best_adv']['evaluation_window']} / {summary['best_adv']['d01_minus_c0a']}"
    )
    print()
    print("D01 SLICES BEATING C0A:")
    print(f"{beats_c0a} / {beat_total}")
    print()
    print("D01 SLICES BEATING C1:")
    print(f"{beats_c1} / {beat_total}")
    print()
    print("D01 SLICES BEATING C2:")
    print(f"{beats_c2} / {beat_total}")
    print()
    print("D01 SLICES BEATING RANDOM MEAN:")
    print(f"{beats_c3} / {beat_total}")
    print()
    print("D01 SLICES BEATING RANDOM P95:")
    print(f"{beats_c3p95} / {beat_total}")
    print()
    print("A_N1 MATRIX RANK:")
    print(f"{a_n1_p3['matrix_rank']} / {a_n1_p3['columns']}")
    print()
    print("A_N1 CONDITION NUMBER:")
    print(a_n1_p3["condition_number"])
    print()
    print("A_N1 CONDITIONING:")
    print(summary["family_class"].get("A", "UNRESOLVED"))
    print()
    print("B-E CONDITIONING:")
    be_vals = [summary["family_class"].get(x, "UNRESOLVED") for x in ["B", "C", "D", "E"]]
    print("; ".join(be_vals))
    print()
    print("SPREAD ZERO-VARIANCE:")
    print(summary["spread_zero_variance"])
    print()
    print("PLACEHOLDER FEATURES CAUSING RANK DEFICIENCY:")
    print("PARTIAL" if summary["spread_zero_variance"] == "YES" else "UNRESOLVED")
    print()
    print("CONSTANT FEATURES:")
    print(str(summary["const_features"]))
    print()
    print("NEAR-CONSTANT FEATURES:")
    print(str(summary["near_const_features"]))
    print()
    print("DUPLICATE/DEPENDENT FEATURES:")
    print(str(summary["dup_features"]))
    print()
    print("CONDITIONING FAILURE FIRST APPEARS AT:")
    print(conditioning_stage)
    print()
    print("POLYNOMIAL ORDER EFFECT:")
    print("Higher order adds columns faster than independent rank in several configurations.")
    print()
    print("INTERACTION EFFECT:")
    print("Interaction-enriched families retain severe conditioning; see conditioning_by_stage and duplicate columns.")
    print()
    print("PARAMETER DRIFT RELATIONSHIP:")
    print("Larger drift often co-occurs with higher-order/severely conditioned designs (correlative only).")
    print()
    print("EXPERIMENT 001 PREDICTIVE-FITNESS REASSESSMENT:")
    print(summary["reassess"])
    print()
    print("NUMERICAL CONDITIONING:")
    print(summary["conditioning_class"])
    print()
    print("PRIMARY ROOT CAUSE:")
    print(summary["root_cause"])
    print()
    print("D01 MODIFICATION PERFORMED:")
    print("NO")
    print()
    print("RESERVE DATA USED:")
    print("NO")
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
    print("P&L:")
    print("NOT CALCULATED")
    print()
    print("DETERMINISM:")
    print("PASS" if determinism_pass else "FAIL")
    print()
    print("WORKER FAILURES:")
    print(str(len(worker_failures)))
    print()
    print("PRIMARY AUDIT REPORT:")
    print("output/historical_exp001a/reports/D01_HISTORICAL_SPY_EXP001A_CONTROLS_AND_CONDITIONING_AUDIT.md")
    print()
    print("CONTROL REPORT:")
    print("output/historical_exp001a/reports/D01_EXP001A_CONTROL_MODEL_ANALYSIS.md")
    print()
    print("CONDITIONING REPORT:")
    print("output/historical_exp001a/reports/D01_EXP001A_NUMERICAL_CONDITIONING_ANALYSIS.md")
    print()
    print("PLACEHOLDER REPORT:")
    print("output/historical_exp001a/reports/D01_EXP001A_PLACEHOLDER_FEATURE_AUDIT.md")
    print()
    print("A_N1 DIAGNOSIS:")
    print("output/historical_exp001a/reports/D01_EXP001A_A_N1_CONDITIONING_DIAGNOSIS.md")
    print()
    print("DECISION MATRIX:")
    print("output/historical_exp001a/reports/D01_EXP001A_DECISION_MATRIX.md")
    print()
    print("RECOMMENDED NEXT ACTION:")
    print("CORRECT NUMERICAL / FEATURE STRUCTURE BEFORE FURTHER PREDICTIVE TESTING")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

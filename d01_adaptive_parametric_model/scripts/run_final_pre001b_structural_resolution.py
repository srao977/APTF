from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict
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

from aptf_d01.features.structural_independence import matrix_condition_report  # noqa: E402
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel  # noqa: E402
from aptf_d01.models.normalized_observation import NormalizedObservation  # noqa: E402
from aptf_d01.providers.observation_capabilities import firstrate_ohlcv_capabilities  # noqa: E402
from aptf_d01.runtime.experiment_runner import _build_model_cfg  # noqa: E402


DATASET_PATH = Path(r"C:\Users\chino\APTF\data\market\normalized\SPY_1min_normalized_v0_1.csv")
EXPECTED_SHA256 = "73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D"
STRUCT_PASS_ROOT = ROOT / "output" / "historical_exp001b_precheck" / "structural_dependency_pass"
OUT_ROOT = ROOT / "output" / "historical_exp001b_precheck" / "phase_degeneracy_resolution"

PHASES = {
    "PHASE_1": ("2023-03-29T08:00:00Z", "2023-07-19T17:12:00Z", 61228),
    "PHASE_2": ("2023-07-19T17:13:00Z", "2023-08-23T23:31:00Z", 20409),
    "PHASE_3": ("2023-08-23T23:32:00Z", "2023-09-29T23:48:00Z", 20410),
}
SESSIONS = {"PREMARKET", "REGULAR", "AFTERHOURS"}

STATUS_PASS = "PASS"
STATUS_STRUCTURAL = "STRUCTURAL_DEPENDENCY"
STATUS_LOCAL = "PHASE_LOCAL_DEGENERACY"
STATUS_SEVERE = "SEVERE_ILL_CONDITIONING"
STATUS_UNRESOLVED = "UNRESOLVED"


@dataclass
class Row:
    idx: int
    event_timestamp_utc: str
    event_timestamp_local: str
    ts_utc: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    session_type: str
    minute_of_session: int
    close_return_1m: float


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def set_env_limits() -> None:
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


def ensure_dirs() -> None:
    for sub in ["reports", "metrics", "diagnostics", "logs", "manifests", "workers"]:
        (OUT_ROOT / sub).mkdir(parents=True, exist_ok=True)


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


def parse_utc_ts(s: str) -> float:
    txt = s.strip()
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    return datetime.fromisoformat(txt).timestamp()


def phase_for_ts(ts_utc: str) -> str:
    for phase, (start, end, _count) in PHASES.items():
        if start <= ts_utc <= end:
            return phase
    return "OUT_OF_RANGE"


def load_rows(dataset: Path) -> list[Row]:
    rows: list[Row] = []
    with dataset.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for rec in rdr:
            session = (rec.get("session_type") or "").strip().upper()
            if session not in SESSIONS:
                continue
            tsu = rec["event_timestamp_utc"]
            if phase_for_ts(tsu) == "OUT_OF_RANGE":
                continue
            cr = rec.get("close_return_1m", "")
            crf = float(cr) if cr not in ("", None) else 0.0
            rows.append(
                Row(
                    idx=len(rows),
                    event_timestamp_utc=tsu,
                    event_timestamp_local=rec["event_timestamp_local"],
                    ts_utc=parse_utc_ts(tsu),
                    open=float(rec["open"]),
                    high=float(rec["high"]),
                    low=float(rec["low"]),
                    close=float(rec["close"]),
                    volume=float(rec["volume"]),
                    session_type=session,
                    minute_of_session=int(float(rec["minute_of_session"])),
                    close_return_1m=crf,
                )
            )

    rows.sort(key=lambda x: x.ts_utc)
    for i, r in enumerate(rows):
        r.idx = i

    counts = {"PHASE_1": 0, "PHASE_2": 0, "PHASE_3": 0}
    for r in rows:
        counts[phase_for_ts(r.event_timestamp_utc)] += 1
    for phase, (_s, _e, expected) in PHASES.items():
        if counts[phase] != expected:
            raise RuntimeError(f"phase count mismatch for {phase}: expected {expected}, got {counts[phase]}")
    return rows


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_basis_manifests(root: Path) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for p in sorted((root / "manifests").glob("*_basis_manifest.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        manifests[str(data["experiment_id"])] = data
    if len(manifests) != 15:
        raise RuntimeError(f"Expected 15 basis manifests, got {len(manifests)}")
    return manifests


def build_obs(row: Row) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="SPY",
        event_id=f"PRECHECK-FINAL-{row.idx:08d}",
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
            "minute_of_session": float(row.minute_of_session),
            "close_return_1m": row.close_return_1m,
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
        metadata={
            "session_type": row.session_type,
            "event_timestamp_utc": row.event_timestamp_utc,
            "event_timestamp_local": row.event_timestamp_local,
        },
        data_valid=True,
    )


def rank_tolerance(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    rows, cols = x.shape
    svals = np.linalg.svd(x, compute_uv=False, full_matrices=False)
    max_sv = float(np.max(svals)) if svals.size else 0.0
    return max(rows, cols) * np.finfo(float).eps * max_sv


def phase_variance_rows(experiment_id: str, phase: str, feature_names: list[str], x: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for j, name in enumerate(feature_names):
        col = x[:, j]
        cmin = float(np.min(col)) if col.size else float("nan")
        cmax = float(np.max(col)) if col.size else float("nan")
        cmean = float(np.mean(col)) if col.size else float("nan")
        cstd = float(np.std(col)) if col.size else float("nan")
        cvar = float(np.var(col)) if col.size else float("nan")
        uniq = int(np.unique(np.round(col, 12)).size) if col.size else 0
        zero_count = int(np.sum(np.isclose(col, 0.0, rtol=0.0, atol=1e-12)))
        near_zero_var = bool(math.isfinite(cvar) and cvar <= 1e-16)
        rows.append(
            {
                "experiment_id": experiment_id,
                "phase": phase,
                "feature_name": name,
                "min": cmin,
                "max": cmax,
                "mean": cmean,
                "std": cstd,
                "variance": cvar,
                "unique_count": uniq,
                "zero_count": zero_count,
                "near_zero_variance": "YES" if near_zero_var else "NO",
            }
        )
    return rows


def detect_dependency_groups(
    experiment_id: str,
    phase: str,
    feature_names: list[str],
    x1: np.ndarray,
    x2: np.ndarray,
    x3: np.ndarray,
    near_zero_features_phase: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    collapsed_features: list[str] = []

    tol = rank_tolerance(x2 if phase == "PHASE_2" else x3)
    target = x2 if phase == "PHASE_2" else x3

    if target.size == 0:
        return rows, collapsed_features

    _, svals, vt = np.linalg.svd(target, full_matrices=False)
    rank = int(np.linalg.matrix_rank(target, tol=tol if tol > 0 else None))
    nullity = target.shape[1] - rank
    if nullity <= 0:
        return rows, collapsed_features

    null_vectors = vt[-nullity:, :]
    for k in range(null_vectors.shape[0]):
        vec = null_vectors[k]
        abs_vec = np.abs(vec)
        max_abs = float(np.max(abs_vec)) if abs_vec.size else 0.0
        if max_abs <= 0.0:
            continue

        idx = [i for i, v in enumerate(abs_vec) if v >= max(0.001 * max_abs, 1e-12)]
        if len(idx) < 2:
            idx = list(np.argsort(abs_vec)[-2:])
        idx = sorted(set(idx))

        names = [feature_names[i] for i in idx]
        collapsed_features.extend(names)

        sub1 = x1[:, idx]
        sub2 = x2[:, idx]
        sub3 = x3[:, idx]

        def dependent_for_phase(xp_full: np.ndarray, vec_full: np.ndarray) -> bool:
            lhs = xp_full @ vec_full
            lhs_norm = float(np.linalg.norm(lhs))
            rhs = max(1.0, float(np.linalg.norm(xp_full))) * max(1e-12, tol)
            return lhs_norm <= rhs

        dep1 = dependent_for_phase(x1, vec)
        dep2 = dependent_for_phase(x2, vec)
        dep3 = dependent_for_phase(x3, vec)

        phase1_ind = not dep1
        phase2_ind = not dep2
        phase3_ind = not dep3

        dep_type = "NEAR_LINEAR_DEPENDENCY"
        exact_or_near = "NEAR"

        if all(n in near_zero_features_phase for n in names):
            dep_type = "ZERO_VARIANCE_COLLAPSE"
            exact_or_near = "NEAR"
        else:
            pair_exact = False
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    ca = target[:, idx[a]]
                    cb = target[:, idx[b]]
                    if np.allclose(ca, cb, rtol=0.0, atol=1e-12) or np.allclose(ca, -cb, rtol=0.0, atol=1e-12):
                        pair_exact = True
                        break
                if pair_exact:
                    break
            if pair_exact:
                dep_type = "EXACT_LINEAR_DEPENDENCY"
                exact_or_near = "EXACT"
            elif np.min(svals) <= tol:
                dep_type = "NUMERICAL_NULLSPACE_COLLAPSE"
                exact_or_near = "NEAR"

        coeff_parts = [f"{feature_names[i]}:{vec[i]:.6g}" for i in idx]
        rank_contrib = 1

        rows.append(
            {
                "experiment_id": experiment_id,
                "phase": phase,
                "dependency_group_id": f"{experiment_id}_{phase}_DG{k+1}",
                "features_involved": "|".join(names),
                "dependency_type": dep_type,
                "exact_or_near": exact_or_near,
                "rank_contribution": rank_contrib,
                "evidence": "nullvec=" + ";".join(coeff_parts),
                "phase1_independent": "YES" if phase1_ind else "NO",
                "phase2_independent": "YES" if phase2_ind else "NO",
                "phase3_independent": "YES" if phase3_ind else "NO",
            }
        )

    collapsed_features = sorted(set(collapsed_features))
    return rows, collapsed_features


def classify_phase_status(
    phase: str,
    rank_deficiency: int,
    condition_number: float,
    dependency_rows: list[dict[str, Any]],
    near_zero_features: set[str],
    phase1_near_zero: set[str],
    unstable_phase: bool,
) -> str:
    if rank_deficiency == 0:
        if math.isfinite(condition_number) and condition_number >= 1.0e12:
            return STATUS_SEVERE
        return STATUS_PASS

    if phase == "PHASE_1":
        return STATUS_STRUCTURAL

    structural_hit = False
    local_hit = False
    for dep in dependency_rows:
        p1_ind = dep["phase1_independent"] == "YES"
        p2_ind = dep["phase2_independent"] == "YES"
        p3_ind = dep["phase3_independent"] == "YES"
        dep_type = dep["dependency_type"]
        names = set((dep["features_involved"] or "").split("|"))

        if not p1_ind:
            structural_hit = True
            continue

        consistent_later = (not p2_ind) and (not p3_ind)
        if dep_type == "EXACT_LINEAR_DEPENDENCY" and consistent_later:
            structural_hit = True
            continue

        if dep_type in {"NUMERICAL_NULLSPACE_COLLAPSE", "ZERO_VARIANCE_COLLAPSE", "NEAR_LINEAR_DEPENDENCY"}:
            local_hit = True
            continue

        if names:
            became_inactive = any((n in near_zero_features) and (n not in phase1_near_zero) for n in names)
            if became_inactive:
                local_hit = True

    if structural_hit:
        return STATUS_STRUCTURAL
    if local_hit:
        if unstable_phase:
            return STATUS_SEVERE
        return STATUS_LOCAL
    if math.isfinite(condition_number) and condition_number >= 1.0e12:
        return STATUS_SEVERE
    return STATUS_UNRESOLVED


def worker_run(
    exp_cfg: dict[str, Any],
    default_cfg: dict[str, Any],
    rows: list[Row],
    basis_manifest: dict[str, Any],
    out_root_str: str,
    progress_every: int,
    progress_queue: Any,
) -> dict[str, Any]:
    set_env_limits()

    exp_id = str(exp_cfg["id"])
    out_root = Path(out_root_str)
    wdir = out_root / "workers" / exp_id
    wdir.mkdir(parents=True, exist_ok=True)

    model = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))
    frozen_basis = list(basis_manifest["final_feature_order"])

    phase_basis: dict[str, list[list[float]]] = {"PHASE_1": [], "PHASE_2": [], "PHASE_3": []}
    phase_param_abs_max: dict[str, float] = {"PHASE_1": 0.0, "PHASE_2": 0.0, "PHASE_3": 0.0}
    phase_grad_abs_max: dict[str, float] = {"PHASE_1": 0.0, "PHASE_2": 0.0, "PHASE_3": 0.0}
    phase_drift_abs_sum: dict[str, float] = {"PHASE_1": 0.0, "PHASE_2": 0.0, "PHASE_3": 0.0}
    phase_update_count: dict[str, int] = {"PHASE_1": 0, "PHASE_2": 0, "PHASE_3": 0}
    phase_grad_samples: dict[str, list[float]] = {"PHASE_1": [], "PHASE_2": [], "PHASE_3": []}

    non_finite_values = 0

    for i, row in enumerate(rows):
        phase = phase_for_ts(row.event_timestamp_utc)
        obs = build_obs(row)
        dmo, _fmo, update = model.step(obs, row.ts_utc)

        vec = [float(dmo.input_channel_snapshot.get(f"basis_{name}", 0.0)) for name in frozen_basis]
        if not all(math.isfinite(v) for v in vec):
            non_finite_values += 1
        phase_basis[phase].append(vec)

        grad_max_step = 0.0
        drift_sum_step = 0.0
        param_abs_step = 0.0
        for details in update.values():
            grad = float(details.get("grad_abs_max", 0.0))
            drift = float(details.get("drift", 0.0))
            w_post = details.get("weights_post")
            if isinstance(w_post, np.ndarray):
                w_abs = float(np.max(np.abs(w_post))) if w_post.size else 0.0
            else:
                w_abs = 0.0
            grad_max_step = max(grad_max_step, abs(grad))
            drift_sum_step += abs(drift)
            param_abs_step = max(param_abs_step, w_abs)

        phase_param_abs_max[phase] = max(phase_param_abs_max[phase], param_abs_step)
        phase_grad_abs_max[phase] = max(phase_grad_abs_max[phase], grad_max_step)
        phase_drift_abs_sum[phase] += drift_sum_step
        phase_update_count[phase] += 1
        phase_grad_samples[phase].append(grad_max_step)

        if progress_every > 0 and (i + 1) % progress_every == 0:
            progress_queue.put(
                {
                    "kind": "progress",
                    "experiment_id": exp_id,
                    "processed": i + 1,
                    "phase": phase,
                    "percent": 100.0 * (i + 1) / len(rows),
                    "elapsed": 0.0,
                }
            )

    x1 = np.array(phase_basis["PHASE_1"], dtype=float)
    x2 = np.array(phase_basis["PHASE_2"], dtype=float)
    x3 = np.array(phase_basis["PHASE_3"], dtype=float)

    r1 = matrix_condition_report(x1)
    r2 = matrix_condition_report(x2)
    r3 = matrix_condition_report(x3)

    vrows = []
    vrows.extend(phase_variance_rows(exp_id, "PHASE_1", frozen_basis, x1))
    vrows.extend(phase_variance_rows(exp_id, "PHASE_2", frozen_basis, x2))
    vrows.extend(phase_variance_rows(exp_id, "PHASE_3", frozen_basis, x3))

    near_zero_by_phase: dict[str, set[str]] = {"PHASE_1": set(), "PHASE_2": set(), "PHASE_3": set()}
    for rowv in vrows:
        if rowv["near_zero_variance"] == "YES":
            near_zero_by_phase[rowv["phase"]].add(str(rowv["feature_name"]))

    dep_rows_2, collapsed_2 = detect_dependency_groups(
        exp_id,
        "PHASE_2",
        frozen_basis,
        x1,
        x2,
        x3,
        near_zero_by_phase["PHASE_2"],
    )
    dep_rows_3, collapsed_3 = detect_dependency_groups(
        exp_id,
        "PHASE_3",
        frozen_basis,
        x1,
        x2,
        x3,
        near_zero_by_phase["PHASE_3"],
    )

    p1_grad_p99 = float(np.percentile(np.array(phase_grad_samples["PHASE_1"], dtype=float), 99)) if phase_grad_samples["PHASE_1"] else 0.0
    spike_threshold = max(10.0, 10.0 * p1_grad_p99)

    spikes = {
        ph: int(sum(1 for g in phase_grad_samples[ph] if g > spike_threshold)) for ph in ["PHASE_1", "PHASE_2", "PHASE_3"]
    }

    unstable_phase = {}
    explosion_phase = {}
    for ph in ["PHASE_1", "PHASE_2", "PHASE_3"]:
        pexp = (
            (not math.isfinite(phase_param_abs_max[ph]))
            or phase_param_abs_max[ph] >= 1.0e3
        )
        explosion_phase[ph] = pexp

        ref_drift = phase_drift_abs_sum["PHASE_1"] / max(1, phase_update_count["PHASE_1"])
        cur_drift = phase_drift_abs_sum[ph] / max(1, phase_update_count[ph])
        unstable = pexp or (spikes[ph] > 0 and spikes[ph] >= max(25, int(0.02 * phase_update_count[ph]))) or (cur_drift > max(1e-9, 10.0 * ref_drift))
        unstable_phase[ph] = unstable

    status_1 = classify_phase_status(
        phase="PHASE_1",
        rank_deficiency=int(r1["rank_deficiency"]),
        condition_number=float(r1["condition_number"]),
        dependency_rows=[],
        near_zero_features=near_zero_by_phase["PHASE_1"],
        phase1_near_zero=near_zero_by_phase["PHASE_1"],
        unstable_phase=unstable_phase["PHASE_1"],
    )
    status_2 = classify_phase_status(
        phase="PHASE_2",
        rank_deficiency=int(r2["rank_deficiency"]),
        condition_number=float(r2["condition_number"]),
        dependency_rows=dep_rows_2,
        near_zero_features=near_zero_by_phase["PHASE_2"],
        phase1_near_zero=near_zero_by_phase["PHASE_1"],
        unstable_phase=unstable_phase["PHASE_2"],
    )
    status_3 = classify_phase_status(
        phase="PHASE_3",
        rank_deficiency=int(r3["rank_deficiency"]),
        condition_number=float(r3["condition_number"]),
        dependency_rows=dep_rows_3,
        near_zero_features=near_zero_by_phase["PHASE_3"],
        phase1_near_zero=near_zero_by_phase["PHASE_1"],
        unstable_phase=unstable_phase["PHASE_3"],
    )

    phase_failure_rows = [
        {
            "experiment_id": exp_id,
            "phase": "PHASE_1",
            "rows": int(r1["rows"]),
            "frozen_basis_columns": int(r1["columns"]),
            "matrix_rank": int(r1["matrix_rank"]),
            "rank_deficiency": int(r1["rank_deficiency"]),
            "condition_number": float(r1["condition_number"]),
            "smallest_singular_value": float(r1["smallest_singular_value"]),
            "largest_singular_value": float(r1["largest_singular_value"]),
            "status": status_1,
        },
        {
            "experiment_id": exp_id,
            "phase": "PHASE_2",
            "rows": int(r2["rows"]),
            "frozen_basis_columns": int(r2["columns"]),
            "matrix_rank": int(r2["matrix_rank"]),
            "rank_deficiency": int(r2["rank_deficiency"]),
            "condition_number": float(r2["condition_number"]),
            "smallest_singular_value": float(r2["smallest_singular_value"]),
            "largest_singular_value": float(r2["largest_singular_value"]),
            "status": status_2,
        },
        {
            "experiment_id": exp_id,
            "phase": "PHASE_3",
            "rows": int(r3["rows"]),
            "frozen_basis_columns": int(r3["columns"]),
            "matrix_rank": int(r3["matrix_rank"]),
            "rank_deficiency": int(r3["rank_deficiency"]),
            "condition_number": float(r3["condition_number"]),
            "smallest_singular_value": float(r3["smallest_singular_value"]),
            "largest_singular_value": float(r3["largest_singular_value"]),
            "status": status_3,
        },
    ]

    sv_delta_rows = []
    for phase, rp in [("PHASE_2", r2), ("PHASE_3", r3)]:
        rp1 = r1
        cols = int(rp["columns"])
        tol_p = rank_tolerance(x2 if phase == "PHASE_2" else x3)
        svs = np.linalg.svd(x2 if phase == "PHASE_2" else x3, compute_uv=False, full_matrices=False)
        collapsed = int(np.sum(svs <= tol_p))
        sv_delta_rows.append(
            {
                "experiment_id": exp_id,
                "transition": f"PHASE_1->{phase}",
                "phase1_smallest_singular_value": float(rp1["smallest_singular_value"]),
                "phaseN_smallest_singular_value": float(rp["smallest_singular_value"]),
                "phase1_largest_singular_value": float(rp1["largest_singular_value"]),
                "phaseN_largest_singular_value": float(rp["largest_singular_value"]),
                "phase1_condition_number": float(rp1["condition_number"]),
                "phaseN_condition_number": float(rp["condition_number"]),
                "phase1_rank": int(rp1["matrix_rank"]),
                "phaseN_rank": int(rp["matrix_rank"]),
                "rank_loss": int(rp1["matrix_rank"]) - int(rp["matrix_rank"]),
                "collapsed_singular_values_below_tolerance": collapsed,
                "phaseN_columns": cols,
            }
        )

    stab_rows = []
    for phase in ["PHASE_2", "PHASE_3"]:
        row_phase = phase_failure_rows[1] if phase == "PHASE_2" else phase_failure_rows[2]
        if row_phase["status"] != STATUS_PASS:
            stab_rows.append(
                {
                    "experiment_id": exp_id,
                    "phase": phase,
                    "status": row_phase["status"],
                    "max_parameter_magnitude": phase_param_abs_max[phase],
                    "max_gradient": phase_grad_abs_max[phase],
                    "total_drift": phase_drift_abs_sum[phase],
                    "update_spikes": spikes[phase],
                    "update_count": phase_update_count[phase],
                    "spike_threshold": spike_threshold,
                    "parameter_explosion": "YES" if explosion_phase[phase] else "NO",
                    "numerically_unstable": "YES" if unstable_phase[phase] else "NO",
                }
            )

    worker_manifest = {
        "experiment_id": exp_id,
        "frozen_basis_columns": len(frozen_basis),
        "basis_sha256": basis_manifest.get("basis_sha256", ""),
        "phase1_rank": int(r1["matrix_rank"]),
        "phase2_rank": int(r2["matrix_rank"]),
        "phase3_rank": int(r3["matrix_rank"]),
        "phase1_status": status_1,
        "phase2_status": status_2,
        "phase3_status": status_3,
        "phase2_collapsed_features": collapsed_2,
        "phase3_collapsed_features": collapsed_3,
        "non_finite_values": non_finite_values,
    }

    (wdir / "phase_failure_rows.json").write_text(json.dumps(phase_failure_rows, indent=2), encoding="utf-8")
    (wdir / "phase_feature_variance.json").write_text(json.dumps(vrows, indent=2), encoding="utf-8")
    (wdir / "phase_singular_value_deltas.json").write_text(json.dumps(sv_delta_rows, indent=2), encoding="utf-8")
    (wdir / "phase_degeneracy_dependencies.json").write_text(json.dumps(dep_rows_2 + dep_rows_3, indent=2), encoding="utf-8")
    (wdir / "phase_parameter_stability.json").write_text(json.dumps(stab_rows, indent=2), encoding="utf-8")
    (wdir / "worker_manifest.json").write_text(json.dumps(worker_manifest, indent=2, sort_keys=True), encoding="utf-8")

    progress_queue.put({"kind": "done", "experiment_id": exp_id})

    return {
        "experiment_id": exp_id,
        "phase_failure_rows": phase_failure_rows,
        "phase_feature_variance": vrows,
        "phase_singular_value_deltas": sv_delta_rows,
        "phase_degeneracy_dependencies": dep_rows_2 + dep_rows_3,
        "phase_degeneracy_parameter_stability": stab_rows,
        "worker_manifest": worker_manifest,
        "non_finite_values": non_finite_values,
        "parameter_explosion_cases": int(sum(1 for ph in ["PHASE_2", "PHASE_3"] if explosion_phase[ph])),
        "unstable_degeneracy_cases": int(sum(1 for ph in ["PHASE_2", "PHASE_3"] if unstable_phase[ph])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Final pre-001B structural resolution pass")
    parser.add_argument("--workers", type=int, default=18)
    parser.add_argument("--progress-every", type=int, default=5000)
    args = parser.parse_args()

    set_env_limits()
    ensure_dirs()

    if not STRUCT_PASS_ROOT.exists():
        raise RuntimeError("Missing structural dependency pass output")

    dataset_sha = sha256_file(DATASET_PATH)
    if dataset_sha != EXPECTED_SHA256:
        raise RuntimeError(f"Dataset hash mismatch: {dataset_sha}")

    basis_manifests = load_basis_manifests(STRUCT_PASS_ROOT)
    rows = load_rows(DATASET_PATH)

    default_cfg = load_yaml(ROOT / "config" / "default_v0_1_2.yaml")
    default_cfg["observation_capabilities"] = firstrate_ohlcv_capabilities("SPY").to_dict()
    matrix_cfg = load_yaml(ROOT / "config" / "experiment_matrix.yaml")
    experiments = list(matrix_cfg["experiments"])

    import multiprocessing as mp

    mgr = mp.Manager()
    q = mgr.Queue()

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    print(f"[{now_iso()}] Launching final precheck workers={args.workers}")

    with ProcessPoolExecutor(max_workers=int(args.workers)) as ex:
        futs = {
            ex.submit(
                worker_run,
                exp,
                default_cfg,
                rows,
                basis_manifests[str(exp["id"])],
                str(OUT_ROOT),
                int(args.progress_every),
                q,
            ): str(exp["id"])
            for exp in experiments
        }

        pending = set(futs.keys())
        while pending:
            done, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
            while not q.empty():
                m = q.get()
                if m.get("kind") == "progress":
                    print(
                        f"[{m['experiment_id']} PRECHECK] processed={m['processed']} phase={m['phase']} "
                        f"percent={m['percent']:.2f}"
                    )
                elif m.get("kind") == "done":
                    print(f"[{m['experiment_id']} PRECHECK] complete")

            for d in done:
                exp_id = futs[d]
                try:
                    results.append(d.result())
                except Exception as exc:
                    failures.append({"experiment_id": exp_id, "exception": str(exc)})
                    print(f"[FAIL] {exp_id}: {exc}")

    phase_failure_rows: list[dict[str, Any]] = []
    variance_rows: list[dict[str, Any]] = []
    sv_delta_rows: list[dict[str, Any]] = []
    dep_rows: list[dict[str, Any]] = []
    stab_rows: list[dict[str, Any]] = []

    non_finite_total = 0
    explosion_cases = 0
    unstable_cases = 0

    manifests_out = {}
    for r in sorted(results, key=lambda x: x["experiment_id"]):
        phase_failure_rows.extend(r["phase_failure_rows"])
        variance_rows.extend(r["phase_feature_variance"])
        sv_delta_rows.extend(r["phase_singular_value_deltas"])
        dep_rows.extend(r["phase_degeneracy_dependencies"])
        stab_rows.extend(r["phase_degeneracy_parameter_stability"])
        non_finite_total += int(r["non_finite_values"])
        explosion_cases += int(r["parameter_explosion_cases"])
        unstable_cases += int(r["unstable_degeneracy_cases"])
        manifests_out[r["experiment_id"]] = r["worker_manifest"]

    write_csv(
        OUT_ROOT / "metrics" / "phase_failure_matrix.csv",
        [
            "experiment_id",
            "phase",
            "rows",
            "frozen_basis_columns",
            "matrix_rank",
            "rank_deficiency",
            "condition_number",
            "smallest_singular_value",
            "largest_singular_value",
            "status",
        ],
        phase_failure_rows,
    )

    write_csv(
        OUT_ROOT / "metrics" / "phase_feature_variance.csv",
        [
            "experiment_id",
            "phase",
            "feature_name",
            "min",
            "max",
            "mean",
            "std",
            "variance",
            "unique_count",
            "zero_count",
            "near_zero_variance",
        ],
        variance_rows,
    )

    write_csv(
        OUT_ROOT / "diagnostics" / "phase_singular_value_deltas.csv",
        [
            "experiment_id",
            "transition",
            "phase1_smallest_singular_value",
            "phaseN_smallest_singular_value",
            "phase1_largest_singular_value",
            "phaseN_largest_singular_value",
            "phase1_condition_number",
            "phaseN_condition_number",
            "phase1_rank",
            "phaseN_rank",
            "rank_loss",
            "collapsed_singular_values_below_tolerance",
            "phaseN_columns",
        ],
        sv_delta_rows,
    )

    write_csv(
        OUT_ROOT / "diagnostics" / "phase_degeneracy_dependencies.csv",
        [
            "experiment_id",
            "phase",
            "dependency_group_id",
            "features_involved",
            "dependency_type",
            "exact_or_near",
            "rank_contribution",
            "evidence",
            "phase1_independent",
            "phase2_independent",
            "phase3_independent",
        ],
        dep_rows,
    )

    write_csv(
        OUT_ROOT / "metrics" / "phase_degeneracy_parameter_stability.csv",
        [
            "experiment_id",
            "phase",
            "status",
            "max_parameter_magnitude",
            "max_gradient",
            "total_drift",
            "update_spikes",
            "update_count",
            "spike_threshold",
            "parameter_explosion",
            "numerically_unstable",
        ],
        stab_rows,
    )

    by_exp_phase: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in phase_failure_rows:
        by_exp_phase[str(row["experiment_id"])][str(row["phase"])] = row

    phase2_structural_failures = 0
    phase3_structural_failures = 0
    phase2_local_cases = 0
    phase3_local_cases = 0
    structural_remaining = 0
    local_total = 0
    unresolved_count = 0
    severe_count = 0

    for row in phase_failure_rows:
        phase = str(row["phase"])
        status = str(row["status"])
        if phase == "PHASE_2" and status == STATUS_STRUCTURAL:
            phase2_structural_failures += 1
        if phase == "PHASE_3" and status == STATUS_STRUCTURAL:
            phase3_structural_failures += 1
        if phase == "PHASE_2" and status == STATUS_LOCAL:
            phase2_local_cases += 1
        if phase == "PHASE_3" and status == STATUS_LOCAL:
            phase3_local_cases += 1
        if status == STATUS_STRUCTURAL:
            structural_remaining += 1
        if status == STATUS_LOCAL:
            local_total += 1
        if status == STATUS_UNRESOLVED:
            unresolved_count += 1
        if status == STATUS_SEVERE:
            severe_count += 1

    phase1_structural_pass = all(
        by_exp_phase[e]["PHASE_1"]["matrix_rank"] == by_exp_phase[e]["PHASE_1"]["frozen_basis_columns"]
        and by_exp_phase[e]["PHASE_1"]["status"] == STATUS_PASS
        for e in sorted(by_exp_phase.keys())
    )

    non_finite_ok = non_finite_total == 0
    no_worker_failures = len(failures) == 0

    structural_basis_valid = phase1_structural_pass and structural_remaining == 0
    temporary_inactive_safe = "NOT APPLICABLE"
    if local_total > 0:
        temporary_inactive_safe = "YES" if unstable_cases == 0 and explosion_cases == 0 else "NO"

    # Revised gate decision.
    if unresolved_count > 0 or not no_worker_failures:
        final_decision = "NOT READY — UNRESOLVED"
    elif not structural_basis_valid:
        final_decision = "NOT READY — STRUCTURAL DEPENDENCIES REMAIN"
    elif not non_finite_ok or explosion_cases > 0 or unstable_cases > 0:
        final_decision = "NOT READY — PHASE-LOCAL DEGENERACY CAUSES NUMERICAL INSTABILITY"
    else:
        final_decision = "READY FOR EXP001B"

    # Reports.
    fail_md = ["# D01 v0.1.2 Phase Failure Matrix", ""]
    fail_md.append("|experiment_id|phase|rank|columns|condition_number|collapsed_features|dependency_group|classification|")
    fail_md.append("|---|---|---:|---:|---:|---|---|---|")

    dep_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for drow in dep_rows:
        dep_by_key[(str(drow["experiment_id"]), str(drow["phase"]))].append(drow)

    for exp in sorted(by_exp_phase.keys()):
        for phase in ["PHASE_2", "PHASE_3"]:
            row = by_exp_phase[exp][phase]
            if row["status"] == STATUS_PASS:
                continue
            dlist = dep_by_key.get((exp, phase), [])
            collapsed = sorted({n for d in dlist for n in str(d.get("features_involved", "")).split("|") if n})
            dgid = "|".join(d.get("dependency_group_id", "") for d in dlist) if dlist else ""
            fail_md.append(
                f"|{exp}|{phase}|{row['matrix_rank']}|{row['frozen_basis_columns']}|{row['condition_number']}|"
                f"{'|'.join(collapsed)}|{dgid}|{row['status']}|"
            )

    (OUT_ROOT / "reports" / "D01_V0_1_2_PHASE_FAILURE_MATRIX.md").write_text("\n".join(fail_md), encoding="utf-8")

    remediation_md = [
        "# D01 v0.1.2 Targeted Remediation Plan",
        "",
        "|Issue|Classification|Evidence|Correction required?|Exact correction|Core adaptive math affected?|Retest required?|",
        "|---|---|---|---|---|---|---|",
    ]

    for exp in sorted(by_exp_phase.keys()):
        for phase in ["PHASE_2", "PHASE_3"]:
            row = by_exp_phase[exp][phase]
            if row["status"] == STATUS_PASS:
                continue
            issue = f"{exp} {phase} rank={row['matrix_rank']}/{row['frozen_basis_columns']} cond={row['condition_number']}"
            classification = row["status"]
            evidence = f"rank_deficiency={row['rank_deficiency']}; smallest_sv={row['smallest_singular_value']}"

            if classification == STATUS_STRUCTURAL:
                corr_req = "YES"
                exact_corr = "Apply existing structural independence rules to remove exact structural dependency only."
            elif classification == STATUS_LOCAL:
                corr_req = "NO"
                exact_corr = "Keep frozen basis; mark temporarily inactive dimensions; track effective rank separately."
            elif classification == STATUS_SEVERE:
                corr_req = "YES"
                exact_corr = "Keep basis fixed; enforce numerical stability diagnostics and verify no parameter instability."
            else:
                corr_req = "YES"
                exact_corr = "Investigate unresolved dependency reconstruction and lineage evidence."

            remediation_md.append(
                f"|{issue}|{classification}|{evidence}|{corr_req}|{exact_corr}|NO|YES|"
            )

    (OUT_ROOT / "reports" / "D01_V0_1_2_TARGETED_REMEDIATION_PLAN.md").write_text("\n".join(remediation_md), encoding="utf-8")

    assessment = [
        "# D01 v0.1.2 Final Pre001B Basis Assessment",
        "",
        "1. Is the Phase-1 basis structurally independent? " + ("YES" if phase1_structural_pass else "NO"),
        "2. Are later rank losses structural or local? "
        + (
            "STRUCTURAL"
            if structural_remaining > 0
            else ("PHASE-LOCAL" if local_total > 0 else "NONE")
        ),
        "3. Are temporarily inactive dimensions numerically safe? " + temporary_inactive_safe,
        "4. Does any config remain structurally invalid? " + ("YES" if structural_remaining > 0 else "NO"),
        "5. Does any config remain numerically unstable? " + ("YES" if (unstable_cases > 0 or explosion_cases > 0) else "NO"),
        "6. Can EXP001B proceed? " + ("YES" if final_decision == "READY FOR EXP001B" else "NO"),
        "",
        "Gate notes:",
        "- Structural basis dimension is fixed from Phase 1 manifests.",
        "- Effective phase rank is computed per phase without resizing basis.",
        "- No predictive metrics were computed.",
        "- No reserve data used.",
        "",
        "Final decision: " + final_decision,
    ]
    (OUT_ROOT / "reports" / "D01_V0_1_2_FINAL_PRE001B_BASIS_ASSESSMENT.md").write_text("\n".join(assessment), encoding="utf-8")

    root_manifest = {
        "purpose": "DISTINGUISH_STRUCTURAL_DEPENDENCY_FROM_PHASE_LOCAL_DEGENERACY",
        "d01_version": "v0.1.2",
        "dataset": str(DATASET_PATH),
        "dataset_sha256": dataset_sha,
        "reserve_data_used": False,
        "predictive_metrics_calculated": False,
        "exp001b_started": False,
        "workers": int(args.workers),
        "configurations_audited": len(results),
        "worker_failures": failures,
        "non_finite_values": non_finite_total,
        "parameter_explosion_cases": explosion_cases,
        "unstable_degeneracy_cases": unstable_cases,
        "phase1_structural_pass": phase1_structural_pass,
        "structural_dependencies_remaining": structural_remaining,
        "phase_local_degeneracy_cases": local_total,
        "severe_ill_conditioning_cases": severe_count,
        "unresolved_cases": unresolved_count,
        "temporary_inactive_dimensions_safe": temporary_inactive_safe,
        "final_decision": final_decision,
        "created_at": now_iso(),
        "runtime_seconds": max(0.0, time.perf_counter() - t0),
    }

    (OUT_ROOT / "manifests" / "FINAL_PRE001B_PHASE_DEGENERACY_MANIFEST.json").write_text(
        json.dumps(root_manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    for exp_id, wm in manifests_out.items():
        (OUT_ROOT / "manifests" / f"{exp_id}_phase_degeneracy_manifest.json").write_text(
            json.dumps(wm, indent=2, sort_keys=True), encoding="utf-8"
        )

    (OUT_ROOT / "logs" / "worker_failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    # Console summary.
    print("APTF D01 v0.1.2 FINAL PRE-001B STRUCTURAL RESOLUTION COMPLETE")
    print("PURPOSE:")
    print("DISTINGUISH STRUCTURAL DEPENDENCY FROM PHASE-LOCAL DEGENERACY")
    print("D01 VERSION:")
    print("v0.1.2")
    print("CORE ADAPTIVE MATHEMATICS CHANGED:")
    print("NO")
    print("CONFIGURATIONS AUDITED:")
    print(f"{len(results)} / 15")
    print("MAX WORKERS:")
    print(str(args.workers))
    print("PARALLEL MODE:")
    print("PROCESS")
    print("PHASE-1 STRUCTURAL BASIS:")
    print("PASS" if phase1_structural_pass else "FAIL")
    print("PHASE-2 STRUCTURAL FAILURES:")
    print(str(phase2_structural_failures))
    print("PHASE-3 STRUCTURAL FAILURES:")
    print(str(phase3_structural_failures))
    print("PHASE-2 LOCAL DEGENERACY CASES:")
    print(str(phase2_local_cases))
    print("PHASE-3 LOCAL DEGENERACY CASES:")
    print(str(phase3_local_cases))
    print("TRUE STRUCTURAL DEPENDENCIES REMAINING:")
    print(str(structural_remaining))
    print("PHASE-LOCAL DEGENERACY CASES:")
    print(str(local_total))
    print("NUMERICALLY UNSTABLE DEGENERACY CASES:")
    print(str(unstable_cases))
    print("NON-FINITE VALUES:")
    print(str(non_finite_total))
    print("PARAMETER EXPLOSION CASES:")
    print(str(explosion_cases))

    for key in ["A_n1", "B_n1", "D_n2", "E_n3"]:
        r1 = by_exp_phase[key]["PHASE_1"]
        r2 = by_exp_phase[key]["PHASE_2"]
        r3 = by_exp_phase[key]["PHASE_3"]
        if r2["status"] == STATUS_STRUCTURAL or r3["status"] == STATUS_STRUCTURAL:
            cls = "STRUCTURAL"
        elif r2["status"] == STATUS_LOCAL or r3["status"] == STATUS_LOCAL:
            cls = "PHASE-LOCAL"
        elif r2["status"] == STATUS_PASS and r3["status"] == STATUS_PASS:
            cls = "PASS"
        else:
            cls = "UNRESOLVED"

        print(f"{key}:")
        print(f"structural_basis={r1['frozen_basis_columns']}")
        print(f"phase1_rank={r1['matrix_rank']}")
        print(f"phase2_effective_rank={r2['matrix_rank']}")
        print(f"phase3_effective_rank={r3['matrix_rank']}")
        print(f"classification={cls}")

    print("STRUCTURAL BASIS VALID:")
    print("YES" if structural_basis_valid else "NO")
    print("TEMPORARY INACTIVE DIMENSIONS SAFE:")
    print(temporary_inactive_safe)
    print("EXP001B:")
    print("NOT STARTED")
    print("PREDICTIVE METRICS:")
    print("NOT CALCULATED")
    print("RESERVE DATA:")
    print("NOT USED")
    print("PRIMARY REPORT:")
    print("output/historical_exp001b_precheck/phase_degeneracy_resolution/reports/D01_V0_1_2_FINAL_PRE001B_BASIS_ASSESSMENT.md")
    print("FAILURE MATRIX:")
    print("output/historical_exp001b_precheck/phase_degeneracy_resolution/reports/D01_V0_1_2_PHASE_FAILURE_MATRIX.md")
    print("REMEDIATION PLAN:")
    print("output/historical_exp001b_precheck/phase_degeneracy_resolution/reports/D01_V0_1_2_TARGETED_REMEDIATION_PLAN.md")
    print("FINAL DECISION:")
    print(final_decision)

    return 0 if final_decision == "READY FOR EXP001B" else 1


if __name__ == "__main__":
    raise SystemExit(main())

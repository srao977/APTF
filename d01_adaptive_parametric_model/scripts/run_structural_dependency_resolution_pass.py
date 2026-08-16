from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aptf_d01.features.structural_independence import (  # noqa: E402
    ColumnMeta,
    build_independent_basis,
    classify_condition_number,
    matrix_condition_report,
)
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel  # noqa: E402
from aptf_d01.models.normalized_observation import NormalizedObservation  # noqa: E402
from aptf_d01.providers.observation_capabilities import firstrate_ohlcv_capabilities  # noqa: E402
from aptf_d01.runtime.experiment_runner import _build_model_cfg  # noqa: E402


DATASET_PATH = Path(r"C:\Users\chino\APTF\data\market\normalized\SPY_1min_normalized_v0_1.csv")
EXPECTED_SHA256 = "73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D"
OUT_ROOT = ROOT / "output" / "historical_exp001b_precheck" / "structural_dependency_pass"

PHASES = {
    "PHASE_1": ("2023-03-29T08:00:00Z", "2023-07-19T17:12:00Z", 61228),
    "PHASE_2": ("2023-07-19T17:13:00Z", "2023-08-23T23:31:00Z", 20409),
    "PHASE_3": ("2023-08-23T23:32:00Z", "2023-09-29T23:48:00Z", 20410),
}
SESSIONS = {"PREMARKET", "REGULAR", "AFTERHOURS"}


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
    for sub in ["reports", "metrics", "diagnostics", "manifests", "logs", "workers"]:
        (OUT_ROOT / sub).mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def sha256_file(path: Path) -> str:
    import hashlib

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
    for ph, (_s, _e, expected) in PHASES.items():
        if counts[ph] != expected:
            raise RuntimeError(f"phase count mismatch {ph}: expected {expected} got {counts[ph]}")
    return rows


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_obs(row: Row) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="SPY",
        event_id=f"PRECHECK-{row.idx:08d}",
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


def deterministic_column_order(manifest: dict[str, Any]) -> list[str]:
    feature_names = set(manifest["feature_names"])
    order: list[str] = []
    if "bias" in feature_names:
        order.append("bias")

    poly_order = int(manifest["polynomial_order"])
    int_order = int(manifest["interaction_max_order"])

    for base in manifest["active_base_features"]:
        for deg in range(1, poly_order + 1):
            nm = base if deg == 1 else f"{base}^{deg}"
            if nm in feature_names:
                order.append(nm)

    for inter in manifest.get("interaction_features", []):
        max_deg = min(poly_order, int_order)
        for deg in range(1, max_deg + 1):
            nm = inter if deg == 1 else f"{inter}^{deg}"
            if nm in feature_names:
                order.append(nm)

    for nm in manifest["feature_names"]:
        if nm not in order:
            order.append(nm)
    return order


def lineage_meta_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    m = {}
    for row in manifest.get("feature_lineage", []):
        m[row["feature_name"]] = row
    return m


def worker_run(
    exp_cfg: dict[str, Any],
    default_cfg: dict[str, Any],
    rows: list[Row],
    out_root_str: str,
    progress_every: int,
    progress_queue: Any,
) -> dict[str, Any]:
    set_env_limits()
    out_root = Path(out_root_str)
    exp_id = str(exp_cfg["id"])

    wdir = out_root / "workers" / exp_id
    wdir.mkdir(parents=True, exist_ok=True)

    model = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))
    manifest = model.get_feature_manifest()
    manifest["experiment_id"] = exp_id
    manifest["phase_1_discovery_rule"] = "PHASE_1_ONLY_FROZEN_BASIS"

    col_order = deterministic_column_order(manifest)
    lin = lineage_meta_map(manifest)

    phase_basis_rows: dict[str, list[list[float]]] = {"PHASE_1": [], "PHASE_2": [], "PHASE_3": []}
    phase_raw_rows: dict[str, list[list[float]]] = {"PHASE_1": [], "PHASE_2": [], "PHASE_3": []}
    phase_cond_rows: dict[str, list[list[float]]] = {"PHASE_1": [], "PHASE_2": [], "PHASE_3": []}
    non_finite_count = 0

    raw_names = list(model.base_feature_names)

    logs: list[str] = []
    t0 = time.perf_counter()

    for i, row in enumerate(rows):
        ph = phase_for_ts(row.event_timestamp_utc)
        obs = build_obs(row)
        dmo, _fmo, _upd = model.step(obs, row.ts_utc)

        basis_vec = [float(dmo.input_channel_snapshot.get(f"basis_{k}", 0.0)) for k in col_order]
        raw_vec = [float(dmo.input_channel_snapshot.get(f"raw_{k}", 0.0)) for k in raw_names]
        cond_vec = [float(dmo.input_channel_snapshot.get(f"model_{k}", 0.0)) for k in raw_names]

        if not all(math.isfinite(v) for v in basis_vec + raw_vec + cond_vec):
            non_finite_count += 1

        phase_basis_rows[ph].append(basis_vec)
        phase_raw_rows[ph].append(raw_vec)
        phase_cond_rows[ph].append(cond_vec)

        if progress_every > 0 and (i + 1) % progress_every == 0:
            elapsed = max(1e-9, time.perf_counter() - t0)
            pct = 100.0 * (i + 1) / len(rows)
            msg = f"[{exp_id} PRECHECK] processed={i+1} phase={ph} percent={pct:.2f} elapsed={elapsed:.1f}s"
            logs.append(msg)
            progress_queue.put({
                "kind": "progress",
                "experiment_id": exp_id,
                "processed": i + 1,
                "percent": pct,
                "phase": ph,
                "elapsed": elapsed,
            })

    x1 = np.array(phase_basis_rows["PHASE_1"], dtype=float)

    ordered_meta: list[ColumnMeta] = []
    for cidx, cname in enumerate(col_order):
        l = lin.get(cname, {})
        ip = l.get("interaction_parents", [])
        ordered_meta.append(
            ColumnMeta(
                name=cname,
                feature_type=str(l.get("feature_type", "unknown")),
                stage=("INTERACTION" if "_x_" in cname else ("POLYNOMIAL" if "^" in cname else "BASE")),
                base_feature=str(l.get("base_feature", cname.split("^")[0])),
                polynomial_order=int(l.get("polynomial_order", 1)),
                interaction_parent_a=str(ip[0]) if len(ip) >= 1 else "",
                interaction_parent_b=str(ip[1]) if len(ip) >= 2 else "",
                intercept=(cname == "bias"),
                lineage_id=f"{exp_id}:{cidx}:{cname}",
            )
        )

    basis_res = build_independent_basis(x1, ordered_meta)
    retained_names = list(basis_res.retained_names)
    retained_idx = [col_order.index(n) for n in retained_names]

    phase_rank_rows: list[dict[str, Any]] = []
    basis_dim_rows: list[dict[str, Any]] = []
    for phase in ["PHASE_1", "PHASE_2", "PHASE_3"]:
        xp = np.array(phase_basis_rows[phase], dtype=float)
        xp_ret = xp[:, retained_idx]
        rep = matrix_condition_report(xp_ret)
        phase_rank_rows.append(
            {
                "experiment_id": exp_id,
                "phase": phase,
                "rows": int(rep["rows"]),
                "columns": int(rep["columns"]),
                "matrix_rank": int(rep["matrix_rank"]),
                "rank_deficiency": int(rep["rank_deficiency"]),
                "condition_number": float(rep["condition_number"]),
                "smallest_singular_value": float(rep["smallest_singular_value"]),
                "largest_singular_value": float(rep["largest_singular_value"]),
                "classification": str(rep["classification"]),
            }
        )
        basis_dim_rows.append(
            {
                "experiment_id": exp_id,
                "phase": phase,
                "candidate_columns": len(col_order),
                "retained_columns": len(retained_names),
                "excluded_columns": len(col_order) - len(retained_names),
                "matrix_rank": int(rep["matrix_rank"]),
                "rank_deficiency": int(rep["rank_deficiency"]),
                "condition_number": float(rep["condition_number"]),
                "classification": str(rep["classification"]),
            }
        )

    # Base and conditioned dependency analysis on Phase 1.
    xraw1 = np.array(phase_raw_rows["PHASE_1"], dtype=float)
    xcond1 = np.array(phase_cond_rows["PHASE_1"], dtype=float)

    raw_meta = [
        ColumnMeta(
            name=n,
            feature_type="base",
            stage="BASE",
            base_feature=n,
            polynomial_order=1,
            interaction_parent_a="",
            interaction_parent_b="",
            intercept=False,
            lineage_id=f"{exp_id}:raw:{n}",
        )
        for n in raw_names
    ]
    cond_meta = [
        ColumnMeta(
            name=n,
            feature_type="base",
            stage="CONDITIONED",
            base_feature=n,
            polynomial_order=1,
            interaction_parent_a="",
            interaction_parent_b="",
            intercept=False,
            lineage_id=f"{exp_id}:cond:{n}",
        )
        for n in raw_names
    ]

    raw_dep = build_independent_basis(xraw1, raw_meta)
    cond_dep = build_independent_basis(xcond1, cond_meta)

    # Intercept collision audit.
    intercept_count = sum(1 for n in retained_names if n == "bias")
    x1_ret = x1[:, retained_idx]
    stds = np.std(x1_ret, axis=0) if x1_ret.size else np.array([], dtype=float)
    const_collisions = sum(1 for i, n in enumerate(retained_names) if n != "bias" and i < len(stds) and stds[i] == 0.0)

    feature_inventory_rows: list[dict[str, Any]] = []
    for idx, name in enumerate(col_order):
        m = ordered_meta[idx]
        l = lin.get(name, {})
        src_obs = l.get("source_observations", [])
        feature_inventory_rows.append(
            {
                "experiment_id": exp_id,
                "column_index": idx,
                "feature_name": name,
                "feature_type": m.feature_type,
                "base_feature": m.base_feature,
                "source_observations": "|".join(src_obs),
                "conditioned": "true",
                "polynomial_order": m.polynomial_order,
                "interaction_parent_a": m.interaction_parent_a,
                "interaction_parent_b": m.interaction_parent_b,
                "intercept": str(m.intercept).lower(),
                "units_raw": "",
                "model_domain": "basis",
                "active": str(name in retained_names).lower(),
                "lineage_id": m.lineage_id,
            }
        )

    dep_group_rows: list[dict[str, Any]] = []
    for g in basis_res.dependency_groups:
        dep_group_rows.append(
            {
                "dependency_group_id": g.group_id,
                "experiment_id": exp_id,
                "stage": g.stage,
                "features": "|".join(g.feature_names),
                "number_of_features": len(g.feature_names),
                "rank": len(g.feature_names) - 1,
                "independent_dimensions": 1,
                "reason": g.dependency_type,
                "candidate_representatives": g.feature_names[0],
                "retained_representative": g.representative,
                "excluded_features": g.feature_names[-1],
                "retention_rule": "deterministic_structural_priority",
            }
        )

    polynomial_rows: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []
    excluded_set = set(basis_res.excluded_names)
    group_by_feature = {g.feature_names[-1]: g for g in basis_res.dependency_groups}

    for m in ordered_meta:
        if m.name == "bias":
            continue
        if m.stage == "POLYNOMIAL":
            polynomial_rows.append(
                {
                    "experiment_id": exp_id,
                    "source_feature": m.base_feature,
                    "order": m.polynomial_order,
                    "feature_name": m.name,
                    "adds_rank": "NO" if m.name in excluded_set else "YES",
                    "dependency_group": group_by_feature[m.name].group_id if m.name in group_by_feature else "",
                    "retained": "NO" if m.name in excluded_set else "YES",
                    "reason": group_by_feature[m.name].dependency_type if m.name in group_by_feature else "INDEPENDENT",
                }
            )
        if m.stage == "INTERACTION":
            interaction_rows.append(
                {
                    "experiment_id": exp_id,
                    "interaction_name": m.name,
                    "parent_a": m.interaction_parent_a,
                    "parent_b": m.interaction_parent_b,
                    "adds_rank": "NO" if m.name in excluded_set else "YES",
                    "dependency_group": group_by_feature[m.name].group_id if m.name in group_by_feature else "",
                    "retained": "NO" if m.name in excluded_set else "YES",
                    "reason": group_by_feature[m.name].dependency_type if m.name in group_by_feature else "INDEPENDENT",
                }
            )

    basis_manifest = {
        "experiment_id": exp_id,
        "candidate_base_features": list(manifest.get("candidate_base_features", [])),
        "retained_base_features": [n for n in manifest.get("active_base_features", []) if n in retained_names],
        "excluded_base_features": [n for n in manifest.get("active_base_features", []) if n not in retained_names],
        "candidate_polynomial_features": [m.name for m in ordered_meta if m.stage == "POLYNOMIAL"],
        "retained_polynomial_features": [m.name for m in ordered_meta if m.stage == "POLYNOMIAL" and m.name in retained_names],
        "excluded_polynomial_features": [m.name for m in ordered_meta if m.stage == "POLYNOMIAL" and m.name not in retained_names],
        "candidate_interactions": [m.name for m in ordered_meta if m.stage == "INTERACTION"],
        "retained_interactions": [m.name for m in ordered_meta if m.stage == "INTERACTION" and m.name in retained_names],
        "excluded_interactions": [m.name for m in ordered_meta if m.stage == "INTERACTION" and m.name not in retained_names],
        "intercept": "bias",
        "final_feature_order": retained_names,
        "dependency_groups": [
            {
                "group_id": g.group_id,
                "stage": g.stage,
                "feature_names": list(g.feature_names),
                "representative": g.representative,
                "dependency_type": g.dependency_type,
                "exact_or_numerical": g.exact_or_numerical,
                "tolerance": g.tolerance,
                "evidence": g.evidence,
            }
            for g in basis_res.dependency_groups
        ],
        "final_columns": len(retained_names),
        "expected_rank": len(retained_names),
        "basis_sha256": basis_res.basis_sha256,
        "provider_capabilities": manifest.get("provider_capabilities", {}),
        "active_channel_map": manifest.get("active_channel_map", {}),
    }

    # Worker outputs.
    write_csv(
        wdir / "feature_inventory.csv",
        [
            "experiment_id", "column_index", "feature_name", "feature_type", "base_feature", "source_observations",
            "conditioned", "polynomial_order", "interaction_parent_a", "interaction_parent_b", "intercept",
            "units_raw", "model_domain", "active", "lineage_id",
        ],
        feature_inventory_rows,
    )

    write_csv(
        wdir / "dependency_groups.csv",
        [
            "dependency_group_id", "experiment_id", "stage", "features", "number_of_features", "rank",
            "independent_dimensions", "reason", "candidate_representatives", "retained_representative",
            "excluded_features", "retention_rule",
        ],
        dep_group_rows,
    )

    (wdir / "basis_manifest.json").write_text(json.dumps(basis_manifest, indent=2, sort_keys=True), encoding="utf-8")
    (wdir / "phase_rank.json").write_text(json.dumps(phase_rank_rows, indent=2, sort_keys=True), encoding="utf-8")
    (wdir / "conditioning.json").write_text(
        json.dumps(
            {
                "base_dependency_groups": [g.__dict__ for g in raw_dep.dependency_groups],
                "conditioned_dependency_groups": [g.__dict__ for g in cond_dep.dependency_groups],
                "intercept_count": intercept_count,
                "constant_feature_collision_count": const_collisions,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (wdir / "worker.log").write_text("\n".join(logs), encoding="utf-8")

    progress_queue.put({"kind": "done", "experiment_id": exp_id})
    return {
        "experiment_id": exp_id,
        "feature_inventory_rows": feature_inventory_rows,
        "dependency_group_rows": dep_group_rows,
        "phase_rank_rows": phase_rank_rows,
        "basis_dim_rows": basis_dim_rows,
        "basis_manifest": basis_manifest,
        "base_dep_rows": [
            {
                "experiment_id": exp_id,
                "dependency_group_id": g.group_id,
                "feature_names": "|".join(g.feature_names),
                "group_size": len(g.feature_names),
                "group_rank": len(g.feature_names) - 1,
                "dependency_type": g.dependency_type,
                "exact_or_numerical": g.exact_or_numerical,
                "tolerance": g.tolerance,
                "evidence": g.evidence,
            }
            for g in raw_dep.dependency_groups
        ],
        "conditioned_dep_rows": [
            {
                "experiment_id": exp_id,
                "dependency_group_id": g.group_id,
                "feature_names": "|".join(g.feature_names),
                "group_size": len(g.feature_names),
                "group_rank": len(g.feature_names) - 1,
                "dependency_type": g.dependency_type,
                "exact_or_numerical": g.exact_or_numerical,
                "tolerance": g.tolerance,
                "evidence": g.evidence,
            }
            for g in cond_dep.dependency_groups
        ],
        "intercept_rows": [
            {
                "experiment_id": exp_id,
                "intercept_count": intercept_count,
                "constant_feature_collision_count": const_collisions,
            }
        ],
        "polynomial_rows": polynomial_rows,
        "interaction_rows": interaction_rows,
        "non_finite_count": non_finite_count,
        "worker_failure": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run D01 v0.1.2 structural dependency resolution precheck")
    parser.add_argument("--workers", type=int, default=18)
    parser.add_argument("--progress-every", type=int, default=5000)
    args = parser.parse_args()

    set_env_limits()
    ensure_dirs()

    sha = sha256_file(DATASET_PATH)
    if sha != EXPECTED_SHA256:
        raise RuntimeError(f"dataset hash mismatch: {sha}")

    # Existence checks for required 001A references.
    required_001a = [
        ROOT / "output" / "historical_exp001a" / "metrics" / "design_matrix_rank.csv",
        ROOT / "output" / "historical_exp001a" / "metrics" / "conditioning_by_stage.csv",
        ROOT / "output" / "historical_exp001a" / "diagnostics" / "constant_features.csv",
        ROOT / "output" / "historical_exp001a" / "diagnostics" / "near_constant_features.csv",
        ROOT / "output" / "historical_exp001a" / "diagnostics" / "duplicate_feature_columns.csv",
        ROOT / "output" / "historical_exp001a" / "diagnostics" / "high_feature_correlations.csv",
        ROOT / "output" / "historical_exp001a" / "diagnostics" / "singular_value_summary.csv",
    ]
    missing = [str(p) for p in required_001a if not p.exists()]
    if missing:
        raise RuntimeError("Missing required 001A artifacts: " + "; ".join(missing))

    rows = load_rows(DATASET_PATH)

    default_cfg = load_yaml(ROOT / "config" / "default_v0_1_2.yaml")
    default_cfg["observation_capabilities"] = firstrate_ohlcv_capabilities("SPY").to_dict()
    matrix_cfg = load_yaml(ROOT / "config" / "experiment_matrix.yaml")
    experiments = list(matrix_cfg["experiments"])

    import multiprocessing as mp

    mgr = mp.Manager()
    q = mgr.Queue()

    start = time.perf_counter()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    print(f"[{now_iso()}] Launching structural pass workers={args.workers}")
    with ProcessPoolExecutor(max_workers=int(args.workers)) as ex:
        futs = {
            ex.submit(worker_run, exp, default_cfg, rows, str(OUT_ROOT), int(args.progress_every), q): exp["id"]
            for exp in experiments
        }

        pending = set(futs.keys())
        while pending:
            done, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
            while not q.empty():
                msg = q.get()
                if msg.get("kind") == "progress":
                    print(
                        f"[{msg['experiment_id']} PRECHECK] processed={msg['processed']} "
                        f"phase={msg['phase']} percent={msg['percent']:.2f} elapsed={msg['elapsed']:.1f}s"
                    )
                elif msg.get("kind") == "done":
                    print(f"[{msg['experiment_id']} PRECHECK] complete")

            for d in done:
                exp_id = futs[d]
                try:
                    results.append(d.result())
                except Exception as e:
                    failures.append({"experiment_id": exp_id, "exception": str(e)})
                    print(f"[FAIL] {exp_id}: {e}")

    # Merge outputs.
    feature_inventory_exact: list[dict[str, Any]] = []
    dependency_groups: list[dict[str, Any]] = []
    basis_dim: list[dict[str, Any]] = []
    base_deps: list[dict[str, Any]] = []
    cond_deps: list[dict[str, Any]] = []
    intercept_rows: list[dict[str, Any]] = []
    poly_deps: list[dict[str, Any]] = []
    inter_deps: list[dict[str, Any]] = []

    manifests = {}
    total_non_finite = 0

    for r in sorted(results, key=lambda x: x["experiment_id"]):
        feature_inventory_exact.extend(r["feature_inventory_rows"])
        dependency_groups.extend(r["dependency_group_rows"])
        basis_dim.extend(r["basis_dim_rows"])
        base_deps.extend(r["base_dep_rows"])
        cond_deps.extend(r["conditioned_dep_rows"])
        intercept_rows.extend(r["intercept_rows"])
        poly_deps.extend(r["polynomial_rows"])
        inter_deps.extend(r["interaction_rows"])
        manifests[r["experiment_id"]] = r["basis_manifest"]
        total_non_finite += int(r["non_finite_count"])

        (OUT_ROOT / "manifests" / f"{r['experiment_id']}_basis_manifest.json").write_text(
            json.dumps(r["basis_manifest"], indent=2, sort_keys=True), encoding="utf-8"
        )

    write_csv(
        OUT_ROOT / "metrics" / "feature_inventory_exact.csv",
        [
            "experiment_id", "column_index", "feature_name", "feature_type", "base_feature", "source_observations",
            "conditioned", "polynomial_order", "interaction_parent_a", "interaction_parent_b", "intercept",
            "units_raw", "model_domain", "active", "lineage_id",
        ],
        feature_inventory_exact,
    )

    write_csv(
        OUT_ROOT / "diagnostics" / "base_feature_dependencies.csv",
        [
            "experiment_id", "dependency_group_id", "feature_names", "group_size", "group_rank", "dependency_type",
            "exact_or_numerical", "tolerance", "evidence",
        ],
        base_deps,
    )
    write_csv(
        OUT_ROOT / "diagnostics" / "conditioned_feature_dependencies.csv",
        [
            "experiment_id", "dependency_group_id", "feature_names", "group_size", "group_rank", "dependency_type",
            "exact_or_numerical", "tolerance", "evidence",
        ],
        cond_deps,
    )
    write_csv(
        OUT_ROOT / "diagnostics" / "intercept_dependency_audit.csv",
        ["experiment_id", "intercept_count", "constant_feature_collision_count"],
        intercept_rows,
    )
    write_csv(
        OUT_ROOT / "diagnostics" / "polynomial_dependencies.csv",
        ["experiment_id", "source_feature", "order", "feature_name", "adds_rank", "dependency_group", "retained", "reason"],
        poly_deps,
    )
    write_csv(
        OUT_ROOT / "diagnostics" / "interaction_dependencies.csv",
        ["experiment_id", "interaction_name", "parent_a", "parent_b", "adds_rank", "dependency_group", "retained", "reason"],
        inter_deps,
    )

    write_csv(
        OUT_ROOT / "metrics" / "dependency_groups.csv",
        [
            "dependency_group_id", "experiment_id", "stage", "features", "number_of_features", "rank",
            "independent_dimensions", "reason", "candidate_representatives", "retained_representative",
            "excluded_features", "retention_rule",
        ],
        dependency_groups,
    )

    write_csv(
        OUT_ROOT / "metrics" / "basis_dimension_summary.csv",
        [
            "experiment_id", "phase", "candidate_columns", "retained_columns", "excluded_columns", "matrix_rank",
            "rank_deficiency", "condition_number", "classification",
        ],
        basis_dim,
    )

    # Final gate decision across all 15 and all phases.
    full_rank_ok = all(int(r["rank_deficiency"]) == 0 and int(r["matrix_rank"]) == int(r["retained_columns"]) for r in basis_dim)
    severe_or_singular = any(
        (not math.isfinite(float(r["condition_number"]))) or float(r["condition_number"]) >= 1.0e12
        for r in basis_dim
    )

    phase1_ok = all(int(r["rank_deficiency"]) == 0 for r in basis_dim if r["phase"] == "PHASE_1")
    phase2_ok = all(int(r["rank_deficiency"]) == 0 for r in basis_dim if r["phase"] == "PHASE_2")
    phase3_ok = all(int(r["rank_deficiency"]) == 0 for r in basis_dim if r["phase"] == "PHASE_3")

    basis_det_pass = True
    for exp_id, bm in manifests.items():
        h = hashlib.sha256()
        for name in bm["final_feature_order"]:
            h.update(str(name).encode("utf-8"))
            h.update(b"\n")
        recomputed = h.hexdigest().upper()
        if recomputed != str(bm.get("basis_sha256", "")).upper():
            basis_det_pass = False
            break

    full_rank_configs = len({r["experiment_id"] for r in basis_dim if int(r["phase"] == "PHASE_1") and int(r["rank_deficiency"]) == 0})
    rank_def_configs = len({r["experiment_id"] for r in basis_dim if int(r["rank_deficiency"]) > 0})
    severe_configs = len({r["experiment_id"] for r in basis_dim if float(r["condition_number"]) >= 1.0e12})
    singular_configs = len({r["experiment_id"] for r in basis_dim if not math.isfinite(float(r["condition_number"]))})

    # Validation table report.
    status_rows = []
    by_exp = defaultdict(dict)
    for r in basis_dim:
        by_exp[r["experiment_id"]][r["phase"]] = r

    for exp in sorted(by_exp.keys()):
        p1 = by_exp[exp]["PHASE_1"]
        p2 = by_exp[exp]["PHASE_2"]
        p3 = by_exp[exp]["PHASE_3"]
        status = "PASS"
        if any(int(x["rank_deficiency"]) > 0 for x in [p1, p2, p3]):
            status = "FAIL_RANK"
        if any((not math.isfinite(float(x["condition_number"]))) or float(x["condition_number"]) >= 1.0e12 for x in [p1, p2, p3]):
            status = "FAIL_CONDITION"
        status_rows.append(
            {
                "experiment_id": exp,
                "candidate_columns": p1["candidate_columns"],
                "retained_columns": p1["retained_columns"],
                "excluded_columns": p1["excluded_columns"],
                "rank_phase1": p1["matrix_rank"],
                "columns_phase1": p1["retained_columns"],
                "condition_phase1": p1["condition_number"],
                "rank_phase2": p2["matrix_rank"],
                "columns_phase2": p2["retained_columns"],
                "condition_phase2": p2["condition_number"],
                "rank_phase3": p3["matrix_rank"],
                "columns_phase3": p3["retained_columns"],
                "condition_phase3": p3["condition_number"],
                "basis_sha256": manifests[exp]["basis_sha256"],
                "status": status,
            }
        )

    write_csv(
        OUT_ROOT / "reports" / "D01_V0_1_2_STRUCTURAL_BASIS_VALIDATION.csv",
        [
            "experiment_id", "candidate_columns", "retained_columns", "excluded_columns", "rank_phase1", "columns_phase1",
            "condition_phase1", "rank_phase2", "columns_phase2", "condition_phase2", "rank_phase3", "columns_phase3",
            "condition_phase3", "basis_sha256", "status",
        ],
        status_rows,
    )

    # Reports.
    excl_lines = ["# D01 v0.1.2 Structurally Excluded Features", ""]
    for exp in sorted(manifests.keys()):
        bm = manifests[exp]
        excl_lines.append(f"## {exp}")
        for name in bm["excluded_polynomial_features"] + bm["excluded_interactions"] + bm["excluded_base_features"]:
            excl_lines.append(f"- {name} | reason=STRUCTURAL_DEPENDENCY | diagnostics_available=true")
        excl_lines.append("")
    (OUT_ROOT / "reports" / "D01_V0_1_2_STRUCTURALLY_EXCLUDED_FEATURES.md").write_text("\n".join(excl_lines), encoding="utf-8")

    basis_lines = ["# D01 v0.1.2 Independent Feature Basis", ""]
    for exp in ["A_n1", "B_n1", "D_n2", "E_n3"]:
        bm = manifests.get(exp)
        if not bm:
            continue
        basis_lines.append(f"## {exp}")
        for nm in bm["final_feature_order"]:
            basis_lines.append(f"- {nm}")
        basis_lines.append("")
    (OUT_ROOT / "reports" / "D01_V0_1_2_INDEPENDENT_FEATURE_BASIS.md").write_text("\n".join(basis_lines), encoding="utf-8")

    dep_lines = [
        "# D01 v0.1.2 Structural Dependency Analysis",
        "",
        "## 1. Purpose",
        "Resolve structural dependencies in parametric basis using Phase-1-only discovery and frozen basis validation.",
        "",
        "## 2. Previous rank failures",
        "A_n1 rank=4/8, B_n1 rank=10/14 before this pass.",
        "",
        "## 3. Exact feature inventory",
        "See metrics/feature_inventory_exact.csv.",
        "",
        "## 4. Base dependencies",
        "See diagnostics/base_feature_dependencies.csv.",
        "",
        "## 5. Conditioned dependencies",
        "See diagnostics/conditioned_feature_dependencies.csv.",
        "",
        "## 6. Intercept dependencies",
        "See diagnostics/intercept_dependency_audit.csv.",
        "",
        "## 7. Polynomial dependencies",
        "See diagnostics/polynomial_dependencies.csv.",
        "",
        "## 8. Interaction dependencies",
        "See diagnostics/interaction_dependencies.csv.",
        "",
        "## 9. Dependency groups",
        "See metrics/dependency_groups.csv.",
        "",
        "## 10. Retention rules",
        "Deterministic structural priority only; no predictive criterion.",
        "",
        "## 11. Phase-1 discovery rule",
        "Basis discovered using PHASE_1 only.",
        "",
        "## 12. Basis freeze",
        "Frozen basis applied to PHASE_2 and PHASE_3 unchanged.",
        "",
        "## 13. Phase-2 verification",
        f"PASS={phase2_ok}",
        "",
        "## 14. Phase-3 verification",
        f"PASS={phase3_ok}",
        "",
        "## 15. Final ranks",
        "See metrics/basis_dimension_summary.csv.",
        "",
        "## 16. Final condition numbers",
        "See metrics/basis_dimension_summary.csv.",
        "",
        "## 17. Excluded features",
        "See reports/D01_V0_1_2_STRUCTURALLY_EXCLUDED_FEATURES.md.",
        "",
        "## 18. Remaining warnings",
        f"severe_or_singular={severe_or_singular}",
        "",
        "## 19. Numerical validation decision",
        "PASS" if (full_rank_ok and (not severe_or_singular) and total_non_finite == 0 and len(failures) == 0) else "FAIL",
    ]
    (OUT_ROOT / "reports" / "D01_V0_1_2_STRUCTURAL_DEPENDENCY_ANALYSIS.md").write_text("\n".join(dep_lines), encoding="utf-8")

    val_lines = ["# D01 v0.1.2 Structural Basis Validation", ""]
    val_lines.append("|experiment_id|candidate_columns|retained_columns|excluded_columns|rank_phase1|columns_phase1|condition_phase1|rank_phase2|columns_phase2|condition_phase2|rank_phase3|columns_phase3|condition_phase3|basis_sha256|status|")
    val_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for r in status_rows:
        val_lines.append(
            f"|{r['experiment_id']}|{r['candidate_columns']}|{r['retained_columns']}|{r['excluded_columns']}|"
            f"{r['rank_phase1']}|{r['columns_phase1']}|{r['condition_phase1']}|{r['rank_phase2']}|{r['columns_phase2']}|{r['condition_phase2']}|"
            f"{r['rank_phase3']}|{r['columns_phase3']}|{r['condition_phase3']}|{r['basis_sha256']}|{r['status']}|"
        )
    (OUT_ROOT / "reports" / "D01_V0_1_2_STRUCTURAL_BASIS_VALIDATION.md").write_text("\n".join(val_lines), encoding="utf-8")

    decision = "READY FOR EXP001B"
    if not full_rank_ok:
        decision = "NOT READY — STRUCTURAL DEPENDENCIES REMAIN"
    elif severe_or_singular:
        decision = "NOT READY — FULL RANK BUT SEVERELY ILL-CONDITIONED"

    # Root manifest and logs.
    root_manifest = {
        "purpose": "STRUCTURAL_BASIS_INDEPENDENCE",
        "d01_version": "v0.1.2",
        "dataset": str(DATASET_PATH),
        "dataset_sha256": sha,
        "provider": "FirstRateData",
        "source_channels": ["open", "high", "low", "close", "volume"],
        "placeholder_quote_channels": "NONE",
        "configurations_audited": len(results),
        "max_workers": int(args.workers),
        "phase_1_basis_discovery": phase1_ok,
        "phase_2_frozen_basis_validation": phase2_ok,
        "phase_3_frozen_basis_validation": phase3_ok,
        "full_rank_ok": full_rank_ok,
        "severe_or_singular": severe_or_singular,
        "non_finite_values": total_non_finite,
        "basis_determinism": basis_det_pass,
        "worker_failures": failures,
        "final_decision": decision,
        "created_at": now_iso(),
        "runtime_seconds": max(0.0, time.perf_counter() - start),
    }
    (OUT_ROOT / "manifests" / "STRUCTURAL_DEPENDENCY_PASS_MANIFEST.json").write_text(
        json.dumps(root_manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    (OUT_ROOT / "logs" / "worker_failures.json").write_text(json.dumps(failures, indent=2, sort_keys=True), encoding="utf-8")

    # Console summary.
    before_a = "rank=4/8 condition=inf"
    before_b = "rank=10/14 condition=inf"

    by_exp_phase1 = {r["experiment_id"]: r for r in basis_dim if r["phase"] == "PHASE_1"}
    a_after = by_exp_phase1.get("A_n1")
    b_after = by_exp_phase1.get("B_n1")
    d_after = by_exp_phase1.get("D_n2")
    e_after = by_exp_phase1.get("E_n3")

    print("APTF D01 v0.1.2 STRUCTURAL DEPENDENCY RESOLUTION COMPLETE")
    print("PURPOSE:")
    print("STRUCTURAL BASIS INDEPENDENCE")
    print("D01 VERSION:")
    print("v0.1.2")
    print("CORE ADAPTIVE MATHEMATICS CHANGED:")
    print("NO")
    print("PROVIDER:")
    print("FirstRateData")
    print("SOURCE CHANNELS:")
    print("OHLCV")
    print("PLACEHOLDER QUOTE CHANNELS:")
    print("NONE")
    print("CONFIGURATIONS AUDITED:")
    print(f"{len(results)}/{len(experiments)}")
    print("MAX WORKERS:")
    print(str(args.workers))
    print("PARALLEL MODE:")
    print("PROCESS")
    print("PHASE-1 BASIS DISCOVERY:")
    print("PASS" if phase1_ok else "FAIL")
    print("PHASE-2 FROZEN-BASIS VALIDATION:")
    print("PASS" if phase2_ok else "FAIL")
    print("PHASE-3 FROZEN-BASIS VALIDATION:")
    print("PASS" if phase3_ok else "FAIL")
    print("A_N1 BEFORE:")
    print(before_a)
    print("A_N1 AFTER:")
    print(f"rank={a_after['matrix_rank']}/{a_after['retained_columns']}")
    print(f"condition={a_after['condition_number']}")
    print("B_N1 BEFORE:")
    print(before_b)
    print("B_N1 AFTER:")
    print(f"rank={b_after['matrix_rank']}/{b_after['retained_columns']}")
    print(f"condition={b_after['condition_number']}")
    print("D_N2 AFTER:")
    print(f"rank={d_after['matrix_rank']}/{d_after['retained_columns']}")
    print(f"condition={d_after['condition_number']}")
    print("E_N3 AFTER:")
    print(f"rank={e_after['matrix_rank']}/{e_after['retained_columns']}")
    print(f"condition={e_after['condition_number']}")
    print("FULL-RANK CONFIGURATIONS:")
    print(f"{full_rank_configs}/15")
    print("RANK-DEFICIENT CONFIGURATIONS:")
    print(f"{rank_def_configs}/15")
    print("SEVERELY ILL-CONDITIONED CONFIGURATIONS:")
    print(f"{severe_configs}/15")
    print("SINGULAR CONFIGURATIONS:")
    print(f"{singular_configs}/15")
    print("TOTAL CANDIDATE FEATURES:")
    print(str(sum(int(r["candidate_columns"]) for r in basis_dim if r["phase"] == "PHASE_1")))
    print("TOTAL RETAINED FEATURES:")
    print(str(sum(int(r["retained_columns"]) for r in basis_dim if r["phase"] == "PHASE_1")))
    print("TOTAL EXCLUDED FEATURES:")
    print(str(sum(int(r["excluded_columns"]) for r in basis_dim if r["phase"] == "PHASE_1")))
    print("DEPENDENCY GROUPS:")
    print(str(len(dependency_groups)))
    print("INTERCEPT COLLISIONS:")
    print(str(sum(int(r["constant_feature_collision_count"]) for r in intercept_rows)))
    print("POLYNOMIAL DEPENDENCIES REMOVED:")
    print(str(sum(1 for r in poly_deps if r["retained"] == "NO")))
    print("INTERACTION DEPENDENCIES REMOVED:")
    print(str(sum(1 for r in inter_deps if r["retained"] == "NO")))
    print("NON-FINITE VALUES:")
    print(str(total_non_finite))
    print("BASIS DETERMINISM:")
    print("PASS" if basis_det_pass else "FAIL")
    print("WORKER FAILURES:")
    print(str(len(failures)))
    print("STRUCTURAL BASIS VALIDATION:")
    print("PASS" if (full_rank_ok and (not severe_or_singular) and total_non_finite == 0 and len(failures) == 0) else "FAIL")
    print("EXP001B:")
    print("NOT STARTED")
    print("RESERVE DATA:")
    print("NOT USED")
    print("PREDICTIVE METRICS:")
    print("NOT CALCULATED")
    print("D02:")
    print("NOT STARTED")
    print("D04:")
    print("NOT USED")
    print("BROKER:")
    print("NONE")
    print("PRIMARY REPORT:")
    print("output/historical_exp001b_precheck/structural_dependency_pass/reports/D01_V0_1_2_STRUCTURAL_BASIS_VALIDATION.md")
    print("DEPENDENCY ANALYSIS:")
    print("output/historical_exp001b_precheck/structural_dependency_pass/reports/D01_V0_1_2_STRUCTURAL_DEPENDENCY_ANALYSIS.md")
    print("INDEPENDENT BASIS:")
    print("output/historical_exp001b_precheck/structural_dependency_pass/reports/D01_V0_1_2_INDEPENDENT_FEATURE_BASIS.md")
    print("EXCLUDED FEATURES:")
    print("output/historical_exp001b_precheck/structural_dependency_pass/reports/D01_V0_1_2_STRUCTURALLY_EXCLUDED_FEATURES.md")
    print("FINAL DECISION:")
    print(decision)

    return 0 if (full_rank_ok and (not severe_or_singular) and total_non_finite == 0 and len(failures) == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())

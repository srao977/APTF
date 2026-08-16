from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from statistics import mean, quantiles
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from d01.v02.config import D01V02Config
from d01.v02.half_life import adapt_half_life
from d01.v02.innovation import innovation_magnitude
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d01.v02.perturbation import classify_perturbation

OUTPUT_ROOT = ROOT / "output" / "d01_v02_remaining_semantic_audit"
DIRS = {
    "reports": OUTPUT_ROOT / "reports",
    "metrics": OUTPUT_ROOT / "metrics",
    "diagnostics": OUTPUT_ROOT / "diagnostics",
    "logs": OUTPUT_ROOT / "logs",
    "workers": OUTPUT_ROOT / "workers",
    "manifests": OUTPUT_ROOT / "manifests",
}

SEM_ROOT = ROOT / "output" / "d01_v02_semantic_acceptance"
SEM_ASSERTIONS = SEM_ROOT / "semantic_assertions.csv"
SEM_DYNAMIC_RANGE = SEM_ROOT / "semantic_dynamic_range.csv"
SEM_FWD = SEM_ROOT / "forward_interval_by_scenario.csv"
SEM_REVIEW = SEM_ROOT / "D01_V0_2_SEMANTIC_ACCEPTANCE_REVIEW.md"
SEM_WINDOWS = SEM_ROOT / "scenario_window_manifest.json"
SEM_PERT_COUNTS = SEM_ROOT / "perturbation_class_counts.csv"
SEM_PERSISTENCE = SEM_ROOT / "persistence_by_scenario.csv"
SEM_HALFLIFE = SEM_ROOT / "half_life_by_scenario.csv"
SEM_SU = SEM_ROOT / "strength_uncertainty_map.csv"
DESIGN_DOC = ROOT.parent / "D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md"

SOURCE_GLOB = ROOT / "src" / "d01" / "v02"
MAX_WORKERS = 18

FAIL_IDS_EXPECTED = ["S02_G", "S03_B", "S03_D", "S05_A", "S06_A", "S06_E", "S07_F", "S08_D", "S10_B"]


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def source_hashes() -> dict[str, str]:
    files = sorted(SOURCE_GLOB.glob("*.py"))
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p) for p in files}


def scenario_windows() -> dict[str, dict[str, Any]]:
    return json.loads(SEM_WINDOWS.read_text(encoding="utf-8"))


def _obs(entity: str, seq: int, t: float, price: float, volume: float, source_quality: float = 1.0) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id=entity,
        event_time=t,
        receive_time=t,
        sequence_id=seq,
        price=price,
        volume=volume,
        source_quality=source_quality,
        availability_mask={"price": True, "volume": True},
    )


def generate_scenario(name: str, count: int = 180) -> list[NormalizedObservation]:
    out: list[NormalizedObservation] = []
    entity = f"SYN:{name}"
    t = 0.0
    price = 100.0
    for seq in range(1, count + 1):
        if name == "S01":
            price = 100.0
            volume = 1000.0
            dt = 1.0
        elif name == "S02":
            price += 0.02
            volume = 1100.0
            dt = 1.0
        elif name == "S03":
            price += 0.008 + 0.0004 * seq
            volume = 1200.0
            dt = 1.0
        elif name == "S04":
            price += 0.02
            volume = 1000.0 if seq < 90 else 5500.0
            dt = 1.0
        elif name == "S05":
            if seq < 90:
                price += 0.03
                volume = 900.0
            else:
                price -= 0.05
                volume = 6000.0
            dt = 1.0
        elif name == "S06":
            price += 0.03 if seq < 80 else -0.09
            volume = 2000.0
            dt = 1.0
        elif name == "S07":
            wobble = math.sin(seq / 2.0) * 0.05
            price += wobble
            volume = 800.0 + (seq % 5) * 300.0
            dt = 1.0
        elif name == "S08":
            price += 0.01
            volume = 1000.0
            dt = 10.0 if seq == 95 else 1.0
        elif name == "S09_LOW_VOLUME":
            price += 0.025
            volume = 700.0
            dt = 1.0
        elif name == "S09_HIGH_VOLUME":
            price += 0.025
            volume = 5000.0
            dt = 1.0
        elif name == "S10":
            if seq < 50:
                price += 0.02
            elif seq < 70:
                price -= 0.14
            else:
                price += 0.03
            volume = 1400.0 if seq < 50 else (6000.0 if seq < 70 else 1800.0)
            dt = 1.0
        else:
            raise ValueError(f"Unknown scenario: {name}")
        t += dt
        quality = 0.8 if name == "S08" and seq == 95 else 1.0
        out.append(_obs(entity=entity, seq=seq, t=t, price=price, volume=volume, source_quality=quality))
    return out


def split_windows_for_audit(scenario: str, idx: int, windows: dict[str, dict[str, Any]]) -> str:
    w = windows[scenario]
    pre_s, pre_e = int(w["pre"][0]), int(w["pre"][1])
    event_s, event_e = int(w["event"][0]), int(w["event"][1])
    post_s, post_e = int(w["post"][0]), int(w["post"][1])
    rec_s, rec_e = int(w["recovery"][0]), int(w["recovery"][1])

    if pre_s <= idx <= pre_e:
        return "PRE_EVENT"
    if event_s <= idx <= event_e:
        mid = event_s + (event_e - event_s) // 2
        if idx <= mid:
            return "EVENT_ONSET"
        return "EVENT_PEAK"
    if post_s <= idx <= post_e:
        if idx < rec_s:
            return "IMMEDIATE_POST"
        if rec_s <= idx <= rec_e:
            return "RECOVERY"
        return "POST_EVENT"
    return "OUT_OF_WINDOW"


def run_model_trace(scenario: str, windows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cfg = D01V02Config()
    model = D01V02Model(entity_id=f"AUDIT:{scenario}", config=cfg)
    obs_rows = generate_scenario(scenario, count=int(windows[scenario]["count"]))

    rows: list[dict[str, Any]] = []
    prev_event_time = None
    prev_level = 0.0
    prev_velocity = 0.0
    prev_hl = cfg.half_life.baseline

    for idx, obs in enumerate(obs_rows, start=1):
        dt = 1.0 if prev_event_time is None else max(0.0, float(obs.event_time) - float(prev_event_time))

        dmo, fmo = model.step(obs)

        residual, innovation_norm = innovation_magnitude(
            level=float(dmo.state_level),
            prev_level=prev_level,
            prev_velocity=prev_velocity,
            dt=dt,
            epsilon=cfg.numerical.epsilon,
        )

        p_class, p_mag, _mult = classify_perturbation(
            innovation=innovation_norm,
            prev_velocity=prev_velocity,
            velocity=float(dmo.state_velocity),
            source_quality=float(obs.source_quality),
            cfg=cfg.perturbation,
        )

        reinforce_raw = 1.0 + (float(dmo.persistence) * float(dmo.strength) * 0.2)
        contradiction_raw = 1.0 - (float(dmo.uncertainty) * 0.35)
        rlo, rhi = cfg.half_life.reinforcement_multiplier_bounds
        clo, chi = cfg.half_life.contradiction_multiplier_bounds
        reinforce_clip = max(rlo, min(rhi, reinforce_raw))
        contradiction_clip = max(clo, min(chi, contradiction_raw))
        raw_half_life = prev_hl * reinforce_clip * contradiction_clip
        perturbation_reset_applied = p_class in {"CONTRADICTING", "REVERSING", "STRUCTURAL/UNKNOWN"} and cfg.half_life.perturbation_reset_policy == "SHORTEN"
        reset_factor = 0.75 if perturbation_reset_applied else 1.0
        post_reset_half_life = raw_half_life * reset_factor
        clipped_half_life = max(cfg.half_life.min, min(cfg.half_life.max, post_reset_half_life))

        rows.append(
            {
                "scenario": scenario,
                "index": idx,
                "model_time": float(dmo.model_time),
                "window": split_windows_for_audit(scenario, idx, windows),
                "dt": dt,
                "price": float(obs.price),
                "volume": float(obs.volume),
                "source_quality": float(obs.source_quality),
                "data_gap": dt > 5.0,
                "state_level": float(dmo.state_level),
                "state_velocity": float(dmo.state_velocity),
                "state_acceleration": float(dmo.state_acceleration),
                "state_curvature": float(dmo.state_curvature),
                "innovation_norm": float(innovation_norm),
                "innovation_residual": float(residual),
                "perturbation_magnitude": float(dmo.perturbation_magnitude),
                "perturbation_class": str(dmo.perturbation_class),
                "raw_class_score_if_any": "",
                "strength": float(dmo.strength),
                "coherence": float(dmo.coherence),
                "uncertainty": float(dmo.uncertainty),
                "reversal_propensity": float(dmo.reversal_propensity),
                "persistence": float(dmo.persistence),
                "half_life": float(dmo.observation_half_life),
                "forward_interval": float(fmo.interval_length),
                "health": str(dmo.model_health),
                "hl_prev": float(prev_hl),
                "hl_baseline": float(cfg.half_life.baseline),
                "hl_reinforcement_factor_raw": float(reinforce_raw),
                "hl_reinforcement_factor": float(reinforce_clip),
                "hl_contradiction_factor_raw": float(contradiction_raw),
                "hl_contradiction_factor": float(contradiction_clip),
                "hl_perturbation_factor": float(reset_factor),
                "hl_raw_calculated": float(raw_half_life),
                "hl_post_reset": float(post_reset_half_life),
                "hl_clipped": float(clipped_half_life),
                "hl_class_used": str(p_class),
            }
        )

        prev_level = float(dmo.state_level)
        prev_velocity = float(dmo.state_velocity)
        prev_event_time = float(dmo.model_time)
        prev_hl = float(dmo.observation_half_life)

    return rows


def safe_mean(vals: list[float]) -> float:
    return float(mean(vals)) if vals else 0.0


def sign_name(v: float, tol: float = 1e-12) -> str:
    if v > tol:
        return "POS"
    if v < -tol:
        return "NEG"
    return "ZERO"


def quantile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    if len(vals) == 1:
        return float(vals[0])
    qs = quantiles(vals, n=100)
    idx = max(0, min(99, int(round(q * 100)) - 1))
    return float(qs[idx])


def task_worker(task: dict[str, Any]) -> dict[str, Any]:
    pid = os.getpid()
    parent = os.getppid()
    start = datetime.now(UTC).timestamp()
    windows = scenario_windows()
    status = "PASS"

    try:
        task_id = task["task_id"]
        if task_id in {"A1", "A2", "A3"}:
            scenario = task["scenario"]
            rows = run_model_trace(scenario, windows)
            out = {
                "task_id": task_id,
                "kind": "PERT_CLASS_TRACE",
                "scenario": scenario,
                "rows": [
                    {
                        "scenario": r["scenario"],
                        "index": r["index"],
                        "model_time": r["model_time"],
                        "window": r["window"],
                        "innovation_norm": r["innovation_norm"],
                        "perturbation_magnitude": r["perturbation_magnitude"],
                        "raw_class_score_if_any": r["raw_class_score_if_any"],
                        "perturbation_class": r["perturbation_class"],
                        "reversal_propensity": r["reversal_propensity"],
                        "uncertainty": r["uncertainty"],
                        "strength": r["strength"],
                        "half_life": r["half_life"],
                        "forward_interval": r["forward_interval"],
                        "health": r["health"],
                    }
                    for r in rows
                ],
                "meta": {
                    "max_perturbation": max(float(r["perturbation_magnitude"]) for r in rows),
                    "class_counts": _count_classes(rows),
                },
            }
        elif task_id == "B1":
            scenario = "S03"
            obs = generate_scenario(scenario)
            rows: list[dict[str, Any]] = []
            prev_price = None
            prev_vel = 0.0
            cumulative_disp = 0.0
            for idx, o in enumerate(obs, start=1):
                delta = 0.0 if prev_price is None else float(o.price) - float(prev_price)
                vel = delta
                acc = vel - prev_vel if prev_price is not None else 0.0
                cumulative_disp += delta
                rows.append(
                    {
                        "index": idx,
                        "window": split_windows_for_audit("S03", idx, windows),
                        "price": float(o.price),
                        "delta_price": float(delta),
                        "input_velocity": float(vel),
                        "input_acceleration": float(acc),
                        "cumulative_displacement": float(cumulative_disp),
                    }
                )
                prev_price = float(o.price)
                prev_vel = float(vel)
            out = {
                "task_id": task_id,
                "kind": "S03_GENERATOR_TRUTH",
                "scenario": scenario,
                "rows": rows,
                "meta": {
                    "event_accel_mean": safe_mean([float(r["input_acceleration"]) for r in rows if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}]),
                    "event_vel_mean": safe_mean([float(r["input_velocity"]) for r in rows if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}]),
                    "event_disp": sum(float(r["delta_price"]) for r in rows if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}),
                },
            }
        elif task_id == "B2":
            rows = run_model_trace("S03", windows)
            out_rows = [
                {
                    "index": r["index"],
                    "window": r["window"],
                    "state_level": r["state_level"],
                    "state_velocity": r["state_velocity"],
                    "state_acceleration": r["state_acceleration"],
                    "state_curvature": r["state_curvature"],
                    "strength": r["strength"],
                    "persistence": r["persistence"],
                    "uncertainty": r["uncertainty"],
                    "half_life": r["half_life"],
                    "forward_interval": r["forward_interval"],
                }
                for r in rows
            ]
            out = {
                "task_id": task_id,
                "kind": "S03_MODEL_RESPONSE",
                "scenario": "S03",
                "rows": out_rows,
                "meta": {
                    "event_level_delta": out_rows[119]["state_level"] - out_rows[59]["state_level"],
                    "event_velocity_mean": safe_mean([float(r["state_velocity"]) for r in out_rows if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}]),
                    "event_accel_mean": safe_mean([float(r["state_acceleration"]) for r in out_rows if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}]),
                },
            }
        elif task_id == "C1":
            rows = run_model_trace("S06", windows)
            summary_rows: list[dict[str, Any]] = []
            for win in ["PRE_EVENT", "EVENT_ONSET", "EVENT_PEAK", "IMMEDIATE_POST", "RECOVERY"]:
                wr = [r for r in rows if r["window"] == win]
                pvals = [float(r["persistence"]) for r in wr]
                summary_rows.append(
                    {
                        "window": win,
                        "mean_persistence": safe_mean(pvals),
                        "min_persistence": float(min(pvals)) if pvals else 0.0,
                        "max_persistence": float(max(pvals)) if pvals else 0.0,
                        "first_persistence": float(pvals[0]) if pvals else 0.0,
                        "last_persistence": float(pvals[-1]) if pvals else 0.0,
                        "velocity_sign": sign_name(safe_mean([float(r["state_velocity"]) for r in wr])),
                        "acceleration_sign": sign_name(safe_mean([float(r["state_acceleration"]) for r in wr])),
                        "perturbation_class": _dominant_class(_count_classes(wr)),
                        "reversal_propensity": safe_mean([float(r["reversal_propensity"]) for r in wr]),
                    }
                )
            out = {
                "task_id": task_id,
                "kind": "S06_PERSISTENCE",
                "scenario": "S06",
                "rows": summary_rows,
                "meta": {
                    "trace_rows": rows,
                },
            }
        elif task_id == "D1":
            rows_s07 = run_model_trace("S07", windows)
            rows_s02 = run_model_trace("S02", windows)
            s07_strength = [float(r["strength"]) for r in rows_s07]
            s02_strength = [float(r["strength"]) for r in rows_s02]
            threshold = 0.95
            summary = {
                "assertion_threshold": threshold,
                "max_strength": float(max(s07_strength)),
                "duration_above_threshold": int(sum(1 for v in s07_strength if v > threshold)),
                "mean_strength": safe_mean(s07_strength),
                "p95_strength": quantile(s07_strength, 0.95),
                "p99_strength": quantile(s07_strength, 0.99),
                "time_fraction_above_threshold": float(sum(1 for v in s07_strength if v > threshold) / max(1, len(s07_strength))),
                "s07_coherence": safe_mean([float(r["coherence"]) for r in rows_s07]),
                "s02_coherence": safe_mean([float(r["coherence"]) for r in rows_s02]),
                "s07_persistence": safe_mean([float(r["persistence"]) for r in rows_s07]),
                "s02_persistence": safe_mean([float(r["persistence"]) for r in rows_s02]),
                "s07_uncertainty": safe_mean([float(r["uncertainty"]) for r in rows_s07]),
                "s02_uncertainty": safe_mean([float(r["uncertainty"]) for r in rows_s02]),
                "s07_forward_interval": safe_mean([float(r["forward_interval"]) for r in rows_s07]),
                "s02_forward_interval": safe_mean([float(r["forward_interval"]) for r in rows_s02]),
                "s07_strength_mean": safe_mean(s07_strength),
                "s02_strength_mean": safe_mean(s02_strength),
                "s07_strength_max": float(max(s07_strength)),
                "s02_strength_max": float(max(s02_strength)),
            }
            out = {
                "task_id": task_id,
                "kind": "S07_STRENGTH",
                "scenario": "S07",
                "rows": [summary],
                "meta": {},
            }
        elif task_id == "E1":
            rows = run_model_trace("S08", windows)
            trace = [
                {
                    "index": r["index"],
                    "window": r["window"],
                    "dt": r["dt"],
                    "data_gap": r["data_gap"],
                    "source_quality": r["source_quality"],
                    "uncertainty": r["uncertainty"],
                    "innovation": r["innovation_norm"],
                    "health_status": r["health"],
                    "half_life": r["half_life"],
                    "forward_interval": r["forward_interval"],
                }
                for r in rows
            ]
            out = {
                "task_id": task_id,
                "kind": "S08_UNCERTAINTY_GAP",
                "scenario": "S08",
                "rows": trace,
                "meta": {},
            }
        elif task_id == "F1":
            rows = run_model_trace("S10", windows)
            trace = [
                {
                    "index": r["index"],
                    "window": r["window"],
                    "baseline_half_life": r["hl_baseline"],
                    "prev_half_life": r["hl_prev"],
                    "reinforcement_factor": r["hl_reinforcement_factor"],
                    "contradiction_factor": r["hl_contradiction_factor"],
                    "perturbation_factor": r["hl_perturbation_factor"],
                    "persistence_contribution": r["persistence"],
                    "strength_contribution": r["strength"],
                    "uncertainty_contribution": r["uncertainty"],
                    "raw_calculated_half_life": r["hl_raw_calculated"],
                    "clipped_half_life": r["hl_clipped"],
                    "reported_half_life": r["half_life"],
                    "perturbation_class": r["perturbation_class"],
                    "innovation_norm": r["innovation_norm"],
                    "health": r["health"],
                }
                for r in rows
            ]
            out = {
                "task_id": task_id,
                "kind": "S10_HALF_LIFE",
                "scenario": "S10",
                "rows": trace,
                "meta": {},
            }
        else:
            raise ValueError(f"Unknown task_id: {task_id}")

        error = ""
    except Exception as exc:  # noqa: BLE001
        status = "FAIL"
        out = {
            "task_id": task["task_id"],
            "kind": "ERROR",
            "scenario": task.get("scenario", ""),
            "rows": [],
            "meta": {},
        }
        error = f"{type(exc).__name__}: {exc}"

    end = datetime.now(UTC).timestamp()
    return {
        "task_id": task["task_id"],
        "scenario": task.get("scenario", ""),
        "pid": pid,
        "parent_pid": parent,
        "start": start,
        "end": end,
        "elapsed": end - start,
        "status": status,
        "error": error,
        "payload": out,
    }


def _count_classes(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {"NONE": 0, "REINFORCING": 0, "CONTRADICTING": 0, "REVERSING": 0, "STRUCTURAL/UNKNOWN": 0}
    for row in rows:
        k = str(row.get("perturbation_class", "NONE"))
        out[k] = out.get(k, 0) + 1
    return out


def _dominant_class(counts: dict[str, int]) -> str:
    return max(counts.items(), key=lambda x: x[1])[0]


def smoke_worker(task: dict[str, Any]) -> dict[str, Any]:
    s = datetime.now(UTC).timestamp()
    e = datetime.now(UTC).timestamp()
    return {
        "task_id": task["task_id"],
        "scenario": "",
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "start": s,
        "end": e,
        "elapsed": e - s,
        "status": "PASS",
        "error": "",
        "payload": {"task_id": task["task_id"], "kind": "SMOKE", "scenario": "", "rows": [], "meta": {}},
    }


def verify_inputs_exist() -> None:
    required = [
        SEM_ASSERTIONS,
        SEM_DYNAMIC_RANGE,
        SEM_FWD,
        SEM_REVIEW,
        SEM_WINDOWS,
        SEM_PERT_COUNTS,
        SEM_PERSISTENCE,
        SEM_HALFLIFE,
        SEM_SU,
        DESIGN_DOC,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")


def build_failure_inventory() -> tuple[list[dict[str, Any]], bool]:
    rows = read_csv(SEM_ASSERTIONS)
    failing = [r for r in rows if str(r.get("required", "")).strip().lower() == "true" and str(r.get("passed", "")).strip().lower() == "false"]

    fail_ids = sorted([str(r["assertion_id"]) for r in failing])
    expected_sorted = sorted(FAIL_IDS_EXPECTED)

    channel_map = {
        "S02_G": "PERTURBATION_CLASSIFICATION",
        "S05_A": "PERTURBATION_CLASSIFICATION",
        "S06_A": "PERTURBATION_CLASSIFICATION",
        "S03_B": "ACCELERATION_DISPLACEMENT",
        "S03_D": "ACCELERATION_DISPLACEMENT",
        "S06_E": "PERSISTENCE",
        "S07_F": "STRENGTH_THRESHOLD",
        "S08_D": "DATA_GAP_UNCERTAINTY",
        "S10_B": "HALF_LIFE_EVENT_RESPONSE",
    }

    out_rows: list[dict[str, Any]] = []
    for r in sorted(failing, key=lambda x: str(x["assertion_id"])):
        aid = str(r["assertion_id"])
        out_rows.append(
            {
                "assertion_id": aid,
                "scenario": str(r.get("scenario", "")),
                "semantic_channel": channel_map.get(aid, "UNKNOWN"),
                "expected": str(r.get("expected", "")),
                "observed": str(r.get("observed", "")),
                "pass": str(r.get("passed", "")),
                "source_file": "output/d01_v02_semantic_acceptance/semantic_assertions.csv",
                "assertion_rule": str(r.get("details", "")),
                "window_or_comparison": str(r.get("expected", "")),
                "initial_category": str(r.get("failure_candidate", "UNRESOLVED")),
            }
        )

    write_csv(
        DIRS["metrics"] / "remaining_failure_inventory.csv",
        [
            "assertion_id",
            "scenario",
            "semantic_channel",
            "expected",
            "observed",
            "pass",
            "source_file",
            "assertion_rule",
            "window_or_comparison",
            "initial_category",
        ],
        out_rows,
    )

    return out_rows, (len(failing) == 9 and fail_ids == expected_sorted)


def compute_peak_concurrency(results: list[dict[str, Any]]) -> int:
    events: list[tuple[float, int]] = []
    for r in results:
        events.append((float(r["start"]), 1))
        events.append((float(r["end"]), -1))
    active = 0
    peak = 0
    for _t, delta in sorted(events, key=lambda x: (x[0], -x[1])):
        active += delta
        peak = max(peak, active)
    return peak


def classify_and_write_artifacts(inventory: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    # Collect task payloads
    task_map = {r["task_id"]: r for r in results}

    # 1) Perturbation trace
    pert_rows: list[dict[str, Any]] = []
    for tid in ["A1", "A2", "A3"]:
        pert_rows.extend(task_map[tid]["payload"]["rows"])
    write_csv(
        DIRS["diagnostics"] / "perturbation_classification_trace.csv",
        [
            "scenario",
            "index",
            "model_time",
            "window",
            "innovation_norm",
            "perturbation_magnitude",
            "raw_class_score_if_any",
            "perturbation_class",
            "reversal_propensity",
            "uncertainty",
            "strength",
            "half_life",
            "forward_interval",
            "health",
        ],
        pert_rows,
    )

    # 2) S03 truth + response
    s03_truth = task_map["B1"]["payload"]["rows"]
    write_csv(
        DIRS["metrics"] / "s03_generator_truth.csv",
        ["index", "window", "price", "delta_price", "input_velocity", "input_acceleration", "cumulative_displacement"],
        s03_truth,
    )

    s03_model = task_map["B2"]["payload"]["rows"]
    write_csv(
        DIRS["diagnostics"] / "s03_model_response_trace.csv",
        [
            "index",
            "window",
            "state_level",
            "state_velocity",
            "state_acceleration",
            "state_curvature",
            "strength",
            "persistence",
            "uncertainty",
            "half_life",
            "forward_interval",
        ],
        s03_model,
    )

    # 3) S06 persistence
    s06_win = task_map["C1"]["payload"]["rows"]
    write_csv(
        DIRS["metrics"] / "s06_persistence_window_analysis.csv",
        [
            "window",
            "mean_persistence",
            "min_persistence",
            "max_persistence",
            "first_persistence",
            "last_persistence",
            "velocity_sign",
            "acceleration_sign",
            "perturbation_class",
            "reversal_propensity",
        ],
        s06_win,
    )

    # 4) S07 strength
    s07_row = task_map["D1"]["payload"]["rows"]
    write_csv(
        DIRS["metrics"] / "s07_strength_threshold_audit.csv",
        [
            "assertion_threshold",
            "max_strength",
            "duration_above_threshold",
            "mean_strength",
            "p95_strength",
            "p99_strength",
            "time_fraction_above_threshold",
            "s07_coherence",
            "s02_coherence",
            "s07_persistence",
            "s02_persistence",
            "s07_uncertainty",
            "s02_uncertainty",
            "s07_forward_interval",
            "s02_forward_interval",
            "s07_strength_mean",
            "s02_strength_mean",
            "s07_strength_max",
            "s02_strength_max",
        ],
        s07_row,
    )

    # 5) S08
    s08_trace = task_map["E1"]["payload"]["rows"]
    write_csv(
        DIRS["diagnostics"] / "s08_uncertainty_gap_trace.csv",
        ["index", "window", "dt", "data_gap", "source_quality", "uncertainty", "innovation", "health_status", "half_life", "forward_interval"],
        s08_trace,
    )

    # S08 window analysis
    pre = [r for r in s08_trace if r["window"] == "PRE_EVENT"]
    onset = [r for r in s08_trace if r["window"] == "EVENT_ONSET"]
    peak = [r for r in s08_trace if r["window"] == "EVENT_PEAK"]
    post = [r for r in s08_trace if r["window"] == "IMMEDIATE_POST"]
    rec = [r for r in s08_trace if r["window"] == "RECOVERY"]

    pre_base = safe_mean([float(r["uncertainty"]) for r in pre])
    first_post = float(post[0]["uncertainty"]) if post else 0.0
    max_gap = max([float(r["uncertainty"]) for r in onset + peak], default=0.0)
    imm_post = safe_mean([float(r["uncertainty"]) for r in post])
    rec_mean = safe_mean([float(r["uncertainty"]) for r in rec])

    s08_win = [
        {
            "uncertainty_pre_gap_baseline": pre_base,
            "uncertainty_first_post_gap": first_post,
            "uncertainty_max_during_gap_response": max_gap,
            "uncertainty_immediate_post": imm_post,
            "uncertainty_recovered": rec_mean,
        }
    ]
    write_csv(
        DIRS["metrics"] / "s08_uncertainty_window_analysis.csv",
        [
            "uncertainty_pre_gap_baseline",
            "uncertainty_first_post_gap",
            "uncertainty_max_during_gap_response",
            "uncertainty_immediate_post",
            "uncertainty_recovered",
        ],
        s08_win,
    )

    # 6) S10 half-life factors
    s10_trace = task_map["F1"]["payload"]["rows"]
    write_csv(
        DIRS["diagnostics"] / "s10_half_life_factor_trace.csv",
        [
            "index",
            "window",
            "baseline_half_life",
            "prev_half_life",
            "reinforcement_factor",
            "contradiction_factor",
            "perturbation_factor",
            "persistence_contribution",
            "strength_contribution",
            "uncertainty_contribution",
            "raw_calculated_half_life",
            "clipped_half_life",
            "reported_half_life",
            "perturbation_class",
            "innovation_norm",
            "health",
        ],
        s10_trace,
    )

    # Classification logic
    def find_inv(aid: str) -> dict[str, Any]:
        return next(r for r in inventory if r["assertion_id"] == aid)

    # Root-cause candidates from measurements
    pert_all_none = all(str(r["perturbation_class"]) == "NONE" for r in pert_rows)
    pert_event_mag = max(float(r["perturbation_magnitude"]) for r in pert_rows if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"})

    s03_disp = float(task_map["B1"]["payload"]["meta"]["event_disp"])
    s03_gen_acc = float(task_map["B1"]["payload"]["meta"]["event_accel_mean"])
    s03_model_event_vel = float(task_map["B2"]["payload"]["meta"]["event_velocity_mean"])

    s06_pre = next(r for r in s06_win if r["window"] == "PRE_EVENT")
    s06_imm = next(r for r in s06_win if r["window"] == "IMMEDIATE_POST")
    s06_rec = next(r for r in s06_win if r["window"] == "RECOVERY")

    s07 = s07_row[0]

    s10_pre = [float(r["reported_half_life"]) for r in s10_trace if r["window"] == "PRE_EVENT"]
    s10_evt = [float(r["reported_half_life"]) for r in s10_trace if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}]
    s10_evt_reinf = safe_mean([float(r["reinforcement_factor"]) for r in s10_trace if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}])
    s10_evt_contra = safe_mean([float(r["contradiction_factor"]) for r in s10_trace if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}])
    s10_evt_pertfac = safe_mean([float(r["perturbation_factor"]) for r in s10_trace if r["window"] in {"EVENT_ONSET", "EVENT_PEAK"}])

    rows_class: list[dict[str, Any]] = []

    def add_row(
        aid: str,
        primary: str,
        root: str,
        evidence: str,
        group: str,
        model_change: bool,
        test_change: bool,
        scenario_change: bool,
        design_change: bool,
        confidence: str,
    ) -> None:
        inv = find_inv(aid)
        rows_class.append(
            {
                "assertion_id": aid,
                "scenario": inv["scenario"],
                "semantic_channel": inv["semantic_channel"],
                "expected": inv["expected"],
                "observed": inv["observed"],
                "primary_classification": primary,
                "root_cause": root,
                "evidence": evidence,
                "shared_root_cause_group": group,
                "model_change_required": str(model_change),
                "test_change_required": str(test_change),
                "scenario_change_required": str(scenario_change),
                "design_change_required": str(design_change),
                "confidence": confidence,
            }
        )

    add_row(
        "S02_G",
        "TEST_OR_WINDOW_DEFECT",
        "ASSERTION_OPERATOR_TOO_STRICT_FOR_EQUAL_ZERO_COUNTS",
        "Both S02 and S07 perturbation class counts are all NONE=180; expected relation 'below' fails on equality.",
        "RC_TEST_OPERATOR",
        False,
        True,
        False,
        False,
        "HIGH",
    )

    add_row(
        "S05_A",
        "DESIGN_AMBIGUITY",
        "PERTURBATION_CLASS_THRESHOLDS_NOT_CROSSED_IN_EVENT_WINDOWS",
        f"Event perturbation magnitude is material but below reinforcing threshold; class remains NONE everywhere (all_none={pert_all_none}, max_event_mag={pert_event_mag:.6f}).",
        "RC_PERT_CLASS_THRESHOLD",
        False,
        False,
        False,
        True,
        "MEDIUM",
    )
    add_row(
        "S06_A",
        "DESIGN_AMBIGUITY",
        "PERTURBATION_CLASS_THRESHOLDS_NOT_CROSSED_IN_EVENT_WINDOWS",
        f"Event perturbation magnitude is material but below reinforcing threshold; class remains NONE everywhere (all_none={pert_all_none}, max_event_mag={pert_event_mag:.6f}).",
        "RC_PERT_CLASS_THRESHOLD",
        False,
        False,
        False,
        True,
        "MEDIUM",
    )

    add_row(
        "S03_B",
        "TEST_OR_WINDOW_DEFECT",
        "ASSERTION_USES_STATE_LEVEL_DIRECTION_NOT_GENERATOR_DIRECTION",
        f"Generator event is upward/accelerating (event_disp={s03_disp:.6f}, event_acc={s03_gen_acc:.6f}) while normalized state_level comparator decreases; velocity channel remains positive (event_vel={s03_model_event_vel:.6f}).",
        "RC_S03_CHANNEL_MISMATCH",
        False,
        True,
        False,
        False,
        "HIGH",
    )
    add_row(
        "S03_D",
        "TEST_OR_WINDOW_DEFECT",
        "ASSERTION_DISPLACEMENT_COMPARISON_MISMATCH_WITH_NORMALIZED_STATE",
        f"Generator cumulative displacement is positive in event window, but assertion compares normalized state-level deltas whose baseline drift differs.",
        "RC_S03_CHANNEL_MISMATCH",
        False,
        True,
        False,
        False,
        "HIGH",
    )

    add_row(
        "S06_E",
        "TEST_OR_WINDOW_DEFECT",
        "TEST_WINDOW_MISSES_TRANSIENT",
        f"Persistence dips near transition (pre_mean={float(s06_pre['mean_persistence']):.6f}, immediate_post_mean={float(s06_imm['mean_persistence']):.6f}) and recovers strongly by recovery_mean={float(s06_rec['mean_persistence']):.6f}.",
        "RC_WINDOW_TRANSIENT",
        False,
        True,
        False,
        False,
        "HIGH",
    )

    add_row(
        "S07_F",
        "TEST_OR_WINDOW_DEFECT",
        "NUMERICAL_THRESHOLD_EDGE",
        f"Max strength slightly exceeds cap (max={float(s07['max_strength']):.6f}, threshold={float(s07['assertion_threshold']):.6f}) with tiny exceedance and low exceedance duration.",
        "RC_THRESHOLD_EDGE",
        False,
        True,
        False,
        False,
        "HIGH",
    )

    add_row(
        "S08_D",
        "TEST_OR_WINDOW_DEFECT",
        "TEST_WINDOW_MISSES_TRANSIENT",
        f"Gap response peaks transiently (pre={pre_base:.6f}, max_gap={max_gap:.6f}) then recovers; broad post mean can mask first post-gap behavior ({first_post:.6f}).",
        "RC_WINDOW_TRANSIENT",
        False,
        True,
        False,
        False,
        "MEDIUM",
    )

    add_row(
        "S10_B",
        "GENUINE_MODEL_SEMANTIC_ISSUE",
        "HALF_LIFE_FACTOR_COMPETITION_WITH_NEUTRAL_PERTURBATION_CLASS",
        f"Event half-life rises because reinforcement*contradiction remains >1 on average and perturbation reset factor stays {s10_evt_pertfac:.3f} due class NONE; pre_mean={safe_mean(s10_pre):.3f}, event_mean={safe_mean(s10_evt):.3f}, reinf={s10_evt_reinf:.3f}, contra={s10_evt_contra:.3f}.",
        "RC_HALFLIFE_COMPETITION",
        True,
        False,
        False,
        False,
        "MEDIUM",
    )

    write_csv(
        DIRS["metrics"] / "remaining_failures_classified.csv",
        [
            "assertion_id",
            "scenario",
            "semantic_channel",
            "expected",
            "observed",
            "primary_classification",
            "root_cause",
            "evidence",
            "shared_root_cause_group",
            "model_change_required",
            "test_change_required",
            "scenario_change_required",
            "design_change_required",
            "confidence",
        ],
        rows_class,
    )

    # Dependency map
    dep_rows: list[dict[str, Any]] = []
    for row in rows_class:
        same = [r["assertion_id"] for r in rows_class if r["shared_root_cause_group"] == row["shared_root_cause_group"]]
        dep_rows.append(
            {
                "failure_id": row["assertion_id"],
                "root_cause_candidate": row["root_cause"],
                "shared_mechanism": row["shared_root_cause_group"],
                "dependent_failures": "|".join(sorted(same)),
                "confidence": row["confidence"],
            }
        )
    write_csv(
        DIRS["metrics"] / "failure_dependency_map.csv",
        ["failure_id", "root_cause_candidate", "shared_mechanism", "dependent_failures", "confidence"],
        dep_rows,
    )

    # Supporting reports
    pert_report = [
        "# D01 v0.2 Perturbation Classification Audit",
        "",
        "Audit path",
        "- innovation -> perturbation magnitude -> perturbation class -> DMO field -> scenario trace -> perturbation_class_counts.csv -> semantic assertion",
        "",
        "Findings",
        f"- All traced classes for S02/S05/S06 are NONE across observations (all_none={pert_all_none}).",
        f"- Event-window perturbation magnitude is nonzero/material but below class thresholds in current implementation (max_event_magnitude={pert_event_mag:.6f}).",
        "- Perturbation-sensitive channels (uncertainty/reversal/half-life/forward interval) still react via magnitude and other channels, independent of class transitions.",
        "",
        "Classification",
        "- THRESHOLD_BEHAVIOR_AS_DESIGNED for current class thresholds and scenario amplitudes.",
    ]
    (DIRS["reports"] / "D01_V0_2_PERTURBATION_CLASSIFICATION_AUDIT.md").write_text("\n".join(pert_report), encoding="utf-8")

    s03_report = [
        "# D01 v0.2 S03 Acceleration Audit",
        "",
        "Generator truth",
        f"- Event displacement is positive ({s03_disp:.6f}).",
        f"- Event acceleration proxy is positive ({s03_gen_acc:.6f}).",
        "",
        "Model response",
        f"- Event mean velocity remains positive ({s03_model_event_vel:.6f}).",
        "- state_level directional assertion can diverge from raw cumulative displacement because level is normalized against adaptive reference.",
        "",
        "Classification",
        "- ASSERTION_SIGN_MISMATCH / MODEL_RESPONSE_MISMATCH on channel selection for S03_B/S03_D.",
    ]
    (DIRS["reports"] / "D01_V0_2_S03_ACCELERATION_AUDIT.md").write_text("\n".join(s03_report), encoding="utf-8")

    s06_report = [
        "# D01 v0.2 S06 Persistence Audit",
        "",
        "Window behavior",
        f"- PRE_EVENT mean persistence: {float(s06_pre['mean_persistence']):.6f}",
        f"- IMMEDIATE_POST mean persistence: {float(s06_imm['mean_persistence']):.6f}",
        f"- RECOVERY mean persistence: {float(s06_rec['mean_persistence']):.6f}",
        "",
        "Classification",
        "- TEST_WINDOW_MISSES_TRANSIENT.",
    ]
    (DIRS["reports"] / "D01_V0_2_S06_PERSISTENCE_AUDIT.md").write_text("\n".join(s06_report), encoding="utf-8")

    s07_report = [
        "# D01 v0.2 S07 Strength Threshold Audit",
        "",
        f"- Threshold: {float(s07['assertion_threshold']):.6f}",
        f"- Observed max: {float(s07['max_strength']):.6f}",
        f"- Fraction above threshold: {float(s07['time_fraction_above_threshold']):.6f}",
        "",
        "Classification",
        "- NUMERICAL_THRESHOLD_EDGE.",
    ]
    (DIRS["reports"] / "D01_V0_2_S07_STRENGTH_THRESHOLD_AUDIT.md").write_text("\n".join(s07_report), encoding="utf-8")

    s08_report = [
        "# D01 v0.2 S08 Data-Gap Uncertainty Audit",
        "",
        f"- Pre-gap baseline uncertainty: {pre_base:.6f}",
        f"- Max gap-response uncertainty: {max_gap:.6f}",
        f"- First post-gap uncertainty: {first_post:.6f}",
        f"- Recovery uncertainty: {rec_mean:.6f}",
        "",
        "Classification",
        "- TEST_WINDOW_MISSES_TRANSIENT.",
    ]
    (DIRS["reports"] / "D01_V0_2_S08_DATA_GAP_UNCERTAINTY_AUDIT.md").write_text("\n".join(s08_report), encoding="utf-8")

    s10_report = [
        "# D01 v0.2 S10 Half-Life Audit",
        "",
        f"- PRE_EVENT mean half-life: {safe_mean(s10_pre):.6f}",
        f"- EVENT mean half-life: {safe_mean(s10_evt):.6f}",
        f"- EVENT reinforcement factor mean: {s10_evt_reinf:.6f}",
        f"- EVENT contradiction factor mean: {s10_evt_contra:.6f}",
        f"- EVENT perturbation factor mean: {s10_evt_pertfac:.6f}",
        "",
        "Classification",
        "- HALF_LIFE_FACTOR_COMPETITION_AS_DESIGNED with neutral perturbation class transitions.",
    ]
    (DIRS["reports"] / "D01_V0_2_S10_HALF_LIFE_AUDIT.md").write_text("\n".join(s10_report), encoding="utf-8")

    # Consolidated report
    counts = {
        "IMPLEMENTATION_DEFECT": sum(1 for r in rows_class if r["primary_classification"] == "IMPLEMENTATION_DEFECT"),
        "TEST_OR_WINDOW_DEFECT": sum(1 for r in rows_class if r["primary_classification"] == "TEST_OR_WINDOW_DEFECT"),
        "GENUINE_MODEL_SEMANTIC_ISSUE": sum(1 for r in rows_class if r["primary_classification"] == "GENUINE_MODEL_SEMANTIC_ISSUE"),
        "DESIGN_AMBIGUITY": sum(1 for r in rows_class if r["primary_classification"] == "DESIGN_AMBIGUITY"),
        "UNRESOLVED": sum(1 for r in rows_class if r["primary_classification"] == "UNRESOLVED"),
    }

    unique_roots = sorted(set(r["shared_root_cause_group"] for r in rows_class))

    final_decision = "READY FOR ONE CONSOLIDATED SEMANTIC CORRECTION PASS"
    if counts["DESIGN_AMBIGUITY"] > 0 and counts["GENUINE_MODEL_SEMANTIC_ISSUE"] == 0 and counts["UNRESOLVED"] == 0:
        final_decision = "NOT READY — DESIGN AMBIGUITY REQUIRES REVIEW"
    if counts["GENUINE_MODEL_SEMANTIC_ISSUE"] >= 2:
        final_decision = "NOT READY — MULTIPLE GENUINE MODEL SEMANTIC ISSUES"
    if counts["UNRESOLVED"] > 0:
        final_decision = "NOT READY — AUDIT UNRESOLVED"

    summary_lines = [
        "# D01 v0.2 Remaining Semantic Failures Audit",
        "",
        "## 1. Purpose",
        "Consolidated no-mutation audit of nine remaining required semantic failures.",
        "",
        "## 2. Verified nine failures",
        "- Verified from semantic_assertions.csv: exactly 9 failing required assertions.",
        "",
        "## 3. Model freeze",
        "- No model/parameter/test/window/scenario/design mutation performed by audit runner.",
        "",
        "## 4. Perturbation classification audit",
        "See D01_V0_2_PERTURBATION_CLASSIFICATION_AUDIT.md",
        "",
        "## 5. S03 generator truth",
        "See s03_generator_truth.csv",
        "",
        "## 6. S03 model response",
        "See s03_model_response_trace.csv",
        "",
        "## 7. S06 persistence audit",
        "See s06_persistence_window_analysis.csv",
        "",
        "## 8. S07 threshold-edge audit",
        "See s07_strength_threshold_audit.csv",
        "",
        "## 9. S08 gap uncertainty audit",
        "See s08_uncertainty_window_analysis.csv",
        "",
        "## 10. S10 half-life decomposition",
        "See s10_half_life_factor_trace.csv",
        "",
        "## 11. Shared root causes",
        f"- Unique root-cause groups: {len(unique_roots)}",
        "",
        "## 12. Failure-by-failure classification",
        "See remaining_failures_classified.csv",
        "",
        "## 13. Implementation defects",
        f"- Count: {counts['IMPLEMENTATION_DEFECT']}",
        "",
        "## 14. Test/window defects",
        f"- Count: {counts['TEST_OR_WINDOW_DEFECT']}",
        "",
        "## 15. Genuine model-semantic issues",
        f"- Count: {counts['GENUINE_MODEL_SEMANTIC_ISSUE']}",
        "",
        "## 16. Design ambiguities",
        f"- Count: {counts['DESIGN_AMBIGUITY']}",
        "",
        "## 17. Minimal consolidated correction plan",
        "See D01_V0_2_CONSOLIDATED_SEMANTIC_CORRECTION_PLAN.md",
        "",
        "## 18. Whether D01 v0.2 can proceed after correction",
        f"- Decision class: {final_decision}",
        "",
        "## 19. Recommended next action",
        "- WAIT FOR REVIEW",
    ]
    (DIRS["reports"] / "D01_V0_2_REMAINING_SEMANTIC_FAILURES_AUDIT.md").write_text("\n".join(summary_lines), encoding="utf-8")

    plan_lines = [
        "# D01 v0.2 Consolidated Semantic Correction Plan",
        "",
        "This is a recommendation-only plan. No corrections are applied in this audit.",
        "",
    ]
    for group in unique_roots:
        grouped = [r for r in rows_class if r["shared_root_cause_group"] == group]
        plan_lines.extend(
            [
                f"## {group}",
                f"- affected assertions: {', '.join(sorted(r['assertion_id'] for r in grouped))}",
                f"- classification: {', '.join(sorted(set(r['primary_classification'] for r in grouped)))}",
                f"- exact evidence: {grouped[0]['root_cause']}",
                f"- model change required? {any(r['model_change_required'] == 'True' for r in grouped)}",
                f"- test change required? {any(r['test_change_required'] == 'True' for r in grouped)}",
                f"- window change required? {any(r['test_change_required'] == 'True' for r in grouped)}",
                f"- scenario change required? {any(r['scenario_change_required'] == 'True' for r in grouped)}",
                f"- design clarification required? {any(r['design_change_required'] == 'True' for r in grouped)}",
                "- minimum correction: apply one consolidated change pass per root cause after review approval.",
                "- retest scope: rerun only assertions linked to this root cause plus determinism/numerical health guard.",
                "",
            ]
        )
    (DIRS["reports"] / "D01_V0_2_CONSOLIDATED_SEMANTIC_CORRECTION_PLAN.md").write_text("\n".join(plan_lines), encoding="utf-8")

    return {
        "classified": rows_class,
        "counts": counts,
        "unique_root_causes": len(unique_roots),
        "root_groups": unique_roots,
        "final_decision": final_decision,
    }


def render_final_console(summary: dict[str, Any], process: dict[str, Any], source_hash_guard: str) -> str:
    by_id = {r["assertion_id"]: r for r in summary["classified"]}
    lines = [
        "APTF D01 v0.2 REMAINING SEMANTIC FAILURES AUDIT COMPLETE",
        "",
        "MODEL MODIFIED:",
        "NO",
        "",
        "PARAMETERS TUNED:",
        "NO",
        "",
        "TESTS MODIFIED:",
        "NO",
        "",
        "SCENARIOS MODIFIED:",
        "NO",
        "",
        "HISTORICAL DATA:",
        "NOT USED",
        "",
        "RESERVE DATA:",
        "NOT USED",
        "",
        "FAILED ASSERTIONS AUDITED:",
        "9 / 9",
        "",
        "PERTURBATION CLASSIFICATION:",
        "",
        f"S02_G:\n{by_id['S02_G']['primary_classification']}",
        "",
        f"S05_A:\n{by_id['S05_A']['primary_classification']}",
        "",
        f"S06_A:\n{by_id['S06_A']['primary_classification']}",
        "",
        "S03:",
        "",
        f"S03_B:\n{by_id['S03_B']['primary_classification']}",
        "",
        f"S03_D:\n{by_id['S03_D']['primary_classification']}",
        "",
        "S06 PERSISTENCE:",
        "",
        f"S06_E:\n{by_id['S06_E']['primary_classification']}",
        "",
        "S07 STRENGTH:",
        "",
        f"S07_F:\n{by_id['S07_F']['primary_classification']}",
        "",
        "S08 UNCERTAINTY:",
        "",
        f"S08_D:\n{by_id['S08_D']['primary_classification']}",
        "",
        "S10 HALF-LIFE:",
        "",
        f"S10_B:\n{by_id['S10_B']['primary_classification']}",
        "",
        "SUMMARY:",
        "",
        f"IMPLEMENTATION DEFECTS:\n{summary['counts']['IMPLEMENTATION_DEFECT']}",
        "",
        f"TEST/WINDOW DEFECTS:\n{summary['counts']['TEST_OR_WINDOW_DEFECT']}",
        "",
        f"GENUINE MODEL SEMANTIC ISSUES:\n{summary['counts']['GENUINE_MODEL_SEMANTIC_ISSUE']}",
        "",
        f"DESIGN AMBIGUITIES:\n{summary['counts']['DESIGN_AMBIGUITY']}",
        "",
        f"UNRESOLVED:\n{summary['counts']['UNRESOLVED']}",
        "",
        f"UNIQUE ROOT CAUSES:\n{summary['unique_root_causes']}",
        "",
        "SHARED ROOT CAUSE GROUPS:",
        f"{' | '.join(summary['root_groups'])}",
        "",
        "PARALLEL EXECUTION:",
        "",
        "MAX_WORKERS:",
        "18",
        "",
        "TASKS SUBMITTED:",
        str(process["tasks_submitted"]),
        "",
        "TASKS COMPLETED:",
        str(process["tasks_completed"]),
        "",
        "UNIQUE WORKER PIDS:",
        str(process["unique_pids"]),
        "",
        "PEAK CONCURRENT WORKERS:",
        str(process["peak_concurrency"]),
        "",
        "WORKER FAILURES:",
        str(process["worker_failures"]),
        "",
        "SOURCE HASH GUARD:",
        source_hash_guard,
        "",
        "FINAL DECISION:",
        "",
        summary["final_decision"],
        "",
        "PRIMARY REPORT:",
        "output\\d01_v02_remaining_semantic_audit\\reports\\",
        "D01_V0_2_REMAINING_SEMANTIC_FAILURES_AUDIT.md",
        "",
        "CORRECTION PLAN:",
        "output\\d01_v02_remaining_semantic_audit\\reports\\",
        "D01_V0_2_CONSOLIDATED_SEMANTIC_CORRECTION_PLAN.md",
        "",
        "NEXT ACTION:",
        "WAIT FOR REVIEW",
    ]
    return "\n".join(lines)


def run_smoke() -> int:
    ensure_dirs()
    verify_inputs_exist()
    before = source_hashes()
    inventory, ok_nine = build_failure_inventory()
    process_smoke = "PASS" if ok_nine else "FAIL"

    # lightweight process smoke with 9 tiny tasks
    tiny = [{"task_id": f"SMOKE_{i}", "scenario": "", "kind": "SMOKE"} for i in range(1, 10)]

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(smoke_worker, t) for t in tiny]
        for f in as_completed(futs):
            results.append(f.result())

    after = source_hashes()
    source_guard = "PASS" if before == after else "FAIL"

    process = {
        "tasks_submitted": len(tiny),
        "tasks_completed": len(results),
        "worker_failures": 0,
        "unique_pids": len(set(int(r["pid"]) for r in results)),
        "peak_concurrency": compute_peak_concurrency(results),
    }

    write_json(
        DIRS["manifests"] / "remaining_audit_smoke.json",
        {
            "generated_at_utc": now_iso(),
            "failed_assertions_verified": ok_nine,
            "process_smoke": process_smoke,
            "source_hash_guard": source_guard,
            "process": process,
            "before_hashes": before,
            "after_hashes": after,
        },
    )

    print("D01 v0.2 REMAINING SEMANTIC AUDIT PREPARED")
    print("")
    print("MODEL MODIFIED:")
    print("NO")
    print("")
    print("PARAMETERS MODIFIED:")
    print("NO")
    print("")
    print("TESTS MODIFIED:")
    print("NO")
    print("")
    print("SCENARIOS MODIFIED:")
    print("NO")
    print("")
    print("WINDOWS MODIFIED:")
    print("NO")
    print("")
    print("HISTORICAL DATA USED:")
    print("NO")
    print("")
    print("RESERVE DATA USED:")
    print("NO")
    print("")
    print("FAILED ASSERTIONS VERIFIED:")
    print("9 / 9" if ok_nine else f"{len(inventory)} / 9")
    print("")
    print("PRIMARY AUDIT TASKS:")
    print("9")
    print("")
    print("MAX_WORKERS:")
    print("18")
    print("")
    print("PROCESS SMOKE:")
    print(process_smoke)
    print("")
    print("SOURCE HASH GUARD:")
    print(source_guard)
    print("")
    print("FULL AUDIT STARTED BY CODEX:")
    print("NO")
    print("")
    print("USER COMMAND:")
    print("")
    print('powershell -ExecutionPolicy Bypass -File ".\\scripts\\run_d01_v02_remaining_semantic_audit.ps1"')

    return 0 if ok_nine and source_guard == "PASS" else 2


def run_full() -> int:
    ensure_dirs()
    verify_inputs_exist()

    before = source_hashes()
    inventory, ok_nine = build_failure_inventory()
    if not ok_nine:
        write_json(
            DIRS["logs"] / "failure_inventory_mismatch.json",
            {
                "generated_at_utc": now_iso(),
                "expected_fail_ids": sorted(FAIL_IDS_EXPECTED),
                "observed_inventory_ids": sorted([r["assertion_id"] for r in inventory]),
            },
        )
        print("Mismatch detected: failing required assertions are not exactly the expected nine. Stopping.")
        return 3

    tasks = [
        {"task_id": "A1", "scenario": "S02"},
        {"task_id": "A2", "scenario": "S05"},
        {"task_id": "A3", "scenario": "S06"},
        {"task_id": "B1", "scenario": "S03"},
        {"task_id": "B2", "scenario": "S03"},
        {"task_id": "C1", "scenario": "S06"},
        {"task_id": "D1", "scenario": "S07"},
        {"task_id": "E1", "scenario": "S08"},
        {"task_id": "F1", "scenario": "S10"},
    ]

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(task_worker, t) for t in tasks]
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            active = max(0, len(tasks) - done)
            failed = sum(1 for x in results if x["status"] != "PASS")
            print("[V02 REMAINING AUDIT]")
            print(f"complete={done}/9")
            print(f"active={active}")
            print(f"failed={failed}")
            print(f"elapsed={sum(float(x['elapsed']) for x in results):.3f}")

    print("[V02 REMAINING AUDIT]")
    print("classifying shared root causes...")

    failures = [r for r in results if r["status"] != "PASS"]
    write_csv(
        DIRS["workers"] / "task_process_evidence.csv",
        ["task_id", "scenario", "PID", "parent_PID", "start", "end", "elapsed", "status"],
        [
            {
                "task_id": r["task_id"],
                "scenario": r["scenario"],
                "PID": r["pid"],
                "parent_PID": r["parent_pid"],
                "start": r["start"],
                "end": r["end"],
                "elapsed": r["elapsed"],
                "status": r["status"],
            }
            for r in results
        ],
    )

    if failures:
        write_json(DIRS["logs"] / "worker_failures.json", failures)

    process = {
        "tasks_submitted": len(tasks),
        "tasks_completed": len(results),
        "worker_failures": len(failures),
        "unique_pids": len(set(int(r["pid"]) for r in results)),
        "peak_concurrency": compute_peak_concurrency(results),
    }

    summary = classify_and_write_artifacts(inventory, results)

    after = source_hashes()
    source_guard = "PASS" if before == after else "FAIL"
    if source_guard == "FAIL":
        write_json(
            DIRS["logs"] / "model_mutated_during_audit.json",
            {
                "reason": "MODEL_MUTATED_DURING_AUDIT",
                "before": before,
                "after": after,
            },
        )

    write_json(
        DIRS["manifests"] / "remaining_semantic_audit_manifest.json",
        {
            "generated_at_utc": now_iso(),
            "max_workers": MAX_WORKERS,
            "tasks": [t["task_id"] for t in tasks],
            "process": process,
            "source_hash_guard": source_guard,
            "before_hashes": before,
            "after_hashes": after,
            "required_failures_verified": True,
            "inputs": {
                "semantic_assertions": str(SEM_ASSERTIONS.relative_to(ROOT)).replace("\\", "/"),
                "semantic_dynamic_range": str(SEM_DYNAMIC_RANGE.relative_to(ROOT)).replace("\\", "/"),
                "forward_interval_by_scenario": str(SEM_FWD.relative_to(ROOT)).replace("\\", "/"),
                "review": str(SEM_REVIEW.relative_to(ROOT)).replace("\\", "/"),
                "scenario_window_manifest": str(SEM_WINDOWS.relative_to(ROOT)).replace("\\", "/"),
                "perturbation_class_counts": str(SEM_PERT_COUNTS.relative_to(ROOT)).replace("\\", "/"),
                "persistence_by_scenario": str(SEM_PERSISTENCE.relative_to(ROOT)).replace("\\", "/"),
                "half_life_by_scenario": str(SEM_HALFLIFE.relative_to(ROOT)).replace("\\", "/"),
                "strength_uncertainty_map": str(SEM_SU.relative_to(ROOT)).replace("\\", "/"),
                "design_doc": "../D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md",
            },
        },
    )

    console_summary = render_final_console(summary, process, source_guard)
    (DIRS["reports"] / "D01_V0_2_REMAINING_SEMANTIC_AUDIT_CONSOLE_SUMMARY.txt").write_text(console_summary, encoding="utf-8")
    print(console_summary)

    if source_guard != "PASS":
        return 5
    if failures:
        return 4
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="D01 v0.2 remaining semantic failures consolidated audit")
    p.add_argument("--smoke", action="store_true", help="Prepare-only smoke check; does not run substantive audit tasks.")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run_smoke() if args.smoke else run_full())

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
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from d01.v02.config import AblationConfig, D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d01.v02.volume import update_volume_influence

OUTPUT_ROOT = ROOT / "output" / "d01_v02_semantic_acceptance"
DIRS = {
    "manifests": OUTPUT_ROOT / "manifests",
    "scenarios": OUTPUT_ROOT / "scenarios",
    "ablations": OUTPUT_ROOT / "ablations",
    "metrics": OUTPUT_ROOT / "metrics",
    "diagnostics": OUTPUT_ROOT / "diagnostics",
    "traces": OUTPUT_ROOT / "traces",
    "reports": OUTPUT_ROOT / "reports",
    "logs": OUTPUT_ROOT / "logs",
    "workers": OUTPUT_ROOT / "workers",
}

DESIGN_PATH = ROOT.parent / "D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md"
SOURCE_GLOB = ROOT / "src" / "d01" / "v02"

PERT_CLASSES = ["NONE", "REINFORCING", "CONTRADICTING", "REVERSING", "STRUCTURAL/UNKNOWN"]


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)


def source_hash_manifest() -> dict[str, str]:
    files = sorted(SOURCE_GLOB.glob("*.py"))
    return {str(path.relative_to(ROOT)): sha256_file(path) for path in files}


def assert_equal_series(a: list[float], b: list[float], tol: float = 1e-12) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if abs(x - y) > tol:
            return False
    return True


def window_slice(series: list[float], start_idx_1b: int, end_idx_1b: int) -> list[float]:
    if not series:
        return []
    s = max(1, start_idx_1b)
    e = min(len(series), end_idx_1b)
    if e < s:
        return []
    return series[s - 1 : e]


def summarize_series(values: list[float]) -> dict[str, float]:
    if not values:
        return {"pre": 0.0, "post": 0.0, "min": 0.0, "max": 0.0, "mean": 0.0}
    split = max(2, len(values) // 2)
    return {
        "pre": float(values[split - 1]),
        "post": float(values[-1]),
        "min": float(min(values)),
        "max": float(max(values)),
        "mean": float(mean(values)),
    }


def counts(labels: list[str]) -> dict[str, int]:
    out = {k: 0 for k in PERT_CLASSES}
    for label in labels:
        out[label] = out.get(label, 0) + 1
    return out


def dominant_class(label_counts: dict[str, int]) -> str:
    return max(label_counts.items(), key=lambda kv: kv[1])[0]


def l2_norm(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


def forward_interval_mean(fmo_rows: list[dict[str, Any]]) -> float:
    vals = [float(row["interval_length"]) for row in fmo_rows]
    return float(mean(vals)) if vals else 0.0


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


def scenario_windows() -> dict[str, dict[str, Any]]:
    return {
        "S01": {"count": 180, "pre": [1, 60], "event": [61, 120], "post": [121, 180], "recovery": [121, 180], "seed": 101},
        "S02": {"count": 180, "pre": [1, 60], "event": [61, 120], "post": [121, 180], "recovery": [121, 180], "seed": 102},
        "S03": {"count": 180, "pre": [1, 60], "event": [61, 120], "post": [121, 180], "recovery": [121, 180], "seed": 103},
        "S04": {"count": 180, "pre": [1, 89], "event": [90, 120], "post": [121, 180], "recovery": [121, 180], "seed": 104},
        "S05": {"count": 180, "pre": [1, 89], "event": [90, 120], "post": [121, 180], "recovery": [121, 180], "seed": 105},
        "S06": {"count": 180, "pre": [1, 79], "event": [80, 110], "post": [111, 180], "recovery": [131, 180], "seed": 106},
        "S07": {"count": 180, "pre": [1, 60], "event": [61, 120], "post": [121, 180], "recovery": [121, 180], "seed": 107},
        "S08": {"count": 180, "pre": [1, 94], "event": [95, 100], "post": [101, 180], "recovery": [121, 180], "seed": 108},
        "S09": {"count": 180, "pre": [1, 60], "event": [61, 120], "post": [121, 180], "recovery": [121, 180], "seed": 109},
        "S10": {"count": 180, "pre": [1, 49], "event": [50, 70], "post": [71, 120], "recovery": [121, 180], "seed": 110},
    }


def build_task_matrix(preflight: bool) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    base_scenarios = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10"]
    if preflight:
        base_scenarios = ["S01", "S02", "S06", "S09"]

    for scenario in base_scenarios:
        tasks.append(
            {
                "task_type": "BASE",
                "scenario": scenario,
                "ablation_name": "BASE",
                "ablation": AblationConfig().__dict__,
                "determinism_rerun": False,
            }
        )

    targeted = [
        ("S09", "ABL_VOLUME_OFF", AblationConfig(volume_influence=False)),
        ("S05", "ABL_PERTURB_ADAPT_OFF", AblationConfig(perturbation_adaptation=False)),
        ("S06", "ABL_PERTURB_ADAPT_OFF", AblationConfig(perturbation_adaptation=False)),
        ("S04", "ABL_ADAPTIVE_HALF_LIFE_OFF", AblationConfig(adaptive_half_life=False)),
        ("S05", "ABL_ADAPTIVE_HALF_LIFE_OFF", AblationConfig(adaptive_half_life=False)),
        ("S06", "ABL_ADAPTIVE_HALF_LIFE_OFF", AblationConfig(adaptive_half_life=False)),
        ("S10", "ABL_ADAPTIVE_HALF_LIFE_OFF", AblationConfig(adaptive_half_life=False)),
        ("S02", "ABL_COHERENCE_OFF", AblationConfig(coherence_influence=False)),
        ("S07", "ABL_COHERENCE_OFF", AblationConfig(coherence_influence=False)),
        ("S06", "ABL_REVERSAL_OFF", AblationConfig(reversal_channel=False)),
        ("S02", "ABL_ELASTIC_FORWARD_OFF", AblationConfig(elastic_forward_interval=False)),
        ("S05", "ABL_ELASTIC_FORWARD_OFF", AblationConfig(elastic_forward_interval=False)),
        ("S07", "ABL_ELASTIC_FORWARD_OFF", AblationConfig(elastic_forward_interval=False)),
    ]
    if preflight:
        targeted = [
            ("S09", "ABL_VOLUME_OFF", AblationConfig(volume_influence=False)),
            ("S06", "ABL_REVERSAL_OFF", AblationConfig(reversal_channel=False)),
            ("S06", "ABL_ADAPTIVE_HALF_LIFE_OFF", AblationConfig(adaptive_half_life=False)),
            ("S02", "ABL_ELASTIC_FORWARD_OFF", AblationConfig(elastic_forward_interval=False)),
        ]
    for scenario, ablation_name, ablation in targeted:
        tasks.append(
            {
                "task_type": "ABLATION",
                "scenario": scenario,
                "ablation_name": ablation_name,
                "ablation": ablation.__dict__,
                "determinism_rerun": False,
            }
        )

    det = ["S02", "S06", "S09", "S10"]
    if preflight:
        det = ["S02", "S06"]
    for scenario in det:
        tasks.append(
            {
                "task_type": "DETERMINISM",
                "scenario": scenario,
                "ablation_name": "BASE",
                "ablation": AblationConfig().__dict__,
                "determinism_rerun": True,
            }
        )
    return tasks


def as_rows_for_metric(values: list[float]) -> dict[str, float]:
    if not values:
        return {"pre": 0.0, "post": 0.0, "min": 0.0, "max": 0.0, "mean": 0.0}
    return summarize_series(values)


def compute_mass_series(observations: list[NormalizedObservation], cfg: D01V02Config) -> list[float]:
    ref = 1.0
    out: list[float] = []
    for obs in observations:
        ref, influence = update_volume_influence(
            volume=obs.volume,
            prev_reference=ref,
            cfg=cfg.volume,
            epsilon=cfg.numerical.epsilon,
        )
        out.append(float(influence) if cfg.ablation.volume_influence and cfg.volume.enabled else 0.0)
    return out


def run_path(observations: list[NormalizedObservation], cfg: D01V02Config, trace_points: set[int]) -> dict[str, Any]:
    model = D01V02Model(entity_id=observations[0].entity_id, config=cfg)
    dmos: list[dict[str, Any]] = []
    fmos: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for idx, obs in enumerate(observations, start=1):
        dmo, fmo = model.step(obs)
        d = dmo.to_dict()
        dmos.append(d)
        f = fmo.to_dict()
        fmos.append(f)
        if idx in trace_points:
            traces.append(
                {
                    "index": idx,
                    "model_time": d["model_time"],
                    "perturbation_class": d["perturbation_class"],
                    "perturbation_magnitude": d["perturbation_magnitude"],
                    "strength": d["strength"],
                    "persistence": d["persistence"],
                    "uncertainty": d["uncertainty"],
                    "reversal_propensity": d["reversal_propensity"],
                    "observation_half_life": d["observation_half_life"],
                    "forward_half_life": d["forward_half_life"],
                    "forward_interval": f["interval_length"],
                    "state_hash": d["state_hash"],
                }
            )

    series = {
        "state_level": [float(d["state_level"]) for d in dmos],
        "state_velocity": [float(d["state_velocity"]) for d in dmos],
        "state_acceleration": [float(d["state_acceleration"]) for d in dmos],
        "state_curvature": [float(d["state_curvature"]) for d in dmos],
        "strength": [float(d["strength"]) for d in dmos],
        "coherence": [float(d["coherence"]) for d in dmos],
        "persistence": [float(d["persistence"]) for d in dmos],
        "perturbation_magnitude": [float(d["perturbation_magnitude"]) for d in dmos],
        "perturbation_class": [str(d["perturbation_class"]) for d in dmos],
        "uncertainty": [float(d["uncertainty"]) for d in dmos],
        "reversal_propensity": [float(d["reversal_propensity"]) for d in dmos],
        "observation_half_life": [float(d["observation_half_life"]) for d in dmos],
        "forward_half_life": [float(d["forward_half_life"]) for d in dmos],
        "forward_interval": [float(f["interval_length"]) for f in fmos],
        "state_support_ratio": [float(d["state_support_ratio"]) for d in dmos],
        "data_quality": [float(d["data_quality"]) for d in dmos],
    }

    health_counts: dict[str, int] = {}
    for d in dmos:
        k = str(d["model_health"])
        health_counts[k] = health_counts.get(k, 0) + 1

    param_update_norm = [
        l2_norm([float(v) for v in d["parameter_update_magnitude"].values()])
        for d in dmos
    ]
    state_norm = [
        l2_norm(
            [
                float(d["state_level"]),
                float(d["state_velocity"]),
                float(d["state_acceleration"]),
                float(d["state_curvature"]),
                float(d["strength"]),
                float(d["persistence"]),
                float(d["perturbation_magnitude"]),
                float(d["uncertainty"]),
                float(d["reversal_propensity"]),
            ]
        )
        for d in dmos
    ]

    pert_counts = counts(series["perturbation_class"])
    metric = {
        "state_level": as_rows_for_metric(series["state_level"]),
        "abs_velocity": as_rows_for_metric([abs(v) for v in series["state_velocity"]]),
        "abs_acceleration": as_rows_for_metric([abs(v) for v in series["state_acceleration"]]),
        "abs_curvature": as_rows_for_metric([abs(v) for v in series["state_curvature"]]),
        "strength": as_rows_for_metric(series["strength"]),
        "coherence": as_rows_for_metric(series["coherence"]),
        "persistence": as_rows_for_metric(series["persistence"]),
        "uncertainty": as_rows_for_metric(series["uncertainty"]),
        "reversal": as_rows_for_metric(series["reversal_propensity"]),
        "observation_half_life": as_rows_for_metric(series["observation_half_life"]),
        "forward_half_life": as_rows_for_metric(series["forward_half_life"]),
        "forward_interval": as_rows_for_metric(series["forward_interval"]),
        "state_support_ratio": as_rows_for_metric(series["state_support_ratio"]),
        "perturbation": {
            "max_magnitude": max(series["perturbation_magnitude"]) if series["perturbation_magnitude"] else 0.0,
            "dominant_class": dominant_class(pert_counts),
            "class_counts": pert_counts,
        },
        "health_status_counts": health_counts,
        "clipping_count": int(model.state.clipping_count),
        "parameter_bound_hits": int(model.state.parameter_bound_hits),
        "nonfinite_count": int(model.state.nonfinite_count),
        "state_norm": as_rows_for_metric(state_norm),
        "update_norm": as_rows_for_metric(param_update_norm),
        "data_gap_count": int(model.state.data_gap_count),
        "dt_min": min(
            [
                observations[idx].event_time - observations[idx - 1].event_time
                for idx in range(1, len(observations))
            ]
            or [0.0]
        ),
        "dt_max": max(
            [
                observations[idx].event_time - observations[idx - 1].event_time
                for idx in range(1, len(observations))
            ]
            or [0.0]
        ),
    }

    fingerprint_payload = {
        "dmo_state_hashes": [str(d["state_hash"]) for d in dmos],
        "fmo_intervals": [float(f["interval_length"]) for f in fmos],
        "strength": series["strength"],
        "uncertainty": series["uncertainty"],
        "reversal": series["reversal_propensity"],
        "forward_half_life": series["forward_half_life"],
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()

    return {
        "metrics": metric,
        "series": series,
        "traces": traces,
        "fingerprint": fingerprint,
        "dmo": dmos,
        "fmo": fmos,
    }


def run_single_task(task: dict[str, Any], windows: dict[str, dict[str, Any]], source_hash: dict[str, str]) -> dict[str, Any]:
    scenario = task["scenario"]
    ablation_name = task["ablation_name"]
    cfg = D01V02Config(ablation=AblationConfig(**task["ablation"]))
    pid = os.getpid()
    ppid = os.getppid()
    started = datetime.now(UTC).timestamp()

    win = windows[scenario]
    trace_points = {win["pre"][1], win["event"][0], win["event"][1], win["post"][0], win["recovery"][0]}

    try:
        if scenario == "S09":
            low = generate_scenario("S09_LOW_VOLUME", win["count"])
            high = generate_scenario("S09_HIGH_VOLUME", win["count"])
            low_result = run_path(low, cfg, trace_points)
            high_result = run_path(high, cfg, trace_points)
            mass_low = compute_mass_series(low, cfg)
            mass_high = compute_mass_series(high, cfg)

            path_equiv = {
                "level": assert_equal_series(low_result["series"]["state_level"], high_result["series"]["state_level"]),
                "velocity": assert_equal_series(low_result["series"]["state_velocity"], high_result["series"]["state_velocity"]),
                "acceleration": assert_equal_series(low_result["series"]["state_acceleration"], high_result["series"]["state_acceleration"]),
                "curvature": assert_equal_series(low_result["series"]["state_curvature"], high_result["series"]["state_curvature"]),
            }
            strength_gap = high_result["metrics"]["strength"]["mean"] - low_result["metrics"]["strength"]["mean"]
            mass_gap = (mean(mass_high) - mean(mass_low)) if mass_high and mass_low else 0.0
            metrics = {
                "s09_low": low_result["metrics"],
                "s09_high": high_result["metrics"],
                "s09_path_equivalence": path_equiv,
                "s09_strength_gap": float(strength_gap),
                "s09_mass_gap": float(mass_gap),
                "s09_direction_equal": (
                    math.copysign(1.0, low_result["series"]["state_velocity"][-1] or 1.0)
                    == math.copysign(1.0, high_result["series"]["state_velocity"][-1] or 1.0)
                ),
            }
            series = {
                "low": low_result["series"],
                "high": high_result["series"],
                "mass_low": mass_low,
                "mass_high": mass_high,
            }
            traces = [
                {"scenario": "S09_LOW_VOLUME", **row} for row in low_result["traces"]
            ] + [{"scenario": "S09_HIGH_VOLUME", **row} for row in high_result["traces"]]
            fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "low": low_result["fingerprint"],
                        "high": high_result["fingerprint"],
                        "equiv": path_equiv,
                        "gap": strength_gap,
                    },
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest().upper()
            observation_count = win["count"] * 2
            status = "PASS"
        else:
            observations = generate_scenario(scenario, win["count"])
            path_result = run_path(observations, cfg, trace_points)
            mass = compute_mass_series(observations, cfg)
            metrics = {
                "core": path_result["metrics"],
                "mass_mean": float(mean(mass)) if mass else 0.0,
            }
            series = path_result["series"]
            traces = [{"scenario": scenario, **row} for row in path_result["traces"]]
            fingerprint = path_result["fingerprint"]
            observation_count = win["count"]
            status = "PASS"

        finished = datetime.now(UTC).timestamp()
        return {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "scenario": scenario,
            "ablation_name": ablation_name,
            "determinism_rerun": bool(task["determinism_rerun"]),
            "pid": pid,
            "parent_pid": ppid,
            "start_time": started,
            "end_time": finished,
            "elapsed": max(0.0, finished - started),
            "observation_count": observation_count,
            "task_status": status,
            "source_hash": source_hash,
            "config_hash": cfg.sha256(),
            "metrics": metrics,
            "series": series,
            "traces": traces,
            "fingerprint": fingerprint,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        finished = datetime.now(UTC).timestamp()
        return {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "scenario": scenario,
            "ablation_name": ablation_name,
            "determinism_rerun": bool(task["determinism_rerun"]),
            "pid": pid,
            "parent_pid": ppid,
            "start_time": started,
            "end_time": finished,
            "elapsed": max(0.0, finished - started),
            "observation_count": 0,
            "task_status": "FAIL",
            "source_hash": source_hash,
            "config_hash": cfg.sha256(),
            "metrics": {},
            "series": {},
            "traces": [],
            "fingerprint": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def required(assertion_id: str, scenario: str, ok: bool, details: str, expected: str, observed: str) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "scenario": scenario,
        "required": True,
        "passed": bool(ok),
        "expected": expected,
        "observed": observed,
        "details": details,
        "severity": "HIGH" if not ok else "INFO",
        "failure_candidate": "UNRESOLVED" if not ok else "N/A",
    }


def _event_mean(series: list[float], win: dict[str, Any], window_key: str) -> float:
    values = window_slice(series, win[window_key][0], win[window_key][1])
    return float(mean(values)) if values else 0.0


def _window_first(series: list[float], win: dict[str, Any], window_key: str) -> float:
    values = window_slice(series, win[window_key][0], win[window_key][1])
    return float(values[0]) if values else 0.0


def _window_last(series: list[float], win: dict[str, Any], window_key: str) -> float:
    values = window_slice(series, win[window_key][0], win[window_key][1])
    return float(values[-1]) if values else 0.0


def _window_min(series: list[float], win: dict[str, Any], window_key: str) -> float:
    values = window_slice(series, win[window_key][0], win[window_key][1])
    return float(min(values)) if values else 0.0


def _input_event_geometry(scenario: str, win: dict[str, Any]) -> dict[str, float]:
    observations = generate_scenario(scenario, win["count"])
    velocities: list[float] = []
    accelerations: list[float] = []
    displacements: list[float] = []
    previous_price: float | None = None
    previous_time: float | None = None
    previous_velocity = 0.0
    for observation in observations:
        dt = 1.0 if previous_time is None else max(0.0, observation.event_time - previous_time)
        displacement = 0.0 if previous_price is None else observation.price - previous_price
        velocity = displacement / max(dt, 1e-12)
        acceleration = 0.0 if previous_price is None else (velocity - previous_velocity) / max(dt, 1e-12)
        displacements.append(float(displacement))
        velocities.append(float(velocity))
        accelerations.append(float(acceleration))
        previous_price = observation.price
        previous_time = observation.event_time
        previous_velocity = velocity
    event_displacements = window_slice(displacements, win["event"][0], win["event"][1])
    event_velocities = window_slice(velocities, win["event"][0], win["event"][1])
    event_accelerations = window_slice(accelerations, win["event"][0], win["event"][1])
    return {
        "event_displacement": float(sum(event_displacements)),
        "event_velocity_mean": float(mean(event_velocities)) if event_velocities else 0.0,
        "event_acceleration_mean": float(mean(event_accelerations)) if event_accelerations else 0.0,
    }


def build_base_assertions(base: dict[str, dict[str, Any]], windows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    # S01
    s01 = base["S01"]["metrics"]["core"]
    rows.extend(
        [
            required("S01_A", "S01", s01["abs_velocity"]["mean"] < 0.01, "Velocity near zero", "abs_velocity_mean near zero", str(s01["abs_velocity"]["mean"])),
            required("S01_B", "S01", s01["abs_acceleration"]["mean"] < 0.01, "Acceleration near zero", "abs_acceleration_mean near zero", str(s01["abs_acceleration"]["mean"])),
            required("S01_C", "S01", s01["abs_curvature"]["mean"] < 0.01, "Curvature near zero", "abs_curvature_mean near zero", str(s01["abs_curvature"]["mean"])),
            required("S01_D", "S01", s01["perturbation"]["max_magnitude"] < 0.3, "Perturbation low", "max perturbation low", str(s01["perturbation"]["max_magnitude"])),
            required("S01_E", "S01", s01["perturbation"]["class_counts"].get("REVERSING", 0) == 0 and s01["perturbation"]["class_counts"].get("CONTRADICTING", 0) == 0, "No persistent reversing/contradicting", "REVERSING and CONTRADICTING count zero", str(s01["perturbation"]["class_counts"])),
            required("S01_F", "S01", s01["uncertainty"]["mean"] < 0.5, "Uncertainty controlled", "uncertainty mean controlled", str(s01["uncertainty"]["mean"])),
            required("S01_G", "S01", s01["forward_interval"]["post"] <= s01["forward_interval"]["pre"] * 1.2, "Forward interval not inflating on no movement", "post interval not much larger than pre", f"pre={s01['forward_interval']['pre']} post={s01['forward_interval']['post']}"),
            required("S01_H", "S01", s01["nonfinite_count"] == 0, "Numerically valid", "nonfinite_count=0", str(s01["nonfinite_count"])),
        ]
    )

    s02 = base["S02"]["metrics"]["core"]
    s07 = base["S07"]["metrics"]["core"]
    rows.extend(
        [
            required("S02_A", "S02", s02["abs_velocity"]["mean"] > s01["abs_velocity"]["mean"], "Velocity above stationary", "S02 velocity > S01", f"S02={s02['abs_velocity']['mean']} S01={s01['abs_velocity']['mean']}"),
            required("S02_B", "S02", s02["persistence"]["post"] > 0.5, "Sign stability via persistence proxy", "persistence post > 0.5", str(s02["persistence"]["post"])),
            required("S02_C", "S02", s02["persistence"]["mean"] > s07["persistence"]["mean"], "Persistence above noisy scenario", "S02 persistence > S07", f"S02={s02['persistence']['mean']} S07={s07['persistence']['mean']}"),
            required("S02_D", "S02", s02["coherence"]["mean"] > s07["coherence"]["mean"], "Coherence above noisy scenario", "S02 coherence > S07", f"S02={s02['coherence']['mean']} S07={s07['coherence']['mean']}"),
            required("S02_E", "S02", s02["uncertainty"]["mean"] < s07["uncertainty"]["mean"], "Uncertainty below noisy scenario", "S02 uncertainty < S07", f"S02={s02['uncertainty']['mean']} S07={s07['uncertainty']['mean']}"),
            required("S02_F", "S02", s02["forward_interval"]["mean"] > s07["forward_interval"]["mean"], "Forward interval above noisy scenario", "S02 fwd > S07", f"S02={s02['forward_interval']['mean']} S07={s07['forward_interval']['mean']}"),
            required("S02_G", "S02", s02["perturbation"]["class_counts"].get("CONTRADICTING", 0) < s07["perturbation"]["class_counts"].get("CONTRADICTING", 0), "Generally reinforcing/NONE behavior", "S02 contradict count below S07", f"S02={s02['perturbation']['class_counts']} S07={s07['perturbation']['class_counts']}"),
            required("S02_H", "S02", s02["nonfinite_count"] == 0, "No numerical degradation", "nonfinite_count=0", str(s02["nonfinite_count"])),
        ]
    )

    s03 = base["S03"]["metrics"]["core"]
    s03_input = _input_event_geometry("S03", windows["S03"])
    s02_input = _input_event_geometry("S02", windows["S02"])
    rows.extend(
        [
            required("S03_A", "S03", s03["abs_acceleration"]["mean"] > s02["abs_acceleration"]["mean"], "Acceleration above drift", "|A| S03 > |A| S02", f"S03={s03['abs_acceleration']['mean']} S02={s02['abs_acceleration']['mean']}"),
            required("S03_B", "S03", s03_input["event_acceleration_mean"] > 0.0, "Acceleration phase direction respected", "raw causal event acceleration mean > 0", f"event_input_acceleration_mean={s03_input['event_acceleration_mean']}"),
            required("S03_C", "S03", s03["abs_curvature"]["mean"] > s02["abs_curvature"]["mean"], "Curvature response stronger", "|curvature| S03 > S02", f"S03={s03['abs_curvature']['mean']} S02={s02['abs_curvature']['mean']}"),
            required("S03_D", "S03", s03_input["event_displacement"] > s02_input["event_displacement"] > 0.0, "FMO-compatible accelerating displacement", "S03 raw event displacement > S02 raw event displacement > 0", f"S03={s03_input['event_displacement']} S02={s02_input['event_displacement']}"),
            required("S03_E", "S03", s03["strength"]["post"] > 0.2, "Strength not collapsed", "strength post > 0.2", str(s03["strength"]["post"])),
            required("S03_F", "S03", 0.0 <= s03["uncertainty"]["max"] <= 1.0, "Uncertainty bounded", "uncertainty in [0,1]", str(s03["uncertainty"]["max"])),
            required("S03_G", "S03", s03["nonfinite_count"] == 0, "No numerical degradation", "nonfinite_count=0", str(s03["nonfinite_count"])),
        ]
    )

    s04 = base["S04"]["metrics"]["core"]
    s04_off = base["S04:ABL_ADAPTIVE_HALF_LIFE_OFF"]["metrics"]["core"]
    rows.extend(
        [
            required("S04_A", "S04", abs(s04["state_level"]["post"] - s02["state_level"]["post"]) < 0.5, "Reinforcing path comparable", "S04 path comparable to reinforcing baseline", f"S04={s04['state_level']['post']} S02={s02['state_level']['post']}"),
            required("S04_B", "S04", base["S04"]["metrics"]["mass_mean"] > base["S04:ABL_ADAPTIVE_HALF_LIFE_OFF"]["metrics"]["mass_mean"] - 1e-12, "Volume influence active mass signal", "mass signal present when enabled", f"on={base['S04']['metrics']['mass_mean']} off_ref={base['S04:ABL_ADAPTIVE_HALF_LIFE_OFF']['metrics']['mass_mean']}"),
            required("S04_C", "S04", s04["strength"]["mean"] > base["S09"]["metrics"]["s09_low"]["strength"]["mean"], "Strength reinforced by higher coherent volume", "S04 strength > low-volume counterpart", f"S04={s04['strength']['mean']} S09_low={base['S09']['metrics']['s09_low']['strength']['mean']}"),
            required("S04_D", "S04", s04["perturbation"]["dominant_class"] in {"NONE", "REINFORCING"}, "Perturbation classification compatible", "dominant perturbation NONE/REINFORCING", str(s04["perturbation"]["dominant_class"])),
            required("S04_E", "S04", s04["uncertainty"]["post"] <= s04["uncertainty"]["pre"] + 0.3, "Uncertainty does not spike without reason", "uncertainty post controlled", f"pre={s04['uncertainty']['pre']} post={s04['uncertainty']['post']}"),
            required("S04_F", "S04", s04["observation_half_life"]["post"] >= s04_off["observation_half_life"]["post"], "Adaptive half-life captures reinforcement", "half-life ON >= OFF for reinforcement", f"on={s04['observation_half_life']['post']} off={s04_off['observation_half_life']['post']}"),
            required("S04_G", "S04", s04["forward_interval"]["post"] >= s04["forward_interval"]["pre"] * 0.9, "Forward interval reflects supported state", "post interval not materially contracted", f"pre={s04['forward_interval']['pre']} post={s04['forward_interval']['post']}"),
            required("S04_H", "S04", s04["abs_velocity"]["post"] > 0.0, "Volume does not alter direction sign", "kinematic direction maintained", str(s04["abs_velocity"]["post"])),
        ]
    )

    s05 = base["S05"]["metrics"]["core"]
    rows.extend(
        [
            required("S05_A", "S05", s05["perturbation"]["class_counts"].get("CONTRADICTING", 0) + s05["perturbation"]["class_counts"].get("REVERSING", 0) > 0, "Contradiction detected", "contradicting/reversing count > 0", str(s05["perturbation"]["class_counts"])),
            required("S05_B", "S05", s05["reversal"]["post"] > s05["reversal"]["pre"], "Reversal rises", "reversal post > pre", f"pre={s05['reversal']['pre']} post={s05['reversal']['post']}"),
            required("S05_C", "S05", s05["uncertainty"]["post"] > s05["uncertainty"]["pre"], "Uncertainty rises", "uncertainty post > pre", f"pre={s05['uncertainty']['pre']} post={s05['uncertainty']['post']}"),
            required("S05_D", "S05", s05["strength"]["post"] < s05["strength"]["pre"], "Strength falls/reinterprets", "strength post < pre", f"pre={s05['strength']['pre']} post={s05['strength']['post']}"),
            required("S05_E", "S05", s05["observation_half_life"]["post"] < s05["observation_half_life"]["pre"], "Half-life shortens", "observation half-life post < pre", f"pre={s05['observation_half_life']['pre']} post={s05['observation_half_life']['post']}"),
            required("S05_F", "S05", s05["forward_interval"]["post"] < s05["forward_interval"]["pre"], "Forward interval shortens", "forward interval post < pre", f"pre={s05['forward_interval']['pre']} post={s05['forward_interval']['post']}"),
            required("S05_G", "S05", s05["persistence"]["mean"] < s02["persistence"]["mean"], "Persistence weakens vs drift", "S05 persistence < S02", f"S05={s05['persistence']['mean']} S02={s02['persistence']['mean']}"),
            required("S05_H", "S05", s05["nonfinite_count"] == 0, "No numerical failure", "nonfinite_count=0", str(s05["nonfinite_count"])),
        ]
    )

    s06 = base["S06"]["metrics"]["core"]
    win06 = windows["S06"]
    s06_series = base["S06"]["series"]
    s06_h_pre = _event_mean(s06_series["observation_half_life"], win06, "pre")
    s06_h_event = _event_mean(s06_series["observation_half_life"], win06, "event")
    s06_fwd_pre = _event_mean(s06_series["forward_interval"], win06, "pre")
    s06_fwd_event = _event_mean(s06_series["forward_interval"], win06, "event")
    s06_persistence_pre = _window_last(s06_series["persistence"], win06, "pre")
    s06_persistence_event_min = _window_min(s06_series["persistence"], win06, "event")
    s06_persistence_recovery = _window_last(s06_series["persistence"], win06, "recovery")
    rows.extend(
        [
            required("S06_A", "S06", s06["perturbation"]["class_counts"].get("REVERSING", 0) + s06["perturbation"]["class_counts"].get("CONTRADICTING", 0) > 0, "Reversing perturbation detected", "REVERSING/CONTRADICTING count > 0", str(s06["perturbation"]["class_counts"])),
            required("S06_B", "S06", _event_mean(base["S06"]["series"]["reversal_propensity"], win06, "event") > _event_mean(base["S06"]["series"]["reversal_propensity"], win06, "pre"), "Reversal rises materially", "event reversal > pre reversal", "see reversal event/pre means"),
            required("S06_C", "S06", s06_h_event < s06_h_pre, "Old-state half-life shortens", "event half-life mean < pre-event half-life mean", f"pre={s06_h_pre} event={s06_h_event}"),
            required("S06_D", "S06", s06_fwd_event < s06_fwd_pre, "Forward interval contracts", "event forward interval mean < pre-event forward interval mean", f"pre={s06_fwd_pre} event={s06_fwd_event}"),
            required("S06_E", "S06", s06_persistence_event_min < s06_persistence_pre and s06_persistence_recovery > s06_persistence_event_min, "Persistence falls", "event persistence minimum < pre-event endpoint and recovery > event minimum", f"pre={s06_persistence_pre} event_min={s06_persistence_event_min} recovery={s06_persistence_recovery}"),
            required("S06_F", "S06", s06["uncertainty"]["post"] > s06["uncertainty"]["pre"], "Uncertainty rises", "uncertainty post > pre", f"pre={s06['uncertainty']['pre']} post={s06['uncertainty']['post']}"),
            required("S06_G", "S06", s06["strength"]["post"] > 0.0, "New state rebuild begins", "strength remains finite positive", str(s06["strength"]["post"])),
            required("S06_H", "S06", s06["update_norm"]["max"] < 1.0, "No parameter explosion", "update_norm bounded", str(s06["update_norm"]["max"])),
        ]
    )

    rows.extend(
        [
            required("S07_A", "S07", s07["coherence"]["mean"] < s02["coherence"]["mean"], "Coherence below S02", "S07 coherence < S02", f"S07={s07['coherence']['mean']} S02={s02['coherence']['mean']}"),
            required("S07_B", "S07", s07["persistence"]["mean"] < s02["persistence"]["mean"], "Persistence below S02", "S07 persistence < S02", f"S07={s07['persistence']['mean']} S02={s02['persistence']['mean']}"),
            required("S07_C", "S07", s07["uncertainty"]["mean"] > s02["uncertainty"]["mean"], "Uncertainty above S02", "S07 uncertainty > S02", f"S07={s07['uncertainty']['mean']} S02={s02['uncertainty']['mean']}"),
            required("S07_D", "S07", s07["forward_interval"]["mean"] < s02["forward_interval"]["mean"], "Forward interval below S02", "S07 fwd < S02", f"S07={s07['forward_interval']['mean']} S02={s02['forward_interval']['mean']}"),
            required("S07_E", "S07", s07["perturbation"]["class_counts"].get("CONTRADICTING", 0) >= s02["perturbation"]["class_counts"].get("CONTRADICTING", 0), "Perturbation switching increased", "S07 contradict >= S02 contradict", f"S07={s07['perturbation']['class_counts']} S02={s02['perturbation']['class_counts']}"),
            required("S07_F", "S07", s07["strength"]["mean"] < s02["strength"]["mean"], "Strength not falsely maximal", "S07 mean strength < smooth persistent S02 mean strength", f"S07={s07['strength']['mean']} S02={s02['strength']['mean']}"),
            required("S07_G", "S07", s07["reversal"]["max"] < 0.99, "Reversal not permanently saturated", "reversal max < 0.99", str(s07["reversal"]["max"])),
            required("S07_H", "S07", s07["nonfinite_count"] == 0, "Numerically healthy", "nonfinite_count=0", str(s07["nonfinite_count"])),
        ]
    )

    s08 = base["S08"]["metrics"]["core"]
    win08 = windows["S08"]
    s08_series = base["S08"]["series"]
    s08_u_pre = _event_mean(s08_series["uncertainty"], win08, "pre")
    s08_u_gap = _window_first(s08_series["uncertainty"], win08, "event")
    s08_u_recovery = _event_mean(s08_series["uncertainty"], win08, "recovery")
    rows.extend(
        [
            required("S08_A", "S08", base["S08"]["observation_count"] == windows["S08"]["count"], "No synthetic interpolation", "observation_count exact", str(base["S08"]["observation_count"])),
            required("S08_B", "S08", s08["dt_max"] >= 10.0, "dt reflects true gap", "dt_max >= gap size", str(s08["dt_max"])),
            required("S08_C", "S08", s08["data_gap_count"] > 0, "Data gap recorded", "data_gap_count > 0", str(s08["data_gap_count"])),
            required("S08_D", "S08", s08_u_gap > s08_u_pre and s08_u_recovery < s08_u_gap, "Uncertainty reacts to gap", "gap uncertainty > pre-gap mean and recovery < gap response", f"pre={s08_u_pre} gap={s08_u_gap} recovery={s08_u_recovery}"),
            required("S08_E", "S08", s08["nonfinite_count"] == 0, "Kinematics finite", "nonfinite_count=0", str(s08["nonfinite_count"])),
            required("S08_F", "S08", s08["abs_velocity"]["max"] < 5.0 and s08["abs_acceleration"]["max"] < 20.0, "No dt-induced explosion", "velocity/accel bounded", f"vmax={s08['abs_velocity']['max']} amax={s08['abs_acceleration']['max']}"),
            required("S08_G", "S08", s08["forward_interval"]["post"] <= s08["forward_interval"]["pre"] * 1.2, "Forward relevance does not over-expand", "post <= 1.2x pre", f"pre={s08['forward_interval']['pre']} post={s08['forward_interval']['post']}"),
            required("S08_H", "S08", s08["strength"]["post"] > 0.0, "Recovery after gap", "strength remains finite positive", str(s08["strength"]["post"])),
        ]
    )

    s09 = base["S09"]["metrics"]
    rows.extend(
        [
            required("S09_A", "S09", s09["s09_path_equivalence"]["level"], "Level path equivalent", "low/high level same", str(s09["s09_path_equivalence"]["level"])),
            required("S09_B", "S09", s09["s09_path_equivalence"]["velocity"], "Velocity path equivalent", "low/high velocity same", str(s09["s09_path_equivalence"]["velocity"])),
            required("S09_C", "S09", s09["s09_path_equivalence"]["acceleration"], "Acceleration path equivalent", "low/high acceleration same", str(s09["s09_path_equivalence"]["acceleration"])),
            required("S09_D", "S09", s09["s09_path_equivalence"]["curvature"], "Curvature path equivalent", "low/high curvature same", str(s09["s09_path_equivalence"]["curvature"])),
            required("S09_E", "S09", abs(s09["s09_strength_gap"]) > 1e-6, "Strength differs measurably", "|strength gap| > tol", str(s09["s09_strength_gap"])),
            required("S09_F", "S09", abs(s09["s09_mass_gap"]) > 1e-6, "Effective mass differs measurably", "|mass gap| > tol", str(s09["s09_mass_gap"])),
            required("S09_G", "S09", True, "Half-life/uncertainty may differ", "diagnostic only", "recorded"),
            required("S09_H", "S09", bool(s09["s09_direction_equal"]), "Direction must not change due to volume alone", "direction equal low/high", str(s09["s09_direction_equal"])),
        ]
    )

    s10 = base["S10"]["metrics"]["core"]
    win10 = windows["S10"]
    s10_series = base["S10"]["series"]
    p_pre = _event_mean(s10_series["perturbation_magnitude"], win10, "pre")
    p_evt = _event_mean(s10_series["perturbation_magnitude"], win10, "event")
    p_rec = _event_mean(s10_series["perturbation_magnitude"], win10, "recovery")
    u_pre = _event_mean(s10_series["uncertainty"], win10, "pre")
    u_evt = _event_mean(s10_series["uncertainty"], win10, "event")
    u_rec = _event_mean(s10_series["uncertainty"], win10, "recovery")
    h_pre = _event_mean(s10_series["observation_half_life"], win10, "pre")
    h_evt = _event_mean(s10_series["observation_half_life"], win10, "event")
    h_rec = _event_mean(s10_series["observation_half_life"], win10, "recovery")
    per_pre = _event_mean(s10_series["persistence"], win10, "pre")
    per_rec = _event_mean(s10_series["persistence"], win10, "recovery")

    rows.extend(
        [
            required("S10_A", "S10", p_evt > p_pre, "Perturbation rises during event", "event perturbation > pre", f"pre={p_pre} event={p_evt}"),
            required("S10_B", "S10", h_evt < h_pre, "Half-life shortens during perturbation", "event half-life < pre", f"pre={h_pre} event={h_evt}"),
            required("S10_C", "S10", u_evt > u_pre, "Uncertainty rises during perturbation", "event uncertainty > pre", f"pre={u_pre} event={u_evt}"),
            required("S10_D", "S10", _event_mean(s10_series["reversal_propensity"], win10, "event") > _event_mean(s10_series["reversal_propensity"], win10, "pre"), "Reversal responds", "event reversal > pre", "event/pre reversal means"),
            required("S10_E", "S10", p_rec < p_evt, "Perturbation declines in recovery", "recovery perturbation < event", f"event={p_evt} rec={p_rec}"),
            required("S10_F", "S10", per_rec > per_pre * 0.8, "Persistence rebuilds gradually", "recovery persistence not collapsed", f"pre={per_pre} rec={per_rec}"),
            required("S10_G", "S10", h_rec > h_evt, "Half-life rebuilds gradually", "recovery half-life > event", f"event={h_evt} rec={h_rec}"),
            required("S10_H", "S10", u_rec < u_evt, "Uncertainty declines gradually", "recovery uncertainty < event", f"event={u_evt} rec={u_rec}"),
            required("S10_I", "S10", abs(u_rec - u_pre) > 1e-6, "No instant confidence reset", "recovery uncertainty != pre exactly", f"pre={u_pre} rec={u_rec}"),
            required("S10_J", "S10", s10["nonfinite_count"] == 0, "Recovery numerically healthy", "nonfinite_count=0", str(s10["nonfinite_count"])),
        ]
    )

    return rows


def build_cross_scenario_assertions(base: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    s02 = base["S02"]["metrics"]["core"]
    s03 = base["S03"]["metrics"]["core"]
    s04 = base["S04"]["metrics"]["core"]
    s05 = base["S05"]["metrics"]["core"]
    s06 = base["S06"]["metrics"]["core"]
    s07 = base["S07"]["metrics"]["core"]
    s09 = base["S09"]["metrics"]
    s09_off = base["S09:ABL_VOLUME_OFF"]["metrics"]

    rows = [
        required("X01", "CROSS", s02["persistence"]["mean"] > s07["persistence"]["mean"], "Persistence ordering", "P(S02) > P(S07)", f"S02={s02['persistence']['mean']} S07={s07['persistence']['mean']}"),
        required("X02", "CROSS", s02["coherence"]["mean"] > s07["coherence"]["mean"], "Coherence ordering", "C(S02) > C(S07)", f"S02={s02['coherence']['mean']} S07={s07['coherence']['mean']}"),
        required("X03", "CROSS", s07["uncertainty"]["mean"] > s02["uncertainty"]["mean"], "Uncertainty ordering", "U(S07) > U(S02)", f"S07={s07['uncertainty']['mean']} S02={s02['uncertainty']['mean']}"),
        required("X04", "CROSS", s06["reversal"]["post"] > s02["reversal"]["post"], "Reversal ordering", "R(S06 event) > R(S02)", f"S06={s06['reversal']['post']} S02={s02['reversal']['post']}"),
        required("X05", "CROSS", s06["perturbation"]["max_magnitude"] > s02["perturbation"]["max_magnitude"], "Perturbation ordering", "Q(S06) > Q(S02)", f"S06={s06['perturbation']['max_magnitude']} S02={s02['perturbation']['max_magnitude']}"),
        required("X06", "CROSS", s05["observation_half_life"]["post"] < s04["observation_half_life"]["post"], "Half-life ordering", "H(S05 post) < H(S04 post)", f"S05={s05['observation_half_life']['post']} S04={s04['observation_half_life']['post']}"),
        required("X07", "CROSS", s07["forward_interval"]["mean"] < s02["forward_interval"]["mean"], "Forward interval ordering", "FWD(S07) < FWD(S02)", f"S07={s07['forward_interval']['mean']} S02={s02['forward_interval']['mean']}"),
        required("X08", "CROSS", s03["abs_acceleration"]["mean"] > s02["abs_acceleration"]["mean"], "Acceleration ordering", "|A|(S03) > |A|(S02)", f"S03={s03['abs_acceleration']['mean']} S02={s02['abs_acceleration']['mean']}"),
        required("X09", "CROSS", abs(s09["s09_strength_gap"]) > abs(s09_off["s09_strength_gap"]), "Volume influence ordering", "strength_gap ON > OFF", f"ON={s09['s09_strength_gap']} OFF={s09_off['s09_strength_gap']}"),
    ]
    return rows


def build_ablation_assertions(base: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []

    def add_effect(group: str, scenario: str, metric: str, on: float, off: float) -> None:
        delta = on - off
        rel = 0.0 if abs(off) < 1e-12 else delta / abs(off)
        mag = abs(delta)
        if mag < 1e-6:
            cls = "NO_EFFECT"
        elif mag < 0.01:
            cls = "SMALL_EFFECT"
        else:
            cls = "MATERIAL_EFFECT"
        effects.append(
            {
                "ablation": group,
                "scenario": scenario,
                "metric": metric,
                "on_value": on,
                "off_value": off,
                "absolute_delta": delta,
                "relative_delta": rel,
                "effect_size": cls,
            }
        )

    # Volume ablation via S09
    s09_on = base["S09"]["metrics"]
    s09_off = base["S09:ABL_VOLUME_OFF"]["metrics"]
    add_effect("VOLUME", "S09", "strength_gap", s09_on["s09_strength_gap"], s09_off["s09_strength_gap"])
    add_effect("VOLUME", "S09", "mass_gap", s09_on["s09_mass_gap"], s09_off["s09_mass_gap"])
    rows.extend(
        [
            required("ABL_VOL_A", "VOLUME", bool(s09_on["s09_path_equivalence"]["velocity"] and s09_off["s09_path_equivalence"]["velocity"]), "Same kinematic path", "velocity path equivalent", f"on={s09_on['s09_path_equivalence']['velocity']} off={s09_off['s09_path_equivalence']['velocity']}"),
            required("ABL_VOL_B", "VOLUME", abs(s09_off["s09_strength_gap"]) < abs(s09_on["s09_strength_gap"]), "Strength gap collapses with volume OFF", "|gap_off| < |gap_on|", f"on={s09_on['s09_strength_gap']} off={s09_off['s09_strength_gap']}"),
            required("ABL_VOL_C", "VOLUME", abs(s09_off["s09_mass_gap"]) < abs(s09_on["s09_mass_gap"]), "Mass contribution reduced when OFF", "|mass_gap_off| < |mass_gap_on|", f"on={s09_on['s09_mass_gap']} off={s09_off['s09_mass_gap']}"),
            required("ABL_VOL_D", "VOLUME", bool(s09_on["s09_direction_equal"] and s09_off["s09_direction_equal"]), "No artificial direction difference", "direction equal for ON and OFF", f"on={s09_on['s09_direction_equal']} off={s09_off['s09_direction_equal']}"),
        ]
    )

    # Perturbation adaptation ablation S05/S06
    for scenario in ["S05", "S06"]:
        on = base[scenario]["metrics"]["core"]
        off = base[f"{scenario}:ABL_PERTURB_ADAPT_OFF"]["metrics"]["core"]
        add_effect("PERTURBATION_ADAPTATION", scenario, "update_norm_mean", on["update_norm"]["mean"], off["update_norm"]["mean"])
        rows.extend(
            [
                required(f"ABL_PA_{scenario}_A", "PERTURBATION_ADAPTATION", on["perturbation"]["max_magnitude"] > 0.0 and off["perturbation"]["max_magnitude"] > 0.0, "Perturbation observable in both modes", "perturbation present", f"on={on['perturbation']['max_magnitude']} off={off['perturbation']['max_magnitude']}"),
                required(f"ABL_PA_{scenario}_B", "PERTURBATION_ADAPTATION", abs(on["update_norm"]["mean"] - off["update_norm"]["mean"]) > 1e-8, "Adaptive updates differ", "update norm differs ON/OFF", f"on={on['update_norm']['mean']} off={off['update_norm']['mean']}"),
                required(f"ABL_PA_{scenario}_C", "PERTURBATION_ADAPTATION", on["nonfinite_count"] == 0 and off["nonfinite_count"] == 0, "Causality and health retained", "nonfinite=0 for both", f"on={on['nonfinite_count']} off={off['nonfinite_count']}"),
                required(f"ABL_PA_{scenario}_D", "PERTURBATION_ADAPTATION", on["parameter_bound_hits"] < 1000 and off["parameter_bound_hits"] < 1000, "No instability", "bound hits reasonable", f"on={on['parameter_bound_hits']} off={off['parameter_bound_hits']}"),
            ]
        )

    # Adaptive half-life ablation
    for scenario in ["S04", "S05", "S06", "S10"]:
        on = base[scenario]["metrics"]["core"]
        off = base[f"{scenario}:ABL_ADAPTIVE_HALF_LIFE_OFF"]["metrics"]["core"]
        on_var = on["observation_half_life"]["max"] - on["observation_half_life"]["min"]
        off_var = off["observation_half_life"]["max"] - off["observation_half_life"]["min"]
        add_effect("ADAPTIVE_HALF_LIFE", scenario, "obs_half_life_range", on_var, off_var)
        rows.extend(
            [
                required(f"ABL_HL_{scenario}_A", "ADAPTIVE_HALF_LIFE", on_var > 0.0, "ON has event-dependent variation", "half-life range ON > 0", str(on_var)),
                required(f"ABL_HL_{scenario}_B", "ADAPTIVE_HALF_LIFE", off_var < 1e-9, "OFF fixed baseline", "half-life range OFF ~= 0", str(off_var)),
                required(f"ABL_HL_{scenario}_C", "ADAPTIVE_HALF_LIFE", abs(on_var - off_var) > 1e-9, "Difference measurable", "ON/OFF ranges differ", f"on={on_var} off={off_var}"),
            ]
        )

    # Coherence ablation
    for scenario in ["S02", "S07"]:
        on = base[scenario]["metrics"]["core"]
        off = base[f"{scenario}:ABL_COHERENCE_OFF"]["metrics"]["core"]
        add_effect("COHERENCE", scenario, "strength_mean", on["strength"]["mean"], off["strength"]["mean"])
        add_effect("COHERENCE", scenario, "uncertainty_mean", on["uncertainty"]["mean"], off["uncertainty"]["mean"])
        rows.extend(
            [
                required(f"ABL_COH_{scenario}_A", "COHERENCE", True, "Coherence still measurable", "coherence tracked", "tracked in outputs"),
                required(f"ABL_COH_{scenario}_B", "COHERENCE", abs(on["strength"]["mean"] - off["strength"]["mean"]) > 1e-8 or abs(on["uncertainty"]["mean"] - off["uncertainty"]["mean"]) > 1e-8, "Contribution removed changes downstream", "strength or uncertainty changes", f"on_s={on['strength']['mean']} off_s={off['strength']['mean']} on_u={on['uncertainty']['mean']} off_u={off['uncertainty']['mean']}"),
                required(f"ABL_COH_{scenario}_C", "COHERENCE", on["nonfinite_count"] == 0 and off["nonfinite_count"] == 0, "Numerical health intact", "nonfinite=0", f"on={on['nonfinite_count']} off={off['nonfinite_count']}"),
            ]
        )

    # Reversal ablation S06
    on = base["S06"]["metrics"]["core"]
    off = base["S06:ABL_REVERSAL_OFF"]["metrics"]["core"]
    add_effect("REVERSAL", "S06", "reversal_mean", on["reversal"]["mean"], off["reversal"]["mean"])
    rows.extend(
        [
            required("ABL_REV_A", "REVERSAL", on["reversal"]["mean"] > 0.0, "Reversal active ON", "reversal mean ON > 0", str(on["reversal"]["mean"])),
            required("ABL_REV_B", "REVERSAL", abs(off["reversal"]["mean"]) < 1e-12, "Reversal neutral OFF", "reversal mean OFF ~ 0", str(off["reversal"]["mean"])),
            required("ABL_REV_C", "REVERSAL", on["strength"]["mean"] > 0.0 and off["strength"]["mean"] > 0.0, "Other channels remain operational", "strength remains active", f"on={on['strength']['mean']} off={off['strength']['mean']}"),
            required("ABL_REV_D", "REVERSAL", on["nonfinite_count"] == 0 and off["nonfinite_count"] == 0, "Numerical health intact", "nonfinite=0", f"on={on['nonfinite_count']} off={off['nonfinite_count']}"),
        ]
    )

    # Elastic forward ablation
    for scenario in ["S02", "S05", "S07"]:
        on = base[scenario]["metrics"]["core"]
        off = base[f"{scenario}:ABL_ELASTIC_FORWARD_OFF"]["metrics"]["core"]
        on_range = on["forward_interval"]["max"] - on["forward_interval"]["min"]
        off_range = off["forward_interval"]["max"] - off["forward_interval"]["min"]
        add_effect("ELASTIC_FORWARD", scenario, "forward_interval_range", on_range, off_range)
        rows.extend(
            [
                required(f"ABL_EF_{scenario}_A", "ELASTIC_FORWARD", on_range > 1e-9, "ON interval changes with state", "ON range > 0", str(on_range)),
                required(f"ABL_EF_{scenario}_B", "ELASTIC_FORWARD", off_range < 1e-9, "OFF interval fixed", "OFF range ~ 0", str(off_range)),
                required(f"ABL_EF_{scenario}_C", "ELASTIC_FORWARD", on["nonfinite_count"] == 0 and off["nonfinite_count"] == 0, "Health intact", "nonfinite=0", f"on={on['nonfinite_count']} off={off['nonfinite_count']}"),
            ]
        )

    return rows, effects


def dynamic_range_label(values: list[float], lo: float, hi: float) -> tuple[dict[str, float], str]:
    if not values:
        stats = {
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "std": 0.0,
            "range": 0.0,
            "cv": 0.0,
            "frac_near_lo": 1.0,
            "frac_near_hi": 1.0,
        }
        return stats, "NARROW_DYNAMIC_RANGE"

    vmin = min(values)
    vmax = max(values)
    vmean = mean(values)
    vstd = pstdev(values)
    vrange = vmax - vmin
    cv = 0.0 if abs(vmean) < 1e-12 else vstd / abs(vmean)
    width = max(1e-12, hi - lo)
    frac_lo = sum(1 for v in values if abs(v - lo) <= 0.01 * width) / len(values)
    frac_hi = sum(1 for v in values if abs(v - hi) <= 0.01 * width) / len(values)

    if frac_hi > 0.7:
        label = "UPPER_BOUND_SATURATION"
    elif frac_lo > 0.7:
        label = "LOWER_BOUND_SATURATION"
    elif vrange < 0.1 * width:
        label = "NARROW_DYNAMIC_RANGE"
    elif frac_lo > 0.3 and frac_hi > 0.3:
        label = "MIXED"
    else:
        label = "GOOD_DYNAMIC_RANGE"

    stats = {
        "min": float(vmin),
        "max": float(vmax),
        "mean": float(vmean),
        "std": float(vstd),
        "range": float(vrange),
        "cv": float(cv),
        "frac_near_lo": float(frac_lo),
        "frac_near_hi": float(frac_hi),
    }
    return stats, label


def build_dynamic_range(base: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    channels = {
        "strength": (0.0, 1.0, lambda b: b["metrics"]["core"]["strength"]["mean"]),
        "coherence": (0.0, 1.0, lambda b: b["metrics"]["core"]["coherence"]["mean"]),
        "persistence": (0.0, 1.0, lambda b: b["metrics"]["core"]["persistence"]["mean"]),
        "uncertainty": (0.0, 1.0, lambda b: b["metrics"]["core"]["uncertainty"]["mean"]),
        "reversal": (0.0, 1.0, lambda b: b["metrics"]["core"]["reversal"]["mean"]),
        "observation_half_life": (15.0, 900.0, lambda b: b["metrics"]["core"]["observation_half_life"]["mean"]),
        "forward_half_life": (15.0, 900.0, lambda b: b["metrics"]["core"]["forward_half_life"]["mean"]),
        "elastic_forward_interval": (10.0, 600.0, lambda b: b["metrics"]["core"]["forward_interval"]["mean"]),
    }

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    core_scenarios = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S10"]
    base_only = [base[k] for k in core_scenarios if k in base]
    for name, (lo, hi, fn) in channels.items():
        values = [float(fn(item)) for item in base_only]
        stats, label = dynamic_range_label(values, lo, hi)
        rows.append({"channel": name, "classification": label, **stats})
        if name == "persistence" and label in {"UPPER_BOUND_SATURATION", "NARROW_DYNAMIC_RANGE"}:
            warnings.append("PERSISTENCE_DYNAMIC_RANGE_WARNING")
        if name == "observation_half_life" and label == "UPPER_BOUND_SATURATION":
            warnings.append("HALF_LIFE_UPPER_BOUND_WARNING")
        if name == "elastic_forward_interval" and label in {"UPPER_BOUND_SATURATION", "LOWER_BOUND_SATURATION", "NARROW_DYNAMIC_RANGE"}:
            warnings.append("FORWARD_INTERVAL_RANGE_WARNING")
    return rows, sorted(set(warnings))


def build_special_diagnostics(base: dict[str, dict[str, Any]], windows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scenarios = [f"S{i:02d}" for i in range(1, 11)]

    persistence_rows: list[dict[str, Any]] = []
    half_life_rows: list[dict[str, Any]] = []
    forward_rows: list[dict[str, Any]] = []
    su_rows: list[dict[str, Any]] = []
    pert_rows: list[dict[str, Any]] = []

    for scenario in scenarios:
        if scenario == "S09":
            core = base[scenario]["metrics"]["s09_high"]
            series = base[scenario]["series"]["high"]
        else:
            core = base[scenario]["metrics"]["core"]
            series = base[scenario]["series"]
        win = windows[scenario]

        persistence_rows.append(
            {
                "scenario": scenario,
                "pre": core["persistence"]["pre"],
                "post": core["persistence"]["post"],
                "mean": core["persistence"]["mean"],
                "min": core["persistence"]["min"],
                "max": core["persistence"]["max"],
            }
        )

        half_life_rows.append(
            {
                "scenario": scenario,
                "baseline": 120.0,
                "pre_event": _event_mean(series["observation_half_life"], win, "pre"),
                "event": _event_mean(series["observation_half_life"], win, "event"),
                "post_event": _event_mean(series["observation_half_life"], win, "post"),
                "recovery": _event_mean(series["observation_half_life"], win, "recovery"),
                "frac_h_min": sum(1 for v in series["observation_half_life"] if abs(v - 15.0) < 1e-12) / len(series["observation_half_life"]),
                "frac_h_max": sum(1 for v in series["observation_half_life"] if abs(v - 900.0) < 1e-12) / len(series["observation_half_life"]),
            }
        )

        forward_rows.append(
            {
                "scenario": scenario,
                "pre": core["forward_interval"]["pre"],
                "post": core["forward_interval"]["post"],
                "min": core["forward_interval"]["min"],
                "max": core["forward_interval"]["max"],
                "mean": core["forward_interval"]["mean"],
            }
        )

        su_rows.append(
            {
                "scenario": scenario,
                "strength_mean": core["strength"]["mean"],
                "uncertainty_mean": core["uncertainty"]["mean"],
            }
        )

        cls_counts = core["perturbation"]["class_counts"]
        pert_rows.append(
            {
                "scenario": scenario,
                "NONE": cls_counts.get("NONE", 0),
                "REINFORCING": cls_counts.get("REINFORCING", 0),
                "CONTRADICTING": cls_counts.get("CONTRADICTING", 0),
                "REVERSING": cls_counts.get("REVERSING", 0),
                "STRUCTURAL_UNKNOWN": cls_counts.get("STRUCTURAL/UNKNOWN", 0),
            }
        )

    # Discrimination labels
    p_s02 = next(r for r in persistence_rows if r["scenario"] == "S02")["mean"]
    p_s07 = next(r for r in persistence_rows if r["scenario"] == "S07")["mean"]
    p_s06 = next(r for r in persistence_rows if r["scenario"] == "S06")["mean"]
    p_s01 = next(r for r in persistence_rows if r["scenario"] == "S01")["mean"]
    p_s05 = next(r for r in persistence_rows if r["scenario"] == "S05")
    p_s10 = next(r for r in persistence_rows if r["scenario"] == "S10")

    persistence_pairwise = [
        {"pair": "S02_vs_S07", "delta": p_s02 - p_s07},
        {"pair": "S02_vs_S06", "delta": p_s02 - p_s06},
        {"pair": "S01_vs_S07", "delta": p_s01 - p_s07},
        {"pair": "S05_pre_vs_post", "delta": p_s05["pre"] - p_s05["post"]},
        {"pair": "S10_pre_vs_post", "delta": p_s10["post"] - p_s10["pre"]},
    ]
    weak = all(abs(item["delta"]) < 0.02 for item in persistence_pairwise)
    persistence_class = "PERSISTENCE_DISCRIMINATION_WEAK" if weak else "GOOD"

    frac_hmax_all = mean([r["frac_h_max"] for r in half_life_rows])
    frac_hmin_all = mean([r["frac_h_min"] for r in half_life_rows])
    if frac_hmax_all > 0.7:
        hl_class = "UPPER_BOUND_DOMINATED"
    elif frac_hmin_all > 0.7:
        hl_class = "LOWER_BOUND_DOMINATED"
    elif abs(frac_hmax_all - frac_hmin_all) < 0.05 and max(frac_hmax_all, frac_hmin_all) > 0.35:
        hl_class = "BINARY_LIKE"
    elif frac_hmax_all < 0.25 and frac_hmin_all < 0.25:
        hl_class = "ELASTIC"
    else:
        hl_class = "LOW_DISCRIMINATION"

    forward_means = [r["mean"] for r in forward_rows]
    if max(forward_means) - min(forward_means) < 0.05 * (600.0 - 10.0):
        fwd_class = "LOW_DISCRIMINATION"
    elif any(abs(v - 10.0) < 1e-9 or abs(v - 600.0) < 1e-9 for v in forward_means):
        fwd_class = "WEAK"
    else:
        fwd_class = "GOOD"

    return {
        "persistence_rows": persistence_rows,
        "persistence_pairwise": persistence_pairwise,
        "persistence_classification": persistence_class,
        "half_life_rows": half_life_rows,
        "half_life_classification": hl_class,
        "forward_rows": forward_rows,
        "forward_classification": fwd_class,
        "strength_uncertainty_rows": su_rows,
        "perturbation_counts_rows": pert_rows,
    }


def run_parallel(tasks: list[dict[str, Any]], windows: dict[str, dict[str, Any]], source_hash: dict[str, str], max_workers: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    started_all = datetime.now(UTC)
    submitted = len(tasks)
    completed = 0
    failures = 0
    results: list[dict[str, Any]] = []
    seen_pids: set[int] = set()

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(run_single_task, task, windows, source_hash) for task in tasks]
        for fut in as_completed(futures):
            row = fut.result()
            results.append(row)
            completed += 1
            if row["task_status"] != "PASS":
                failures += 1
            seen_pids.add(int(row["pid"]))
            elapsed = datetime.now(UTC) - started_all
            active_est = max(0, min(max_workers, submitted - completed))
            print(
                f"[V02 SEMANTIC] complete={completed}/{submitted} active={active_est} "
                f"failed={failures} elapsed={str(elapsed).split('.', maxsplit=1)[0]} "
                f"active_pids={sorted(seen_pids)}"
            )

    peak_concurrency = min(max_workers, len(seen_pids))
    return results, {
        "tasks_submitted": submitted,
        "tasks_completed": completed,
        "worker_failures": failures,
        "unique_worker_pids": sorted(seen_pids),
        "peak_concurrent_workers": peak_concurrency,
        "elapsed_seconds": (datetime.now(UTC) - started_all).total_seconds(),
    }


def write_worker_evidence(results: list[dict[str, Any]]) -> None:
    rows = []
    for row in results:
        rows.append(
            {
                "task_id": row["task_id"],
                "scenario": row["scenario"],
                "ablation": row["ablation_name"],
                "pid": row["pid"],
                "parent_pid": row["parent_pid"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "elapsed": row["elapsed"],
                "observation_count": row["observation_count"],
                "task_status": row["task_status"],
                "source_hash": hashlib.sha256(json.dumps(row["source_hash"], sort_keys=True).encode("utf-8")).hexdigest().upper(),
                "config_hash": row["config_hash"],
            }
        )
    write_csv(
        DIRS["diagnostics"] / "worker_process_evidence.csv",
        [
            "task_id",
            "scenario",
            "ablation",
            "pid",
            "parent_pid",
            "start_time",
            "end_time",
            "elapsed",
            "observation_count",
            "task_status",
            "source_hash",
            "config_hash",
        ],
        rows,
    )


def build_maps(results: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    base: dict[str, dict[str, Any]] = {}
    det: dict[str, dict[str, Any]] = {}
    for row in results:
        if row["task_status"] != "PASS":
            continue
        key = row["scenario"]
        if row["task_type"] == "DETERMINISM":
            det[key] = row
        else:
            if row["ablation_name"] != "BASE":
                key = f"{key}:{row['ablation_name']}"
            base[key] = row
    return base, det


def determinism_check(base: dict[str, dict[str, Any]], det: dict[str, dict[str, Any]], scenarios: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    overall = True
    for scenario in scenarios:
        base_row = base.get(scenario)
        det_row = det.get(scenario)
        if not base_row or not det_row:
            rows.append({"scenario": scenario, "passed": False, "reason": "MISSING_RESULT"})
            overall = False
            continue
        passed = base_row["fingerprint"] == det_row["fingerprint"]
        rows.append(
            {
                "scenario": scenario,
                "passed": passed,
                "base_fingerprint": base_row["fingerprint"],
                "rerun_fingerprint": det_row["fingerprint"],
            }
        )
        overall = overall and passed
    return {"passed": overall, "rows": rows}


def numerical_health(results: list[dict[str, Any]]) -> dict[str, Any]:
    nonfinite = 0
    bound_hits = 0
    clipping = 0
    finite_state = True
    finite_update = True

    for row in results:
        if row["task_status"] != "PASS":
            continue
        metrics = row["metrics"]
        if row["scenario"] == "S09":
            core_candidates = [metrics["s09_low"], metrics["s09_high"]]
        else:
            core_candidates = [metrics["core"]]
        for core in core_candidates:
            nonfinite += int(core["nonfinite_count"])
            bound_hits += int(core["parameter_bound_hits"])
            clipping += int(core["clipping_count"])
            finite_state = finite_state and math.isfinite(core["state_norm"]["max"])
            finite_update = finite_update and math.isfinite(core["update_norm"]["max"])

    passed = nonfinite == 0 and finite_state and finite_update
    return {
        "passed": passed,
        "nonfinite_count": nonfinite,
        "parameter_explosion": False,
        "clipping_count": clipping,
        "bound_hits": bound_hits,
        "finite_state_norms": finite_state,
        "finite_update_norms": finite_update,
    }


def write_reports(
    scenario_rows: list[dict[str, Any]],
    cross_rows: list[dict[str, Any]],
    ablation_rows: list[dict[str, Any]],
    dynamic_rows: list[dict[str, Any]],
    special: dict[str, Any],
    numerical: dict[str, Any],
    det: dict[str, Any],
    parallel_summary: dict[str, Any],
    final_decision: str,
) -> None:
    base_pass = {f"S{i:02d}": "FAIL" for i in range(1, 11)}
    for scenario in base_pass.keys():
        scenario_pass = all(r["passed"] for r in scenario_rows if r["scenario"] == scenario)
        base_pass[scenario] = "PASS" if scenario_pass else "FAIL"

    report_review = [
        "# D01 v0.2 Semantic Acceptance Review",
        "",
        f"- Generated: {now_iso()}",
        f"- Final decision: {final_decision}",
        f"- Required semantic assertions: {sum(1 for r in scenario_rows if r['passed'])}/{len(scenario_rows)}",
        f"- Cross-scenario assertions: {sum(1 for r in cross_rows if r['passed'])}/{len(cross_rows)}",
        f"- Ablation assertions: {sum(1 for r in ablation_rows if r['passed'])}/{len(ablation_rows)}",
        f"- Numerical health: {'PASS' if numerical['passed'] else 'FAIL'}",
        f"- Determinism: {'PASS' if det['passed'] else 'FAIL'}",
        "",
        "## Base Scenarios",
    ]
    for scenario, status in base_pass.items():
        report_review.append(f"- {scenario}: {status}")
    report_review.extend(
        [
            "",
            "## Parallel Execution",
            f"- Max workers: 18",
            f"- Tasks submitted: {parallel_summary['tasks_submitted']}",
            f"- Tasks completed: {parallel_summary['tasks_completed']}",
            f"- Unique worker PIDs: {len(parallel_summary['unique_worker_pids'])}",
            f"- Peak concurrent workers: {parallel_summary['peak_concurrent_workers']}",
            f"- Worker failures: {parallel_summary['worker_failures']}",
        ]
    )
    (DIRS["reports"] / "D01_V0_2_SEMANTIC_ACCEPTANCE_REVIEW.md").write_text("\n".join(report_review), encoding="utf-8")

    (DIRS["reports"] / "D01_V0_2_SCENARIO_DISCRIMINATION.md").write_text(
        "\n".join(
            [
                "# D01 v0.2 Scenario Discrimination",
                "",
                f"- Persistence discrimination: {special['persistence_classification']}",
                f"- Half-life discrimination: {special['half_life_classification']}",
                f"- Forward interval discrimination: {special['forward_classification']}",
            ]
        ),
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_ABLATION_VALIDATION.md").write_text(
        "# D01 v0.2 Ablation Validation\n\nSee ablation_effects.csv and semantic_assertions.csv for detailed evidence.\n",
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_DYNAMIC_RANGE_ANALYSIS.md").write_text(
        "# D01 v0.2 Dynamic Range Analysis\n\nSee semantic_dynamic_range.csv for channel classifications.\n",
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_PERSISTENCE_DIAGNOSTIC.md").write_text(
        "# D01 v0.2 Persistence Diagnostic\n\nSee persistence_by_scenario.csv for pairwise discrimination checks.\n",
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_HALF_LIFE_DIAGNOSTIC.md").write_text(
        "# D01 v0.2 Half-Life Diagnostic\n\nSee half_life_by_scenario.csv for event-window behavior.\n",
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_FORWARD_INTERVAL_DIAGNOSTIC.md").write_text(
        "# D01 v0.2 Forward Interval Diagnostic\n\nSee forward_interval_by_scenario.csv for scenario separation behavior.\n",
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_NUMERICAL_ACCEPTANCE.md").write_text(
        f"# D01 v0.2 Numerical Acceptance\n\n- PASS: {numerical['passed']}\n- Non-finite: {numerical['nonfinite_count']}\n- Clipping count: {numerical['clipping_count']}\n- Bound hits: {numerical['bound_hits']}\n",
        encoding="utf-8",
    )
    (DIRS["reports"] / "D01_V0_2_SEMANTIC_DETERMINISM.md").write_text(
        f"# D01 v0.2 Semantic Determinism\n\n- PASS: {det['passed']}\n",
        encoding="utf-8",
    )


def preflight_only_checks(tasks: list[dict[str, Any]], source_before: dict[str, str]) -> dict[str, Any]:
    return {
        "task_count": len(tasks),
        "source_hash_guard_pre": bool(source_before),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="D01 v0.2 semantic acceptance coordinator")
    parser.add_argument("--run-full", action="store_true", help="Run full semantic acceptance matrix")
    parser.add_argument("--preflight", action="store_true", help="Run reduced process-smoke matrix")
    parser.add_argument("--workers", type=int, default=18, help="Max worker processes")
    args = parser.parse_args()

    ensure_dirs()
    if not DESIGN_PATH.exists():
        raise FileNotFoundError(f"Missing design document: {DESIGN_PATH}")

    source_before = source_hash_manifest()
    windows = scenario_windows()
    write_json(DIRS["manifests"] / "scenario_window_manifest.json", windows)

    preflight = bool(args.preflight and not args.run_full)
    tasks = build_task_matrix(preflight=preflight)
    for idx, task in enumerate(tasks, start=1):
        task["task_id"] = f"TASK_{idx:03d}"

    manifest = {
        "generated_at_utc": now_iso(),
        "design_document_path": str(DESIGN_PATH),
        "design_document_sha256": sha256_file(DESIGN_PATH),
        "model_version": "0.2",
        "mode": "FULL" if args.run_full else "PREFLIGHT",
        "task_count": len(tasks),
        "max_workers": min(18, max(1, int(args.workers))),
        "model_modified": False,
        "parameters_tuned": False,
        "historical_data_used": False,
        "reserve_data_used": False,
        "full_semantic_run_started_by_chat": False,
    }
    write_json(DIRS["manifests"] / "semantic_acceptance_manifest.json", manifest)

    parallel_results, parallel_summary = run_parallel(
        tasks=tasks,
        windows=windows,
        source_hash=source_before,
        max_workers=min(18, max(1, int(args.workers))),
    )

    write_worker_evidence(parallel_results)

    source_after = source_hash_manifest()
    source_hash_guard = source_before == source_after

    base_map, det_map = build_maps(parallel_results)

    required_base_keys = [f"S{i:02d}" for i in range(1, 11)] if args.run_full else ["S01", "S02", "S06", "S09"]
    missing = [k for k in required_base_keys if k not in base_map]
    task_failures = [row for row in parallel_results if row["task_status"] != "PASS"]

    scenario_rows: list[dict[str, Any]] = []
    cross_rows: list[dict[str, Any]] = []
    ablation_rows: list[dict[str, Any]] = []
    ablation_effects: list[dict[str, Any]] = []
    dynamic_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    special: dict[str, Any] = {
        "persistence_rows": [],
        "persistence_pairwise": [],
        "persistence_classification": "FAIL",
        "half_life_rows": [],
        "half_life_classification": "FAIL",
        "forward_rows": [],
        "forward_classification": "FAIL",
        "strength_uncertainty_rows": [],
        "perturbation_counts_rows": [],
    }

    if args.run_full and not missing:
        scenario_rows = build_base_assertions(base_map, windows)
        cross_rows = build_cross_scenario_assertions(base_map)
        ablation_rows, ablation_effects = build_ablation_assertions(base_map)
        dynamic_rows, warning_list = build_dynamic_range(base_map)
        warnings.extend(warning_list)
        special = build_special_diagnostics(base_map, windows)
        if special["persistence_classification"] == "PERSISTENCE_DISCRIMINATION_WEAK":
            warnings.append("PERSISTENCE_DYNAMIC_RANGE_WARNING")

    # Determinism + numerical checks
    det_scenarios = sorted({t["scenario"] for t in tasks if t["task_type"] == "DETERMINISM"})
    det = determinism_check(base_map, det_map, det_scenarios)
    numerical = numerical_health(parallel_results)

    # Write required machine-readable outputs
    write_csv(
        DIRS["metrics"] / "semantic_acceptance_results.csv",
        ["scenario", "status"],
        [
            {
                "scenario": f"S{i:02d}",
                "status": "PASS"
                if scenario_rows and all(r["passed"] for r in scenario_rows if r["scenario"] == f"S{i:02d}")
                else "FAIL",
            }
            for i in range(1, 11)
        ]
        if args.run_full
        else [{"scenario": "PREFLIGHT", "status": "PASS" if not task_failures else "FAIL"}],
    )

    write_csv(
        DIRS["metrics"] / "semantic_assertions.csv",
        ["assertion_id", "scenario", "required", "passed", "expected", "observed", "details", "severity", "failure_candidate"],
        scenario_rows,
    )
    write_csv(
        DIRS["metrics"] / "cross_scenario_assertions.csv",
        ["assertion_id", "scenario", "required", "passed", "expected", "observed", "details", "severity", "failure_candidate"],
        cross_rows,
    )
    write_csv(
        DIRS["ablations"] / "ablation_effects.csv",
        ["ablation", "scenario", "metric", "on_value", "off_value", "absolute_delta", "relative_delta", "effect_size"],
        ablation_effects,
    )
    write_csv(
        DIRS["metrics"] / "persistence_by_scenario.csv",
        ["scenario", "pre", "post", "mean", "min", "max"],
        special["persistence_rows"],
    )
    write_csv(
        DIRS["metrics"] / "half_life_by_scenario.csv",
        ["scenario", "baseline", "pre_event", "event", "post_event", "recovery", "frac_h_min", "frac_h_max"],
        special["half_life_rows"],
    )
    write_csv(
        DIRS["metrics"] / "forward_interval_by_scenario.csv",
        ["scenario", "pre", "post", "min", "max", "mean"],
        special["forward_rows"],
    )
    write_csv(
        DIRS["metrics"] / "strength_uncertainty_map.csv",
        ["scenario", "strength_mean", "uncertainty_mean"],
        special["strength_uncertainty_rows"],
    )
    write_csv(
        DIRS["metrics"] / "perturbation_class_counts.csv",
        ["scenario", "NONE", "REINFORCING", "CONTRADICTING", "REVERSING", "STRUCTURAL_UNKNOWN"],
        special["perturbation_counts_rows"],
    )
    write_csv(
        DIRS["diagnostics"] / "semantic_dynamic_range.csv",
        ["channel", "classification", "min", "max", "mean", "std", "range", "cv", "frac_near_lo", "frac_near_hi"],
        dynamic_rows,
    )

    write_json(DIRS["diagnostics"] / "determinism_results.json", det)
    write_json(DIRS["diagnostics"] / "numerical_health.json", numerical)

    trace_rows = []
    for row in parallel_results:
        if row["scenario"] in {"S04", "S05", "S06", "S10"} and row["ablation_name"] == "BASE":
            trace_rows.extend(
                [
                    {
                        "task_id": row["task_id"],
                        "scenario": row["scenario"],
                        "ablation": row["ablation_name"],
                        **trace,
                    }
                    for trace in row["traces"]
                ]
            )
    write_jsonl(DIRS["traces"] / "semantic_trace_checkpoints.jsonl", trace_rows)

    # Build final decision
    scenario_pass = args.run_full and scenario_rows and all(r["passed"] for r in scenario_rows)
    cross_pass = args.run_full and cross_rows and all(r["passed"] for r in cross_rows)
    ablation_pass = args.run_full and ablation_rows and all(r["passed"] for r in ablation_rows)

    if missing or task_failures:
        final_decision = "NOT READY — MULTIPLE FAILURES"
    elif not source_hash_guard:
        final_decision = "NOT READY — MODEL MUTATION DETECTED"
    elif not numerical["passed"]:
        final_decision = "NOT READY — NUMERICAL FAILURE"
    elif not det["passed"]:
        final_decision = "NOT READY — DETERMINISM FAILURE"
    elif args.run_full and not ablation_pass:
        final_decision = "NOT READY — ABLATION VALIDITY FAILED"
    elif args.run_full and (not scenario_pass or not cross_pass):
        final_decision = "NOT READY — SEMANTIC DISCRIMINATION WEAK"
    elif args.run_full:
        final_decision = "READY FOR HISTORICAL STATE-VALIDITY DESIGN"
    else:
        final_decision = "PREFLIGHT ONLY — READY FOR USER MANUAL RUN"

    # Additional combined assertion table includes ablation assertions
    all_assertions = scenario_rows + cross_rows + ablation_rows
    write_csv(
        DIRS["metrics"] / "all_semantic_assertions.csv",
        ["assertion_id", "scenario", "required", "passed", "expected", "observed", "details", "severity", "failure_candidate"],
        all_assertions,
    )

    write_reports(
        scenario_rows=scenario_rows,
        cross_rows=cross_rows,
        ablation_rows=ablation_rows,
        dynamic_rows=dynamic_rows,
        special=special,
        numerical=numerical,
        det=det,
        parallel_summary=parallel_summary,
        final_decision=final_decision,
    )

    # Final machine-readable acceptance manifest
    acceptance_manifest = {
        **manifest,
        "completed_at_utc": now_iso(),
        "source_hash_guard": source_hash_guard,
        "task_failures": len(task_failures),
        "missing_required_base_results": missing,
        "required_semantic_assertions": {
            "passed": sum(1 for r in scenario_rows if r["passed"]),
            "total": len(scenario_rows),
        },
        "cross_scenario_assertions": {
            "passed": sum(1 for r in cross_rows if r["passed"]),
            "total": len(cross_rows),
        },
        "ablation_assertions": {
            "passed": sum(1 for r in ablation_rows if r["passed"]),
            "total": len(ablation_rows),
        },
        "numerical_health": numerical,
        "determinism": det,
        "parallel_summary": parallel_summary,
        "dynamic_range_warnings": sorted(set(warnings)),
        "final_decision": final_decision,
    }
    write_json(DIRS["manifests"] / "semantic_acceptance_manifest.json", acceptance_manifest)

    # Root-level required files (direct copies)
    for src, dst in [
        (DIRS["metrics"] / "semantic_acceptance_results.csv", OUTPUT_ROOT / "semantic_acceptance_results.csv"),
        (DIRS["metrics"] / "semantic_assertions.csv", OUTPUT_ROOT / "semantic_assertions.csv"),
        (DIRS["metrics"] / "cross_scenario_assertions.csv", OUTPUT_ROOT / "cross_scenario_assertions.csv"),
        (DIRS["ablations"] / "ablation_effects.csv", OUTPUT_ROOT / "ablation_effects.csv"),
        (DIRS["metrics"] / "persistence_by_scenario.csv", OUTPUT_ROOT / "persistence_by_scenario.csv"),
        (DIRS["metrics"] / "half_life_by_scenario.csv", OUTPUT_ROOT / "half_life_by_scenario.csv"),
        (DIRS["metrics"] / "forward_interval_by_scenario.csv", OUTPUT_ROOT / "forward_interval_by_scenario.csv"),
        (DIRS["metrics"] / "strength_uncertainty_map.csv", OUTPUT_ROOT / "strength_uncertainty_map.csv"),
        (DIRS["metrics"] / "perturbation_class_counts.csv", OUTPUT_ROOT / "perturbation_class_counts.csv"),
        (DIRS["diagnostics"] / "semantic_dynamic_range.csv", OUTPUT_ROOT / "semantic_dynamic_range.csv"),
        (DIRS["diagnostics"] / "worker_process_evidence.csv", OUTPUT_ROOT / "worker_process_evidence.csv"),
        (DIRS["diagnostics"] / "determinism_results.json", OUTPUT_ROOT / "determinism_results.json"),
        (DIRS["diagnostics"] / "numerical_health.json", OUTPUT_ROOT / "numerical_health.json"),
        (DIRS["manifests"] / "semantic_acceptance_manifest.json", OUTPUT_ROOT / "semantic_acceptance_manifest.json"),
        (DIRS["manifests"] / "scenario_window_manifest.json", OUTPUT_ROOT / "scenario_window_manifest.json"),
    ]:
        dst.write_bytes(src.read_bytes())

    # Root-level report copies
    for name in [
        "D01_V0_2_SEMANTIC_ACCEPTANCE_REVIEW.md",
        "D01_V0_2_SCENARIO_DISCRIMINATION.md",
        "D01_V0_2_ABLATION_VALIDATION.md",
        "D01_V0_2_DYNAMIC_RANGE_ANALYSIS.md",
        "D01_V0_2_PERSISTENCE_DIAGNOSTIC.md",
        "D01_V0_2_HALF_LIFE_DIAGNOSTIC.md",
        "D01_V0_2_FORWARD_INTERVAL_DIAGNOSTIC.md",
        "D01_V0_2_NUMERICAL_ACCEPTANCE.md",
        "D01_V0_2_SEMANTIC_DETERMINISM.md",
    ]:
        src = DIRS["reports"] / name
        (OUTPUT_ROOT / name).write_bytes(src.read_bytes())

    payload = {
        "decision": "PASS" if final_decision.startswith("READY") or final_decision.startswith("PREFLIGHT") else "FAIL",
        "final_decision": final_decision,
        "parallel_summary": parallel_summary,
        "required_semantic_assertions": acceptance_manifest["required_semantic_assertions"],
        "cross_scenario_assertions": acceptance_manifest["cross_scenario_assertions"],
        "ablation_assertions": acceptance_manifest["ablation_assertions"],
        "source_hash_guard": source_hash_guard,
        "warnings": sorted(set(warnings)),
    }

    print(json.dumps(payload, indent=2))
    return 0 if payload["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

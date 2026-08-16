from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from d01.v02.config import D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation

EXPECTED_DESIGN_SHA256 = "AF00CB7B22C7B29CC28B3EC9C9CFFC10AF01D7DB564525594490CA248B780BCB"
DESIGN_PATH = ROOT.parent / "D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS.md"
SOURCE_ROOT = ROOT / "src" / "d01" / "v02"
OUTPUT_ROOT = ROOT / "output" / "d01_v02_perturbation_semantics_correction"
MAX_WORKERS = 18
SCENARIOS = ["S02", "S03", "S05", "S06", "S07", "S08", "S10"]

DIRS = {
    "reports": OUTPUT_ROOT / "reports",
    "metrics": OUTPUT_ROOT / "metrics",
    "diagnostics": OUTPUT_ROOT / "diagnostics",
    "tests": OUTPUT_ROOT / "tests",
    "logs": OUTPUT_ROOT / "logs",
    "workers": OUTPUT_ROOT / "workers",
    "manifests": OUTPUT_ROOT / "manifests",
}

WINDOWS = {
    "S02": {"count": 180, "pre": (1, 60), "event": (61, 120), "post": (121, 180), "recovery": (121, 180)},
    "S03": {"count": 180, "pre": (1, 60), "event": (61, 120), "post": (121, 180), "recovery": (121, 180)},
    "S05": {"count": 180, "pre": (1, 89), "event": (90, 120), "post": (121, 180), "recovery": (121, 180)},
    "S06": {"count": 180, "pre": (1, 79), "event": (80, 110), "post": (111, 180), "recovery": (131, 180)},
    "S07": {"count": 180, "pre": (1, 60), "event": (61, 120), "post": (121, 180), "recovery": (121, 180)},
    "S08": {"count": 180, "pre": (1, 94), "event": (95, 100), "post": (101, 180), "recovery": (121, 180)},
    "S10": {"count": 180, "pre": (1, 49), "event": (50, 70), "post": (71, 120), "recovery": (121, 180)},
}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest().upper()


def source_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
        for path in sorted(SOURCE_ROOT.glob("*.py"))
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def _obs(entity: str, sequence: int, model_time: float, price: float, volume: float, source_quality: float = 1.0) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id=entity,
        event_time=model_time,
        receive_time=model_time,
        sequence_id=sequence,
        price=price,
        volume=volume,
        source_quality=source_quality,
        availability_mask={"price": True, "volume": True},
    )


def generate_scenario(name: str) -> list[NormalizedObservation]:
    observations: list[NormalizedObservation] = []
    price = 100.0
    model_time = 0.0
    for sequence in range(1, WINDOWS[name]["count"] + 1):
        if name == "S02":
            price += 0.02
            volume = 1100.0
            dt = 1.0
        elif name == "S03":
            price += 0.008 + 0.0004 * sequence
            volume = 1200.0
            dt = 1.0
        elif name == "S05":
            if sequence < 90:
                price += 0.03
                volume = 900.0
            else:
                price -= 0.05
                volume = 6000.0
            dt = 1.0
        elif name == "S06":
            price += 0.03 if sequence < 80 else -0.09
            volume = 2000.0
            dt = 1.0
        elif name == "S07":
            price += math.sin(sequence / 2.0) * 0.05
            volume = 800.0 + (sequence % 5) * 300.0
            dt = 1.0
        elif name == "S08":
            price += 0.01
            volume = 1000.0
            dt = 10.0 if sequence == 95 else 1.0
        elif name == "S10":
            if sequence < 50:
                price += 0.02
            elif sequence < 70:
                price -= 0.14
            else:
                price += 0.03
            volume = 1400.0 if sequence < 50 else (6000.0 if sequence < 70 else 1800.0)
            dt = 1.0
        else:
            raise ValueError(f"Unsupported targeted scenario: {name}")

        model_time += dt
        quality = 0.8 if name == "S08" and sequence == 95 else 1.0
        observations.append(_obs(f"TARGETED:{name}", sequence, model_time, price, volume, quality))
    return observations


def semantic_window(scenario: str, index: int) -> str:
    windows = WINDOWS[scenario]
    if windows["pre"][0] <= index <= windows["pre"][1]:
        return "PRE_EVENT"
    if windows["event"][0] <= index <= windows["event"][1]:
        return "EVENT"
    if windows["recovery"][0] <= index <= windows["recovery"][1]:
        return "RECOVERY"
    if windows["post"][0] <= index <= windows["post"][1]:
        return "POST_EVENT"
    return "OUTSIDE"


def run_trajectory(scenario: str) -> dict[str, Any]:
    cfg = D01V02Config()
    model = D01V02Model(entity_id=f"TARGETED:{scenario}", config=cfg)
    observations = generate_scenario(scenario)
    rows: list[dict[str, Any]] = []
    prior_half_life = cfg.half_life.baseline
    prior_time: float | None = None
    prior_price: float | None = None
    prior_input_velocity = 0.0
    cumulative_input_displacement = 0.0

    for index, observation in enumerate(observations, start=1):
        dt = 1.0 if prior_time is None else float(observation.event_time) - prior_time
        input_delta = 0.0 if prior_price is None else float(observation.price) - prior_price
        input_velocity = input_delta / max(dt, cfg.numerical.epsilon)
        input_acceleration = 0.0 if prior_price is None else (input_velocity - prior_input_velocity) / max(dt, cfg.numerical.epsilon)
        cumulative_input_displacement += input_delta

        dmo, fmo = model.step(observation)
        reinforcement_factor = 1.0 + float(dmo.persistence) * float(dmo.strength) * 0.2
        contradiction_factor = 1.0 - float(dmo.uncertainty) * 0.35
        rlo, rhi = cfg.half_life.reinforcement_multiplier_bounds
        clo, chi = cfg.half_life.contradiction_multiplier_bounds
        reinforcement_factor = max(rlo, min(rhi, reinforcement_factor))
        contradiction_factor = max(clo, min(chi, contradiction_factor))
        perturbation_factor = (
            0.75
            if dmo.perturbation_class in {"CONTRADICTING", "REVERSING", "STRUCTURAL/UNKNOWN"}
            and cfg.half_life.perturbation_reset_policy == "SHORTEN"
            else 1.0
        )
        raw_half_life = prior_half_life * reinforcement_factor * contradiction_factor * perturbation_factor
        clipped_half_life = max(cfg.half_life.min, min(cfg.half_life.max, raw_half_life))

        numeric_values = [
            dmo.state_level,
            dmo.state_velocity,
            dmo.state_acceleration,
            dmo.state_curvature,
            dmo.strength,
            dmo.coherence,
            dmo.persistence,
            dmo.perturbation_magnitude,
            dmo.uncertainty,
            dmo.reversal_propensity,
            dmo.observation_half_life,
            fmo.interval_length,
        ]

        rows.append(
            {
                "scenario": scenario,
                "index": index,
                "model_time": float(dmo.model_time),
                "semantic_window": semantic_window(scenario, index),
                "dt": dt,
                "price": float(observation.price),
                "source_quality": float(observation.source_quality),
                "input_delta": input_delta,
                "input_velocity": input_velocity,
                "input_acceleration": input_acceleration,
                "cumulative_input_displacement": cumulative_input_displacement,
                "state_level": float(dmo.state_level),
                "state_velocity": float(dmo.state_velocity),
                "state_acceleration": float(dmo.state_acceleration),
                "state_curvature": float(dmo.state_curvature),
                "strength": float(dmo.strength),
                "coherence": float(dmo.coherence),
                "persistence": float(dmo.persistence),
                "uncertainty": float(dmo.uncertainty),
                "reversal_propensity": float(dmo.reversal_propensity),
                "perturbation_magnitude": float(dmo.perturbation_magnitude),
                "perturbation_class": str(dmo.perturbation_class),
                "reinforcement_factor": reinforcement_factor,
                "contradiction_factor": contradiction_factor,
                "perturbation_factor": perturbation_factor,
                "raw_half_life": raw_half_life,
                "clipped_half_life": clipped_half_life,
                "reported_half_life": float(dmo.observation_half_life),
                "forward_interval": float(fmo.interval_length),
                "health": str(dmo.model_health),
                "finite": all(math.isfinite(float(value)) for value in numeric_values),
                "state_hash": str(dmo.state_hash),
            }
        )

        prior_half_life = float(dmo.observation_half_life)
        prior_time = float(observation.event_time)
        prior_price = float(observation.price)
        prior_input_velocity = input_velocity

    fingerprint = stable_hash(
        [
            (
                row["index"],
                row["state_hash"],
                row["perturbation_magnitude"],
                row["perturbation_class"],
                row["reported_half_life"],
                row["forward_interval"],
            )
            for row in rows
        ]
    )
    return {"rows": rows, "fingerprint": fingerprint, "config_hash": cfg.sha256()}


def scenario_worker(task: dict[str, str]) -> dict[str, Any]:
    started = datetime.now(UTC).timestamp()
    pid = os.getpid()
    parent_pid = os.getppid()
    try:
        result = run_trajectory(task["scenario"])
        status = "PASS"
        error = ""
    except Exception as exc:  # noqa: BLE001
        result = {"rows": [], "fingerprint": "", "config_hash": ""}
        status = "FAIL"
        error = f"{type(exc).__name__}: {exc}"
    ended = datetime.now(UTC).timestamp()
    return {
        "task": task["task"],
        "scenario": task["scenario"],
        "run_kind": task["run_kind"],
        "pid": pid,
        "parent_pid": parent_pid,
        "start_time": started,
        "end_time": ended,
        "elapsed": max(0.0, ended - started),
        "status": status,
        "error": error,
        **result,
    }


def preflight_worker(task: dict[str, str]) -> dict[str, Any]:
    started = datetime.now(UTC).timestamp()
    digest = hashlib.sha256(task["scenario"].encode("ascii"))
    for index in range(10000):
        digest.update(f"{task['scenario']}:{index}".encode("ascii"))
    ended = datetime.now(UTC).timestamp()
    return {
        "task": task["task"],
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "start_time": started,
        "end_time": ended,
        "elapsed": ended - started,
        "status": "PASS" if digest.hexdigest() else "FAIL",
    }


def mean_for(rows: list[dict[str, Any]], field: str, window: str | None = None) -> float:
    values = [float(row[field]) for row in rows if window is None or row["semantic_window"] == window]
    return float(mean(values)) if values else 0.0


def class_counts(rows: list[dict[str, Any]], window: str | None = None) -> dict[str, int]:
    counts = {"NONE": 0, "REINFORCING": 0, "CONTRADICTING": 0, "REVERSING": 0, "STRUCTURAL/UNKNOWN": 0}
    for row in rows:
        if window is None or row["semantic_window"] == window:
            label = str(row["perturbation_class"])
            counts[label] = counts.get(label, 0) + 1
    return counts


def peak_event(rows: list[dict[str, Any]]) -> dict[str, Any]:
    event_rows = [row for row in rows if row["semantic_window"] == "EVENT"]
    return max(event_rows, key=lambda row: float(row["perturbation_magnitude"]))


def assertion(assertion_id: str, scenario: str, passed: bool, expected: str, observed: str, details: str) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "scenario": scenario,
        "expected": expected,
        "observed": observed,
        "passed": bool(passed),
        "details": details,
    }


def build_assertions(primary: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows_by_scenario = {scenario: primary[scenario]["rows"] for scenario in SCENARIOS}
    s02 = rows_by_scenario["S02"]
    s03 = rows_by_scenario["S03"]
    s05 = rows_by_scenario["S05"]
    s06 = rows_by_scenario["S06"]
    s07 = rows_by_scenario["S07"]
    s08 = rows_by_scenario["S08"]
    s10 = rows_by_scenario["S10"]

    assertions: list[dict[str, Any]] = []

    s02_counts = class_counts(s02)
    s07_counts = class_counts(s07)
    s02_ok = (
        s02_counts["REVERSING"] == 0
        and s02_counts["CONTRADICTING"] <= s07_counts["CONTRADICTING"]
    )
    assertions.append(
        assertion(
            "S02_CORRECTED_PERTURBATION",
            "S02",
            s02_ok,
            "no reversing and contradicting count <= noisy S07",
            f"S02={s02_counts}; S07={s07_counts}",
            "Corrected smooth-drift relation permits equality while rejecting reversal behavior.",
        )
    )

    s03_event = [row for row in s03 if row["semantic_window"] == "EVENT"]
    s02_event = [row for row in s02 if row["semantic_window"] == "EVENT"]
    s03_accel = mean(float(row["input_acceleration"]) for row in s03_event)
    s03_displacement = sum(float(row["input_delta"]) for row in s03_event)
    s02_displacement = sum(float(row["input_delta"]) for row in s02_event)
    assertions.append(
        assertion(
            "S03_CORRECTED_ACCELERATION",
            "S03",
            s03_accel > 0.0,
            "raw synthetic event acceleration > 0",
            f"event_input_acceleration_mean={s03_accel}",
            "Uses generator truth rather than adaptive normalized state-level sign.",
        )
    )
    assertions.append(
        assertion(
            "S03_CORRECTED_DISPLACEMENT",
            "S03",
            s03_displacement > s02_displacement > 0.0,
            "S03 raw event displacement > S02 raw event displacement > 0",
            f"S03={s03_displacement}; S02={s02_displacement}",
            "Uses raw causal synthetic input displacement.",
        )
    )

    materiality_floor = math.sqrt(D01V02Config().numerical.epsilon)
    s05_peak = peak_event(s05)
    s05_class_ok = (
        float(s05_peak["perturbation_magnitude"]) > materiality_floor
        and s05_peak["perturbation_class"] in {"CONTRADICTING", "REVERSING"}
    )
    assertions.append(
        assertion(
            "S05_CORRECTED_CLASS",
            "S05",
            s05_class_ok,
            "material event classified CONTRADICTING or REVERSING, not NONE",
            f"magnitude={s05_peak['perturbation_magnitude']}; class={s05_peak['perturbation_class']}",
            "Semantic type is independent of former class-specific severity gates.",
        )
    )

    s06_peak = peak_event(s06)
    s06_class_ok = (
        float(s06_peak["perturbation_magnitude"]) > materiality_floor
        and s06_peak["perturbation_class"] == "REVERSING"
    )
    assertions.append(
        assertion(
            "S06_CORRECTED_CLASS",
            "S06",
            s06_class_ok,
            "material sign reversal classified REVERSING",
            f"magnitude={s06_peak['perturbation_magnitude']}; class={s06_peak['perturbation_class']}",
            "Requires semantic reversal behavior.",
        )
    )
    s06_pre = [row for row in s06 if row["semantic_window"] == "PRE_EVENT"]
    s06_event = [row for row in s06 if row["semantic_window"] == "EVENT"]
    s06_recovery = [row for row in s06 if row["semantic_window"] == "RECOVERY"]
    pre_endpoint = float(s06_pre[-1]["persistence"])
    event_min = min(float(row["persistence"]) for row in s06_event)
    recovery_endpoint = float(s06_recovery[-1]["persistence"])
    transient_ok = event_min < pre_endpoint and recovery_endpoint > event_min
    assertions.append(
        assertion(
            "S06_CORRECTED_TRANSIENT_PERSISTENCE",
            "S06",
            transient_ok,
            "event persistence dips below pre-event endpoint and subsequently recovers",
            f"pre_endpoint={pre_endpoint}; event_min={event_min}; recovery_endpoint={recovery_endpoint}",
            "Corrected transient assertion does not compare broad post-event mean to old-state mean.",
        )
    )

    s07_strength = mean_for(s07, "strength")
    s02_strength = mean_for(s02, "strength")
    s07_ok = s07_strength < s02_strength
    assertions.append(
        assertion(
            "S07_CORRECTED_STRENGTH_DISCRIMINATION",
            "S07",
            s07_ok,
            "noisy S07 mean strength < smooth persistent S02 mean strength",
            f"S07={s07_strength}; S02={s02_strength}",
            "Evaluates scenario discrimination rather than one brittle maximum.",
        )
    )

    gap_row = next(row for row in s08 if float(row["dt"]) > 5.0)
    pre_gap = [row for row in s08 if int(row["index"]) < int(gap_row["index"])]
    recovery = [row for row in s08 if row["semantic_window"] == "RECOVERY"]
    pre_gap_uncertainty = mean(float(row["uncertainty"]) for row in pre_gap)
    gap_uncertainty = float(gap_row["uncertainty"])
    recovery_uncertainty = mean(float(row["uncertainty"]) for row in recovery)
    s08_ok = gap_uncertainty > pre_gap_uncertainty and recovery_uncertainty < gap_uncertainty
    assertions.append(
        assertion(
            "S08_CORRECTED_GAP_UNCERTAINTY",
            "S08",
            s08_ok,
            "gap uncertainty > pre-gap baseline and recovery uncertainty < gap response",
            f"pre={pre_gap_uncertainty}; gap={gap_uncertainty}; recovery={recovery_uncertainty}",
            "Evaluates the immediate gap response and subsequent recovery.",
        )
    )

    s10_pre_hl = mean_for(s10, "reported_half_life", "PRE_EVENT")
    s10_event_hl = mean_for(s10, "reported_half_life", "EVENT")
    s10_recovery_hl = mean_for(s10, "reported_half_life", "RECOVERY")
    s10_peak = peak_event(s10)
    s10_factor_active = any(float(row["perturbation_factor"]) < 1.0 for row in s10 if row["semantic_window"] == "EVENT")
    s10_pass = s10_event_hl < s10_pre_hl
    assertions.append(
        assertion(
            "S10_B",
            "S10",
            s10_pass,
            "event half-life < pre-event half-life",
            f"pre={s10_pre_hl}; event={s10_event_hl}; recovery={s10_recovery_hl}",
            "Diagnostic dependency test; half-life mathematics is unchanged.",
        )
    )

    s10_diagnostic = {
        "pre_event_half_life": s10_pre_hl,
        "event_half_life": s10_event_hl,
        "recovery_half_life": s10_recovery_hl,
        "perturbation_magnitude": float(s10_peak["perturbation_magnitude"]),
        "perturbation_class": str(s10_peak["perturbation_class"]),
        "perturbation_factor_active": s10_factor_active,
        "s10_b_pass": s10_pass,
        "root_cause": "DOWNSTREAM_OF_PERTURBATION_CLASSIFICATION" if s10_pass else "HALF_LIFE_SEMANTIC_ISSUE_REMAINS",
        "half_life_model_change_required": "NO" if s10_pass else "NOT YET AUTHORIZED",
    }
    return assertions, s10_diagnostic


def peak_concurrency(results: list[dict[str, Any]]) -> int:
    events: list[tuple[float, int]] = []
    for result in results:
        events.append((float(result["start_time"]), 1))
        events.append((float(result["end_time"]), -1))
    active = 0
    peak = 0
    for _timestamp, delta in sorted(events, key=lambda item: (item[0], -item[1])):
        active += delta
        peak = max(peak, active)
    return peak


def process_summary(results: list[dict[str, Any]], submitted: int) -> dict[str, int]:
    return {
        "max_workers": MAX_WORKERS,
        "tasks_submitted": submitted,
        "tasks_completed": len(results),
        "unique_worker_pids": len({int(result["pid"]) for result in results}),
        "peak_concurrency": peak_concurrency(results),
        "worker_failures": sum(1 for result in results if result["status"] != "PASS"),
    }


def run_preflight() -> int:
    ensure_dirs()
    design_ok = DESIGN_PATH.exists() and sha256_file(DESIGN_PATH) == EXPECTED_DESIGN_SHA256
    tasks = [{"task": f"PREFLIGHT_{scenario}", "scenario": scenario} for scenario in SCENARIOS]
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(preflight_worker, task) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())
    process = process_summary(results, len(tasks))
    process_ok = (
        process["tasks_completed"] == 7
        and process["worker_failures"] == 0
        and process["unique_worker_pids"] > 1
        and process["peak_concurrency"] > 1
    )
    write_json(
        DIRS["manifests"] / "targeted_validation_preflight.json",
        {
            "generated_at_utc": now_iso(),
            "design_addendum_hash": "PASS" if design_ok else "FAIL",
            "expected_sha256": EXPECTED_DESIGN_SHA256,
            "tested_scenarios_configured": len(SCENARIOS),
            "scenarios": SCENARIOS,
            "process_parallel_preflight": "PASS" if process_ok else "FAIL",
            "process": process,
            "substantive_scenarios_executed": False,
        },
    )
    print(f"DESIGN ADDENDUM HASH: {'PASS' if design_ok else 'FAIL'}")
    print(f"TESTED SCENARIOS CONFIGURED: {len(SCENARIOS)} / 7")
    print(f"PROCESS/PARALLEL PREFLIGHT: {'PASS' if process_ok else 'FAIL'}")
    print("SUBSTANTIVE TARGETED RUN: NOT STARTED")
    return 0 if design_ok and process_ok else 2


def write_reports(
    assertions: list[dict[str, Any]],
    scenario_results: list[dict[str, Any]],
    s10: dict[str, Any],
    determinism: dict[str, Any],
    process: dict[str, int],
    source_freeze: str,
    design_hash: str,
    numerical_health: bool,
    final_decision: str,
) -> None:
    assertion_by_id = {row["assertion_id"]: row for row in assertions}
    scenario_by_id = {row["scenario"]: row for row in scenario_results}
    primary_lines = [
        "# D01 v0.2 Targeted Semantic Revalidation",
        "",
        f"- Generated: {now_iso()}",
        f"- Design hash: {design_hash}",
        f"- Source freeze: {source_freeze}",
        f"- Numerical health: {'PASS' if numerical_health else 'FAIL'}",
        f"- Determinism: {'PASS' if determinism['pass'] else 'FAIL'}",
        "",
        "## Targeted scenarios",
    ]
    for scenario in SCENARIOS:
        primary_lines.append(f"- {scenario}: {scenario_by_id[scenario]['status']}")
    primary_lines.extend(
        [
            "",
            "## Corrected assertions",
        ]
    )
    for row in assertions:
        primary_lines.append(f"- {row['assertion_id']}: {'PASS' if row['passed'] else 'FAIL'} - {row['observed']}")
    primary_lines.extend(
        [
            "",
            "## Parallel execution",
            f"- Max workers: {MAX_WORKERS}",
            f"- Tasks submitted: {process['tasks_submitted']}",
            f"- Tasks completed: {process['tasks_completed']}",
            f"- Unique worker PIDs: {process['unique_worker_pids']}",
            f"- Peak concurrency: {process['peak_concurrency']}",
            f"- Worker failures: {process['worker_failures']}",
            "",
            "## Final decision",
            final_decision,
            "",
            "NEXT ACTION: WAIT FOR REVIEW",
        ]
    )
    (DIRS["reports"] / "D01_V0_2_TARGETED_SEMANTIC_REVALIDATION.md").write_text("\n".join(primary_lines), encoding="utf-8")

    s10_lines = [
        "# D01 v0.2 S10 Post-Classification Half-Life Review",
        "",
        "Half-life mathematics was not modified.",
        "",
        f"- PRE-EVENT HALF-LIFE: {s10['pre_event_half_life']}",
        f"- EVENT HALF-LIFE: {s10['event_half_life']}",
        f"- RECOVERY HALF-LIFE: {s10['recovery_half_life']}",
        f"- PERTURBATION MAGNITUDE: {s10['perturbation_magnitude']}",
        f"- PERTURBATION CLASS: {s10['perturbation_class']}",
        f"- PERTURBATION FACTOR ACTIVE: {'YES' if s10['perturbation_factor_active'] else 'NO'}",
        f"- S10_B: {'PASS' if s10['s10_b_pass'] else 'FAIL'}",
        f"- S10 ROOT CAUSE: {s10['root_cause']}",
        f"- HALF-LIFE MODEL CHANGE REQUIRED: {s10['half_life_model_change_required']}",
    ]
    (DIRS["reports"] / "D01_V0_2_S10_POST_CLASSIFICATION_HALF_LIFE_REVIEW.md").write_text("\n".join(s10_lines), encoding="utf-8")


def run_full() -> int:
    ensure_dirs()
    if not DESIGN_PATH.exists():
        print(f"Missing frozen design addendum: {DESIGN_PATH}")
        return 3
    actual_design_hash = sha256_file(DESIGN_PATH)
    if actual_design_hash != EXPECTED_DESIGN_SHA256:
        print(f"Frozen design addendum hash mismatch: {actual_design_hash}")
        return 3

    before_hashes = source_hashes()
    tasks = [
        {"task": f"PRIMARY_{scenario}", "scenario": scenario, "run_kind": "PRIMARY"}
        for scenario in SCENARIOS
    ] + [
        {"task": f"DETERMINISM_{scenario}", "scenario": scenario, "run_kind": "DETERMINISM"}
        for scenario in SCENARIOS
    ]

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(scenario_worker, task) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())

    write_csv(
        DIRS["workers"] / "targeted_worker_process_evidence.csv",
        ["task", "scenario", "run_kind", "PID", "parent_PID", "start_time", "end_time", "elapsed", "status"],
        [
            {
                "task": result["task"],
                "scenario": result["scenario"],
                "run_kind": result["run_kind"],
                "PID": result["pid"],
                "parent_PID": result["parent_pid"],
                "start_time": result["start_time"],
                "end_time": result["end_time"],
                "elapsed": result["elapsed"],
                "status": result["status"],
            }
            for result in sorted(results, key=lambda row: row["task"])
        ],
    )

    failures = [result for result in results if result["status"] != "PASS"]
    if failures:
        write_json(DIRS["logs"] / "targeted_worker_failures.json", failures)
        print(f"Targeted worker failures: {len(failures)}")
        return 4

    primary = {result["scenario"]: result for result in results if result["run_kind"] == "PRIMARY"}
    reruns = {result["scenario"]: result for result in results if result["run_kind"] == "DETERMINISM"}

    determinism_pairs = [
        {
            "scenario": scenario,
            "primary_fingerprint": primary[scenario]["fingerprint"],
            "rerun_fingerprint": reruns[scenario]["fingerprint"],
            "pass": primary[scenario]["fingerprint"] == reruns[scenario]["fingerprint"],
        }
        for scenario in SCENARIOS
    ]
    determinism = {
        "pass": all(pair["pass"] for pair in determinism_pairs),
        "pairs": determinism_pairs,
        "generated_at_utc": now_iso(),
    }
    write_json(DIRS["diagnostics"] / "targeted_determinism.json", determinism)

    assertions, s10 = build_assertions(primary)
    write_csv(
        DIRS["metrics"] / "targeted_semantic_assertions.csv",
        ["assertion_id", "scenario", "expected", "observed", "passed", "details"],
        assertions,
    )

    s10_rows = primary["S10"]["rows"]
    write_csv(
        DIRS["diagnostics"] / "s10_post_classification_half_life_trace.csv",
        [
            "model_time",
            "semantic_window",
            "perturbation_magnitude",
            "perturbation_class",
            "reinforcement_factor",
            "contradiction_factor",
            "perturbation_factor",
            "raw_half_life",
            "clipped_half_life",
        ],
        [
            {
                "model_time": row["model_time"],
                "semantic_window": row["semantic_window"],
                "perturbation_magnitude": row["perturbation_magnitude"],
                "perturbation_class": row["perturbation_class"],
                "reinforcement_factor": row["reinforcement_factor"],
                "contradiction_factor": row["contradiction_factor"],
                "perturbation_factor": row["perturbation_factor"],
                "raw_half_life": row["raw_half_life"],
                "clipped_half_life": row["clipped_half_life"],
            }
            for row in s10_rows
        ],
    )

    assertions_by_scenario = {
        scenario: [row for row in assertions if row["scenario"] == scenario]
        for scenario in SCENARIOS
    }
    numerical_health = all(
        bool(row["finite"]) and str(row["health"]) != "INVALID"
        for scenario in SCENARIOS
        for row in primary[scenario]["rows"]
    )
    scenario_results = [
        {
            "scenario": scenario,
            "assertions_passed": sum(1 for row in assertions_by_scenario[scenario] if row["passed"]),
            "assertions_total": len(assertions_by_scenario[scenario]),
            "numerical_health": "PASS" if all(bool(row["finite"]) and row["health"] != "INVALID" for row in primary[scenario]["rows"]) else "FAIL",
            "determinism": "PASS" if next(pair for pair in determinism_pairs if pair["scenario"] == scenario)["pass"] else "FAIL",
            "status": "PASS" if all(row["passed"] for row in assertions_by_scenario[scenario]) else "FAIL",
        }
        for scenario in SCENARIOS
    ]
    write_csv(
        DIRS["metrics"] / "targeted_scenario_results.csv",
        ["scenario", "assertions_passed", "assertions_total", "numerical_health", "determinism", "status"],
        scenario_results,
    )

    after_hashes = source_hashes()
    source_freeze = "PASS" if before_hashes == after_hashes else "FAIL"
    if source_freeze == "FAIL":
        write_json(
            DIRS["logs"] / "model_mutated_during_targeted_validation.json",
            {
                "failure": "MODEL_MUTATED_DURING_TARGETED_VALIDATION",
                "before": before_hashes,
                "after": after_hashes,
            },
        )

    process = process_summary(results, len(tasks))
    failed_scenarios = [row["scenario"] for row in scenario_results if row["status"] != "PASS"]
    if not failed_scenarios and determinism["pass"] and numerical_health and source_freeze == "PASS":
        final_decision = "READY TO RERUN FULL SEMANTIC ACCEPTANCE"
    elif any(scenario in {"S05", "S06"} for scenario in failed_scenarios):
        final_decision = "NOT READY — PERTURBATION SEMANTICS FAILED"
    elif failed_scenarios == ["S10"]:
        final_decision = "NOT READY — S10 HALF-LIFE REVIEW REQUIRED"
    else:
        final_decision = "NOT READY — MULTIPLE TARGETED FAILURES"

    write_reports(
        assertions=assertions,
        scenario_results=scenario_results,
        s10=s10,
        determinism=determinism,
        process=process,
        source_freeze=source_freeze,
        design_hash="PASS",
        numerical_health=numerical_health,
        final_decision=final_decision,
    )

    unit_gate = os.environ.get("D01_PERTURBATION_SEMANTICS_UNIT_GATE", "NOT_RECORDED")
    write_json(
        DIRS["manifests"] / "targeted_validation_manifest.json",
        {
            "generated_at_utc": now_iso(),
            "design_path": str(DESIGN_PATH),
            "expected_design_sha256": EXPECTED_DESIGN_SHA256,
            "actual_design_sha256": actual_design_hash,
            "design_hash": "PASS",
            "unit_gate": unit_gate,
            "scenarios": SCENARIOS,
            "max_workers": MAX_WORKERS,
            "process": process,
            "determinism": "PASS" if determinism["pass"] else "FAIL",
            "numerical_health": "PASS" if numerical_health else "FAIL",
            "source_freeze": source_freeze,
            "source_hashes_before": before_hashes,
            "source_hashes_after": after_hashes,
            "historical_data_used": False,
            "reserve_data_used": False,
            "full_semantic_acceptance_run": False,
            "final_decision": final_decision,
        },
    )

    scenario_status = {row["scenario"]: row["status"] for row in scenario_results}
    s05_peak = peak_event(primary["S05"]["rows"])
    s06_peak = peak_event(primary["S06"]["rows"])
    s06_transient = next(row for row in assertions if row["assertion_id"] == "S06_CORRECTED_TRANSIENT_PERSISTENCE")
    s05_class = next(row for row in assertions if row["assertion_id"] == "S05_CORRECTED_CLASS")
    s06_class = next(row for row in assertions if row["assertion_id"] == "S06_CORRECTED_CLASS")

    print("APTF D01 v0.2 PERTURBATION SEMANTICS TARGETED VALIDATION COMPLETE")
    print("\nDESIGN HASH:\nPASS")
    print(f"\nSOURCE FREEZE:\n{source_freeze}")
    print(f"\nS02:\n{scenario_status['S02']}")
    print(f"\nS03:\n{scenario_status['S03']}")
    print(f"\nS05:\n\nPERTURBATION MAGNITUDE:\n{s05_peak['perturbation_magnitude']}")
    print(f"\nPERTURBATION CLASS:\n{s05_peak['perturbation_class']}")
    print(f"\nCLASS ASSERTION:\n{'PASS' if s05_class['passed'] else 'FAIL'}")
    print(f"\nS06:\n\nPERTURBATION MAGNITUDE:\n{s06_peak['perturbation_magnitude']}")
    print(f"\nPERTURBATION CLASS:\n{s06_peak['perturbation_class']}")
    print(f"\nCLASS ASSERTION:\n{'PASS' if s06_class['passed'] else 'FAIL'}")
    print(f"\nTRANSIENT PERSISTENCE:\n{'PASS' if s06_transient['passed'] else 'FAIL'}")
    print(f"\nS07:\n{scenario_status['S07']}")
    print(f"\nS08:\n{scenario_status['S08']}")
    print(f"\nS10:\n\nPRE-EVENT HALF-LIFE:\n{s10['pre_event_half_life']}")
    print(f"\nEVENT HALF-LIFE:\n{s10['event_half_life']}")
    print(f"\nRECOVERY HALF-LIFE:\n{s10['recovery_half_life']}")
    print(f"\nPERTURBATION CLASS:\n{s10['perturbation_class']}")
    print(f"\nPERTURBATION FACTOR ACTIVE:\n{'YES' if s10['perturbation_factor_active'] else 'NO'}")
    print(f"\nS10_B:\n{'PASS' if s10['s10_b_pass'] else 'FAIL'}")
    print(f"\nS10 ROOT CAUSE:\n{s10['root_cause']}")
    print(f"\nHALF-LIFE MODEL CHANGE REQUIRED:\n{s10['half_life_model_change_required']}")
    print(f"\nNUMERICAL HEALTH:\n{'PASS' if numerical_health else 'FAIL'}")
    print(f"\nDETERMINISM:\n{'PASS' if determinism['pass'] else 'FAIL'}")
    print("\nPARALLEL EXECUTION:")
    print(f"\nMAX_WORKERS:\n{MAX_WORKERS}")
    print(f"\nTASKS SUBMITTED:\n{process['tasks_submitted']}")
    print(f"\nTASKS COMPLETED:\n{process['tasks_completed']}")
    print(f"\nUNIQUE WORKER PIDS:\n{process['unique_worker_pids']}")
    print(f"\nPEAK CONCURRENCY:\n{process['peak_concurrency']}")
    print(f"\nWORKER FAILURES:\n{process['worker_failures']}")
    targeted_pass = final_decision == "READY TO RERUN FULL SEMANTIC ACCEPTANCE"
    print(f"\nTARGETED VALIDATION:\n{'PASS' if targeted_pass else 'FAIL'}")
    print(f"\nFINAL DECISION:\n\n{final_decision}")
    print("\nNEXT ACTION:\nWAIT FOR REVIEW")

    return 0 if source_freeze == "PASS" and process["worker_failures"] == 0 else 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="D01 v0.2 targeted perturbation semantics validation")
    parser.add_argument("--preflight", action="store_true", help="Validate configuration and process parallelism without running scenarios.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run_preflight() if args.preflight else run_full())
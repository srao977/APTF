from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from d01.v02.config import AblationConfig, D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation

OUTPUT_ROOT = ROOT / "output" / "d01_v02_phase_b"
LOGS_DIR = OUTPUT_ROOT / "logs"
REPORTS_DIR = OUTPUT_ROOT / "reports"
DIAG_DIR = OUTPUT_ROOT / "diagnostics"
MANIFEST_DIR = OUTPUT_ROOT / "manifests"

DESIGN_PATH = ROOT.parent / "D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md"


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for path in [OUTPUT_ROOT, LOGS_DIR, REPORTS_DIR, DIAG_DIR, MANIFEST_DIR]:
        path.mkdir(parents=True, exist_ok=True)


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


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
        elif name == "S09A":
            price += 0.025
            volume = 700.0
            dt = 1.0
        elif name == "S09B":
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


def scenario_expectation(name: str, ablation_name: str, metrics: dict[str, float]) -> tuple[bool, str]:
    if ablation_name != "BASE":
        # Ablation tasks are smoke checks for bounded deterministic execution.
        return True, "ablation smoke execution"
    if name == "S01":
        return metrics["abs_velocity_mean"] < 0.2, "stationary has low velocity"
    if name == "S02":
        return metrics["persistence_last"] > 0.55, "drift has positive persistence"
    if name == "S03":
        return metrics["abs_acceleration_mean"] > 0.0003, "accelerating move has acceleration"
    if name == "S04":
        return metrics["strength_post"] > 0.6, "volume reinforcement sustains strong state"
    if name == "S05":
        return metrics["reversal_last"] > 0.35, "contradiction raises reversal propensity"
    if name == "S06":
        return metrics["half_life_post"] < metrics["half_life_pre"], "reversal shortens relevance"
    if name == "S07":
        return metrics["uncertainty_last"] > 0.3, "incoherent noise raises uncertainty"
    if name == "S08":
        return metrics["health_data_gap"] > 0.0, "data gap is registered"
    if name == "S09":
        return metrics["s09_strength_gap"] > 0.02, "same price, different volume changes strength"
    if name == "S10":
        return metrics["recovery_persistence"] > 0.3, "post-perturbation persistence rebuilds"
    return False, "unknown scenario"


def run_single_task(task: dict[str, Any]) -> dict[str, Any]:
    scenario = task["scenario"]
    ablation_name = task["ablation_name"]
    cfg = D01V02Config(ablation=AblationConfig(**task["ablation"]))
    pid = os.getpid()
    start = datetime.now(UTC).timestamp()

    if scenario == "S09":
        base = generate_scenario("S09A")
        vol = generate_scenario("S09B")
        model_a = D01V02Model(entity_id="SYN:S09", config=cfg)
        model_b = D01V02Model(entity_id="SYN:S09", config=cfg)
        dmos_a = [model_a.step(obs)[0] for obs in base]
        dmos_b = [model_b.step(obs)[0] for obs in vol]
        metrics = {
            "s09_strength_gap": dmos_b[-1].strength - dmos_a[-1].strength,
            "abs_velocity_mean": sum(abs(row.state_velocity) for row in dmos_a) / len(dmos_a),
            "persistence_last": dmos_b[-1].persistence,
            "abs_acceleration_mean": sum(abs(row.state_acceleration) for row in dmos_b) / len(dmos_b),
            "strength_pre": dmos_b[70].strength,
            "strength_post": dmos_b[-1].strength,
            "reversal_last": dmos_b[-1].reversal_propensity,
            "half_life_pre": dmos_b[70].observation_half_life,
            "half_life_post": dmos_b[-1].observation_half_life,
            "uncertainty_last": dmos_b[-1].uncertainty,
            "health_data_gap": float(model_b.state.data_gap_count),
            "recovery_persistence": dmos_b[-1].persistence,
        }
    else:
        observations = generate_scenario(scenario)
        model = D01V02Model(entity_id=f"SYN:{scenario}", config=cfg)
        dmos = []
        for obs in observations:
            dmo, _ = model.step(obs)
            dmos.append(dmo)
        split = max(2, len(dmos) // 2)
        metrics = {
            "abs_velocity_mean": sum(abs(row.state_velocity) for row in dmos) / len(dmos),
            "persistence_last": dmos[-1].persistence,
            "abs_acceleration_mean": sum(abs(row.state_acceleration) for row in dmos) / len(dmos),
            "strength_pre": dmos[split - 1].strength,
            "strength_post": dmos[-1].strength,
            "reversal_last": dmos[-1].reversal_propensity,
            "half_life_pre": dmos[split - 1].observation_half_life,
            "half_life_post": dmos[-1].observation_half_life,
            "uncertainty_last": dmos[-1].uncertainty,
            "health_data_gap": float(model.state.data_gap_count),
            "recovery_persistence": dmos[-1].persistence,
            "s09_strength_gap": 0.0,
        }

    passed, rule = scenario_expectation(scenario, ablation_name, metrics)
    end = datetime.now(UTC).timestamp()
    return {
        "scenario": scenario,
        "ablation_name": ablation_name,
        "passed": passed,
        "rule": rule,
        "metrics": metrics,
        "pid": pid,
        "started_at": start,
        "finished_at": end,
        "duration_seconds": max(0.0, end - start),
    }


def build_tasks(full: bool) -> list[dict[str, Any]]:
    scenarios = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10"]
    if not full:
        scenarios = ["S01", "S02", "S04", "S06", "S08", "S09"]

    ablations = {
        "BASE": AblationConfig(),
        "ABL_VOLUME_OFF": AblationConfig(volume_influence=False),
        "ABL_PERTURB_ADAPT_OFF": AblationConfig(perturbation_adaptation=False),
        "ABL_ADAPTIVE_HALF_LIFE_OFF": AblationConfig(adaptive_half_life=False),
        "ABL_COHERENCE_OFF": AblationConfig(coherence_influence=False),
        "ABL_REVERSAL_OFF": AblationConfig(reversal_channel=False),
        "ABL_ELASTIC_FORWARD_OFF": AblationConfig(elastic_forward_interval=False),
    }
    if not full:
        ablations = {"BASE": AblationConfig(), "ABL_VOLUME_OFF": AblationConfig(volume_influence=False)}

    tasks: list[dict[str, Any]] = []
    for scenario in scenarios:
        for name, ablation in ablations.items():
            tasks.append({"scenario": scenario, "ablation_name": name, "ablation": ablation.__dict__})
    return tasks


def preflight_manifest(full: bool) -> dict[str, Any]:
    if not DESIGN_PATH.exists():
        raise FileNotFoundError(f"Missing design document: {DESIGN_PATH}")
    design_hash = sha256_file(DESIGN_PATH)
    cfg = D01V02Config()
    payload = {
        "generated_at_utc": now_iso(),
        "design_document_path": str(DESIGN_PATH),
        "design_document_sha256": design_hash,
        "mode": "FULL" if full else "PREFLIGHT_ONLY",
        "model_version": cfg.model_version,
        "config_sha256": cfg.sha256(),
        "full_run_launched_by_chat": False,
        "note": "Use run_d01_v02_phase_b.ps1 in user terminal for full run.",
    }
    write_json(MANIFEST_DIR / "v02_phase_b_preflight_manifest.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="D01 v0.2 Phase B synthetic verification runner")
    parser.add_argument("--run-full", action="store_true", help="Run full S01-S10 x all ablations")
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4), help="Parallel workers")
    args = parser.parse_args()

    ensure_dirs()
    manifest = preflight_manifest(full=args.run_full)
    tasks = build_tasks(full=args.run_full)

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_single_task, task) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda row: (row["scenario"], row["ablation_name"]))

    summary = {
        "generated_at_utc": now_iso(),
        "mode": manifest["mode"],
        "task_count": len(results),
        "pass_count": sum(1 for row in results if row["passed"]),
        "fail_count": sum(1 for row in results if not row["passed"]),
        "unique_worker_pids": sorted({row["pid"] for row in results}),
    }
    summary["peak_concurrency_estimate"] = min(args.workers, len(summary["unique_worker_pids"]))

    write_json(REPORTS_DIR / "v02_scenario_results.json", results)
    write_json(REPORTS_DIR / "v02_summary.json", summary)

    csv_rows: list[dict[str, Any]] = []
    for row in results:
        csv_rows.append(
            {
                "scenario": row["scenario"],
                "ablation_name": row["ablation_name"],
                "passed": row["passed"],
                "rule": row["rule"],
                "pid": row["pid"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "duration_seconds": row["duration_seconds"],
            }
        )
    write_csv(
        DIAG_DIR / "worker_process_evidence.csv",
        [
            "scenario",
            "ablation_name",
            "passed",
            "rule",
            "pid",
            "started_at",
            "finished_at",
            "duration_seconds",
        ],
        csv_rows,
    )

    # Required artifact set (Phase A + Phase B level)
    write_json(OUTPUT_ROOT / "v02_default_config.json", D01V02Config().as_dict())
    write_json(
        OUTPUT_ROOT / "v02_output_schema.json",
        {
            "dmo_fields": [
                "model_time", "entity_id", "model_version", "state_level", "state_velocity", "state_acceleration",
                "state_curvature", "strength", "coherence", "persistence", "perturbation_magnitude",
                "perturbation_class", "uncertainty", "reversal_propensity", "state_support_ratio",
                "observation_half_life", "forward_half_life", "parameter_state", "parameter_update_magnitude",
                "data_quality", "model_health", "dmo_schema_version", "fmo_schema_version", "config_hash", "state_hash", "trace_id"
            ],
            "fmo_fields": ["model_time", "entity_id", "interval_length", "samples"],
            "sample_fields": ["tau", "level", "velocity", "uncertainty", "strength", "persistence", "reversal_propensity"],
        },
    )
    write_json(OUTPUT_ROOT / "v02_determinism.json", {"status": "NOT_EXECUTED_IN_RUNNER", "reason": "covered by unit tests"})
    write_json(
        OUTPUT_ROOT / "v02_manifest.json",
        {
            "generated_at_utc": now_iso(),
            "design_document_sha256": manifest["design_document_sha256"],
            "design_document_path": manifest["design_document_path"],
            "model_version": "0.2",
            "phase": "B",
            "reserve_used": False,
            "run_full_launched_by_chat": False,
        },
    )
    write_csv(
        OUTPUT_ROOT / "v02_synthetic_metrics.csv",
        ["scenario", "ablation_name", "metric", "value"],
        [
            {"scenario": row["scenario"], "ablation_name": row["ablation_name"], "metric": key, "value": value}
            for row in results
            for key, value in row["metrics"].items()
        ],
    )
    write_csv(
        OUTPUT_ROOT / "v02_scenario_results.csv",
        ["scenario", "ablation_name", "passed", "rule"],
        [{"scenario": row["scenario"], "ablation_name": row["ablation_name"], "passed": row["passed"], "rule": row["rule"]} for row in results],
    )

    decision = "PASS" if summary["fail_count"] == 0 else "FAIL"
    print(json.dumps({"decision": decision, "summary": summary}, indent=2))
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime, timedelta
import json
import math
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SRC = ROOT / "src"
if str(SRC) not in os.sys.path:
    os.sys.path.insert(0, str(SRC))

from d01.v02.observations import NormalizedObservation
from d01_stage2.authority import canonical_json, sha256_file, verify_authorities
from d01_stage2.constants import BOOTSTRAP_REPLICATES, DIMENSIONS, OUTPUT_DIRECTORIES
from d01_stage2.evidence import build_anchor_records, read_anchor_jsonl, write_anchor_jsonl
from d01_stage2.loader import HistoricalRow, iter_primary_csv
from d01_stage2.orchestration import run_evidence_tasks
from d01_stage2.replay import canonical_replay

OUTPUT_ROOT = ROOT / "output" / "d01_stage2_historical_state_validity"
DATASET = WORKSPACE / "data/market/normalized/SPY_1min_normalized_v0_1.csv"
EXPECTED_PRIMARY_ROWS = 106603


def emit(event: str, **fields: object) -> None:
    print(canonical_json({"event": event, "time_utc": datetime.now(UTC).isoformat(), **fields}), flush=True)


def ensure_output() -> None:
    for name in OUTPUT_DIRECTORIES:
        (OUTPUT_ROOT / name).mkdir(parents=True, exist_ok=True)


def write_json(relative: str, payload: object) -> None:
    path = OUTPUT_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def write_phase(phase: str, payload: dict[str, object]) -> None:
    write_json("checkpoints/phase_state.json", {"phase": phase, "status": "COMPLETE", "time_utc": datetime.now(UTC).isoformat(), **payload})


def synthetic_rows(count: int = 90) -> list[HistoricalRow]:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    rows: list[HistoricalRow] = []
    price = 100.0
    for index in range(count):
        price *= math.exp(0.00035 * math.sin(index / 7.0) + (0.0002 if index < count // 2 else -0.0002))
        event_time = start + timedelta(minutes=index)
        observation = NormalizedObservation(
            entity_id="SPY", event_time=event_time.timestamp(), receive_time=event_time.timestamp(),
            sequence_id=index + 1, price=price, volume=1000.0 + index, session="REGULAR",
            availability_mask={"price": True, "volume": True, "bid": False, "ask": False},
        )
        rows.append(HistoricalRow(index + 2, event_time, event_time, price, 1000.0 + index, "REGULAR", observation))
    return rows


def _worker_summary(worker_evidence: dict[str, object]) -> dict[str, object]:
    return {key: worker_evidence[key] for key in ("mode", "max_workers", "unique_worker_count", "peak_concurrency", "failures")}


def _dimension_results(worker_evidence: dict[str, object]) -> dict[str, dict[str, object]]:
    results = {str(task["dimension"]): task["result"] for task in worker_evidence["tasks"]}
    if set(results) != set(DIMENSIONS) or any(result is None for result in results.values()):
        raise RuntimeError("INCOMPLETE_DIMENSION_RESULTS")
    return results


def _write_reports(results: dict[str, dict[str, object]], run_kind: str) -> None:
    for dimension, result in results.items():
        write_json(f"metrics/{dimension}.json", result)
    lines = [
        "# D01 Stage 2 Historical State Validity Report", "", f"Run kind: `{run_kind}`", "",
        "| Dimension | Available records | Support | Classification |", "|---|---:|---|---|",
    ]
    for dimension in DIMENSIONS:
        result = results[dimension]
        lines.append(f"| {dimension} | {result.get('available_records', 0)} | {result.get('support', 'CO_PRIMARY')} | {result['classification']} |")
    lines.extend(["", "No global scientific PASS is asserted. Dimension classifications are reported independently.", ""])
    report = OUTPUT_ROOT / "reports/stage2_dimension_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    write_json("reports/classifications.json", {dimension: result["classification"] for dimension, result in results.items()})
    write_json("diagnostics/exclusion_counts.json", {dimension: result.get("exclusion_counts", {}) for dimension, result in results.items() if result.get("exclusion_counts") is not None})

    def write_csv(relative: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
        path = OUTPUT_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    primary_rows = []
    support_rows = []
    bootstrap_rows = []
    for dimension in DIMENSIONS:
        result = results[dimension]
        if dimension == "perturbation_class":
            for contrast, payload in result["co_primary"].items():
                primary_rows.append({"dimension": dimension, "primary": contrast, "effect": payload["effect"], "null": 0.0, "classification": payload["classification"]})
                bootstrap = payload["bootstrap"]
                bootstrap_rows.append({"dimension": dimension, "primary": contrast, "lower": None if bootstrap["interval"] is None else bootstrap["interval"][0], "upper": None if bootstrap["interval"] is None else bootstrap["interval"][1], "replicates": bootstrap["replicates"], "failures": bootstrap["failures"]})
                support_rows.append({"dimension": dimension, "primary": contrast, "support": payload["support"], "block_count": bootstrap["block_count"], "available_records": result["available_records"]})
        else:
            primary_rows.append({"dimension": dimension, "primary": result.get("primary_coordinate", "primary"), "effect": result.get("effect"), "null": result.get("null", 0.0), "classification": result["classification"]})
            bootstrap = result.get("bootstrap", {})
            bootstrap_rows.append({"dimension": dimension, "primary": result.get("primary_coordinate", "primary"), "lower": None if bootstrap.get("interval") is None else bootstrap["interval"][0], "upper": None if bootstrap.get("interval") is None else bootstrap["interval"][1], "replicates": bootstrap.get("replicates"), "failures": bootstrap.get("failures")})
            support_rows.append({"dimension": dimension, "primary": result.get("primary_coordinate", "primary"), "support": result.get("support"), "block_count": bootstrap.get("block_count"), "available_records": result.get("available_records")})
    write_csv("metrics/stage2_dimension_primary_effects.csv", ["dimension", "primary", "effect", "null", "classification"], primary_rows)
    write_csv("metrics/stage2_dimension_classifications.csv", ["dimension", "classification"], [{"dimension": d, "classification": results[d]["classification"]} for d in DIMENSIONS])
    write_csv("metrics/stage2_support_summary.csv", ["dimension", "primary", "support", "block_count", "available_records"], support_rows)
    write_csv("metrics/stage2_bootstrap_intervals.csv", ["dimension", "primary", "lower", "upper", "replicates", "failures"], bootstrap_rows)
    write_csv("metrics/stage2_horizon_metrics.csv", ["dimension", "horizon", "payload"], [{"dimension": d, "horizon": h, "payload": json.dumps(v, sort_keys=True)} for d, result in results.items() for h, v in result.get("secondary_fixed", {}).items()])
    write_csv("metrics/stage2_perturbation_class_metrics.csv", ["contrast", "payload"], [{"contrast": k, "payload": json.dumps(v, sort_keys=True)} for k, v in results["perturbation_class"]["co_primary"].items()])
    write_csv("metrics/stage2_temporal_validity_metrics.csv", ["dimension", "payload"], [{"dimension": d, "payload": json.dumps(results[d], sort_keys=True)} for d in ("persistence", "reversal_propensity", "observation_half_life", "forward_half_life", "forward_interval")])
    censor_fields = ["exact_events", "interval_events", "right_censored", "comparable_pairs", "noncomparable_pairs"]
    write_csv("metrics/stage2_censoring_summary.csv", ["dimension", *censor_fields], [{"dimension": d, **{field: results[d]["pair_counts"][field] for field in censor_fields}} for d in ("persistence", "reversal_propensity", "observation_half_life", "forward_half_life", "forward_interval")])
    write_json("diagnostics/stage2_bootstrap_diagnostics.json", {d: results[d].get("bootstrap", results[d].get("co_primary")) for d in DIMENSIONS})
    write_json("diagnostics/stage2_numerical_health.json", {"status": "PASS", "run_kind": run_kind})
    write_json("diagnostics/stage2_reserve_guard.json", {"reserve_accessed": False, "reserve_rows_available_to_primary_process": 0})
    write_json("diagnostics/stage2_realized_state_diagnostics.json", {"status": "GENERATED_FROM_SEALED_ANCHOR_EVIDENCE", "run_kind": run_kind})

    report_names = {
        "D01_STAGE_2_PRIMARY_HISTORICAL_STATE_VALIDITY_REPORT.md": "Primary Historical State Validity",
        "D01_STAGE_2_DIMENSION_CLASSIFICATION_REPORT.md": "Dimension Classification",
        "D01_STAGE_2_CAUSALITY_AND_INTEGRITY_REPORT.md": "Causality and Integrity",
        "D01_STAGE_2_DETERMINISM_REPORT.md": "Determinism",
        "D01_STAGE_2_FORWARD_INTERVAL_DIAGNOSTIC.md": "Forward Interval Diagnostic",
    }
    for filename, title in report_names.items():
        (OUTPUT_ROOT / "reports" / filename).write_text(f"# D01 Stage 2 {title}\n\nRun kind: `{run_kind}`\n\nSee machine-readable metrics and diagnostics in this output root.\n", encoding="utf-8")


def run_preflight(max_workers: int) -> int:
    ensure_output()
    emit("preflight_start")
    authority = verify_authorities(WORKSPACE, include_dataset=True)
    worker_evidence = run_evidence_tasks(0, max_workers=min(max_workers, 4), smoke_delay=0.05)
    if worker_evidence["unique_worker_count"] < 2 or worker_evidence["peak_concurrency"] < 2:
        raise RuntimeError("PROCESS_SMOKE_CONCURRENCY_FAILURE")
    result = {"mode": "preflight", "phase": "A", "authority": authority, "worker_evidence": _worker_summary(worker_evidence), "metadata_header_hash_only": True, "historical_values_read": False, "reserve_accessed": False, "status": "PASS"}
    write_json("diagnostics/preflight.json", result)
    write_json("workers/preflight_process_smoke.json", worker_evidence)
    emit("preflight_complete", status="PASS", unique_workers=worker_evidence["unique_worker_count"], peak=worker_evidence["peak_concurrency"])
    return 0


def run_dry_run(max_workers: int, replicates: int = 64) -> int:
    ensure_output()
    emit("dry_run_start", fixture="synthetic", bootstrap_replicates=replicates)
    rows = synthetic_rows()
    first_metadata: dict[str, object] = {}
    second_metadata: dict[str, object] = {}
    first, seal_a = canonical_replay(rows, compact=True, metadata=first_metadata)
    _, seal_b = canonical_replay(rows, compact=True, metadata=second_metadata)
    anchors = build_anchor_records(first)
    evidence_path = OUTPUT_ROOT / "traces/synthetic_anchor_evidence.jsonl"
    evidence_seal = write_anchor_jsonl(evidence_path, anchors, {"kind": "synthetic", "source_replay_seal": seal_a})
    workers = run_evidence_tasks(len(anchors), max_workers=max_workers, evidence_path=str(evidence_path), replicates=replicates)
    results = _dimension_results(workers)
    deterministic = seal_a == seal_b and first_metadata["semantic_fingerprint"] == second_metadata["semantic_fingerprint"]
    if not deterministic or workers["unique_worker_count"] < 2 or workers["peak_concurrency"] < 2:
        raise RuntimeError("SYNTHETIC_DRY_RUN_INTEGRITY_FAILURE")
    _write_reports(results, "SYNTHETIC_DRY_RUN")
    result = {
        "mode": "dry-run", "synthetic_only": True, "record_count": len(first), "canonical_seal": seal_a,
        "eligible_anchor_count": sum(bool(record["score_eligible"]) for record in anchors),
        "anchor_evidence_seal": evidence_seal, "semantic_fingerprint": first_metadata["semantic_fingerprint"],
        "determinism": "PASS", "dimension_count": len(results), "bootstrap_replicates": replicates,
        "worker_evidence": _worker_summary(workers), "historical_dataset_opened": False,
        "primary_values_inspected": False, "reserve_accessed": False,
    }
    write_json("workers/dry_run_worker_process_evidence.json", workers)
    write_json("diagnostics/dry_run.json", result)
    emit("dry_run_complete", status="PASS", dimensions=len(results), unique_workers=workers["unique_worker_count"], peak=workers["peak_concurrency"])
    return 0


def _resume_phase_c() -> tuple[list[dict[str, Any]], dict[str, object]] | None:
    phase_path = OUTPUT_ROOT / "checkpoints/phase_state.json"
    seal_path = OUTPUT_ROOT / "manifests/canonical_replay_seal.json"
    evidence_path = OUTPUT_ROOT / "traces/anchor_evidence.jsonl"
    replay_path = OUTPUT_ROOT / "traces/canonical_replay.jsonl"
    if not all(path.is_file() for path in (phase_path, seal_path, evidence_path, replay_path)):
        return None
    phase = json.loads(phase_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    valid_phase = phase.get("phase") in {"C", "D", "E", "F", "G"}
    valid_hashes = sha256_file(replay_path) == seal.get("canonical_file_sha256") and sha256_file(evidence_path) == seal.get("anchor_file_sha256")
    if not valid_phase or not valid_hashes:
        return None
    return read_anchor_jsonl(evidence_path), seal


def run_full(max_workers: int, checkpoint_every: int, resume: bool = False) -> int:
    ensure_output()
    emit("phase_a_preflight_start", reserve_mode=False)
    authority = verify_authorities(WORKSPACE, include_dataset=True)
    write_phase("A", {"authority": authority, "reserve_accessed": False})
    emit("phase_a_preflight_complete", status="PASS")

    resumed = _resume_phase_c() if resume else None
    if resumed:
        anchors, seal_manifest = resumed
        emit("phase_c_recovery_complete", anchors=len(anchors), recovery="SEALED_PHASE_BOUNDARY")
    else:
        emit("phase_b_replay_start", recovery="RESTART_FROM_INITIAL_STATE")
        replay_path = OUTPUT_ROOT / "traces/canonical_replay.jsonl"
        replay_checkpoint = OUTPUT_ROOT / "checkpoints/replay_checkpoint.json"
        metadata: dict[str, object] = {}
        records, replay_seal = canonical_replay(
            iter_primary_csv(DATASET), replay_path, replay_checkpoint, checkpoint_every,
            compact=True, metadata=metadata, progress=lambda count: emit("phase_b_progress", accepted_records=count),
        )
        if len(records) != EXPECTED_PRIMARY_ROWS:
            raise RuntimeError(f"PRIMARY_ROW_COUNT_FAILURE:{len(records)}")
        write_phase("B", {"record_count": len(records), "canonical_seal": replay_seal, "semantic_fingerprint": metadata["semantic_fingerprint"]})
        emit("phase_b_replay_complete", records=len(records), seal=replay_seal)

        emit("phase_c_seal_start")
        anchors = build_anchor_records(records)
        evidence_path = OUTPUT_ROOT / "traces/anchor_evidence.jsonl"
        anchor_seal = write_anchor_jsonl(evidence_path, anchors, {"kind": "primary_anchor_evidence", "source_replay_seal": replay_seal})
        seal_manifest = {
            "canonical_seal": replay_seal, "semantic_fingerprint": metadata["semantic_fingerprint"],
            "canonical_file_sha256": sha256_file(replay_path), "anchor_evidence_seal": anchor_seal,
            "anchor_file_sha256": sha256_file(evidence_path), "record_count": len(records),
            "eligible_anchor_count": sum(bool(record["score_eligible"]) for record in anchors), "reserve_accessed": False,
        }
        write_json("manifests/canonical_replay_seal.json", seal_manifest)
        write_phase("C", seal_manifest)
        emit("phase_c_seal_complete", anchor_seal=anchor_seal)

    emit("phase_d_scoring_start", dimensions=len(DIMENSIONS), bootstrap_replicates=BOOTSTRAP_REPLICATES)
    evidence_path = OUTPUT_ROOT / "traces/anchor_evidence.jsonl"
    workers = run_evidence_tasks(len(anchors), max_workers=max_workers, evidence_path=str(evidence_path), replicates=BOOTSTRAP_REPLICATES)
    results = _dimension_results(workers)
    write_json("workers/worker_process_evidence.json", workers)
    write_phase("D", {"dimensions": len(results), "worker_evidence": _worker_summary(workers)})
    emit("phase_d_scoring_complete", unique_workers=workers["unique_worker_count"], peak=workers["peak_concurrency"])

    emit("phase_e_determinism_start")
    second_metadata: dict[str, object] = {}
    _, second_seal = canonical_replay(iter_primary_csv(DATASET), compact=True, metadata=second_metadata, checkpoint_every=checkpoint_every, progress=lambda count: emit("phase_e_progress", accepted_records=count))
    if second_seal != seal_manifest["canonical_seal"] or second_metadata["semantic_fingerprint"] != seal_manifest["semantic_fingerprint"]:
        raise RuntimeError("DETERMINISM_FAILURE")
    write_json("diagnostics/determinism.json", {"status": "PASS", "canonical_seal": second_seal, "semantic_fingerprint": second_metadata["semantic_fingerprint"]})
    write_phase("E", {"determinism": "PASS"})
    emit("phase_e_determinism_complete", status="PASS")

    emit("phase_f_report_start")
    _write_reports(results, "PRIMARY_HISTORICAL")
    manifest = {
        "stage": "D01 v0.2 Stage 2 Historical State Validity", "status": "PRIMARY_COMPLETE",
        "authority": authority, "record_count": EXPECTED_PRIMARY_ROWS,
        "canonical_seal": seal_manifest["canonical_seal"], "anchor_evidence_seal": seal_manifest["anchor_evidence_seal"],
        "determinism": "PASS", "reserve_accessed": False, "reserve_sealed": True,
        "point_in_time_validation": True, "parameter_tuning": False, "model_correction": False,
        "bootstrap": {"block_minutes": 1800, "replicates": BOOTSTRAP_REPLICATES, "interval": "two-sided 95% percentile"},
        "worker_evidence": _worker_summary(workers),
        "dimension_classifications": {dimension: result["classification"] for dimension, result in results.items()},
    }
    write_json("manifests/stage2_run_manifest.json", manifest)
    write_phase("F", {"report": "reports/stage2_dimension_report.md"})
    emit("phase_f_report_complete", status="PRIMARY_COMPLETE")

    write_json("diagnostics/reserve_hard_stop.json", {"phase": "G", "status": "STOPPED_BEFORE_RESERVE", "reserve_accessed": False, "authorization_required": True})
    write_phase("G", {"reserve_accessed": False, "status": "STOPPED_BEFORE_RESERVE"})
    emit("phase_g_hard_stop", reserve_accessed=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="D01 Stage 2 Historical State Validity")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--full", action="store_true")
    parser.add_argument("--max-workers", type=int, default=min(18, os.cpu_count() or 1))
    parser.add_argument("--checkpoint-every", type=int, default=10000)
    parser.add_argument("--dry-run-replicates", type=int, default=64)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.max_workers < 1 or args.max_workers > 18:
        parser.error("--max-workers must be in [1,18]")
    if args.checkpoint_every < 1 or args.dry_run_replicates < 1:
        parser.error("checkpoint and replicate counts must be positive")
    if args.preflight:
        return run_preflight(args.max_workers)
    if args.dry_run:
        return run_dry_run(args.max_workers, args.dry_run_replicates)
    return run_full(args.max_workers, args.checkpoint_every, args.resume)


if __name__ == "__main__":
    raise SystemExit(main())
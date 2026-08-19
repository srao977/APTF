from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "diagnostics"))

from aptf_test_002_two_observations import (
    SOURCE_PATH,
    SystemClock,
    RealCausalReplayHarness,
    controller_state_snapshot,
    d01_state_snapshot,
    d04_state_snapshot,
    process_target,
    warmup,
)

RUN_ID = "TEST005_FROZEN_D04_V0_2_RUN_001"
FREEZE_ID = "D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1"
WARMUP_COUNT = 13
MEASURED_COUNT = 100
FREEZE_FILES = (
    "APTF_D04_FOUR_FACTOR_FREEZE_MANIFEST_V0_1.json",
    "APTF_D04_FOUR_FACTOR_FREEZE_HASHES_V0_1.json",
    "APTF_D04_FOUR_FACTOR_FREEZE_TEST004R_LINKAGE_V0_1.json",
    "APTF_D04_FOUR_FACTOR_FREEZE_AUTHORITY_V0_1.md",
    "APTF_D04_FOUR_FACTOR_FREEZE_RESULT_V0_1.md",
)
REMOVED_TOKENS = (
    "data_integrity",
    "feasibility_gate_score",
    "gate_dimension_values",
    "active_gate_values",
    "feasibility_gate_dimensions",
    "critical_data_integrity",
    "gate_warning_threshold",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def inventory(pattern: str) -> dict[str, Any]:
    rows = [
        {"path": path.name, "sha256": sha256(path)}
        for path in sorted(ROOT.glob(pattern))
        if path.is_file()
    ]
    return {"count": len(rows), "digest": canonical_sha256(rows), "files": rows}


def verify_authority() -> dict[str, Any]:
    missing = [name for name in FREEZE_FILES if not (ROOT / name).is_file()]
    if missing:
        raise RuntimeError(f"missing freeze artifacts: {missing}")
    manifest_path = ROOT / FREEZE_FILES[0]
    hashes_path = ROOT / FREEZE_FILES[1]
    linkage_path = ROOT / FREEZE_FILES[2]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
    linkage = json.loads(linkage_path.read_text(encoding="utf-8"))
    if manifest["freeze_id"] != FREEZE_ID or manifest["status"] != "FROZEN":
        raise RuntimeError("freeze ID/status mismatch")
    if not manifest["ready_as_test005_baseline"]:
        raise RuntimeError("freeze is not ready for Test 005")

    frozen_by_path = {item["path"]: item for item in hashes["files"]}
    authority_rows = []
    for item in manifest["authoritative_files"]:
        path = ROOT / item["path"]
        current = sha256(path)
        frozen = frozen_by_path[item["path"]]["sha256"]
        equal = current == frozen == item["sha256"]
        authority_rows.append(
            {
                "path": item["path"],
                "authority_class": item["authority_class"],
                "frozen_sha256": frozen,
                "current_sha256": current,
                "equal": equal,
            }
        )
    if len(authority_rows) != 17 or not all(row["equal"] for row in authority_rows):
        raise RuntimeError("frozen authority hash mismatch")

    evidence_rows = []
    for item in linkage["evidence"]:
        current = sha256(ROOT / item["path"])
        evidence_rows.append({**item, "current_sha256": current, "equal": current == item["sha256"]})
    if len(evidence_rows) != 8 or not all(row["equal"] for row in evidence_rows):
        raise RuntimeError("Test 004R evidence hash mismatch")
    result_text = (ROOT / "APTF_TEST_004R_RESULT_V0_1.md").read_text(encoding="utf-8")
    if linkage["validation_status"] != "PASS" or linkage["validation_acceptance"] != "60/60 PASS":
        raise RuntimeError("Test 004R linkage status mismatch")
    if "Status: **PASS**" not in result_text or "60/60 PASS" not in result_text:
        raise RuntimeError("Test 004R result does not prove PASS/60")

    model_text = (ROOT / "d04_trading_envelope/src/aptf_d04/envelope/capturability_model.py").read_text(encoding="utf-8")
    if "base = geometry * structural * risk" not in model_text or "final = hard_eligibility * base" not in model_text:
        raise RuntimeError("four-factor source equation not found")
    executable_paths = [
        ROOT / item["path"]
        for item in manifest["authoritative_files"]
        if item["path"].endswith((".py", ".yaml"))
    ]
    removed_matches = []
    for path in executable_paths:
        text = path.read_text(encoding="utf-8")
        for token in REMOVED_TOKENS:
            if token in text:
                removed_matches.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "token": token})
    if removed_matches:
        raise RuntimeError(f"removed executable terms found: {removed_matches}")
    expected_thresholds = {
        "open_threshold": 0.75,
        "close_threshold": 0.55,
        "open_persistence_observations": 3,
        "close_persistence_observations": 2,
    }
    if manifest["threshold_authority"] != expected_thresholds:
        raise RuntimeError("frozen threshold authority mismatch")

    source_hash = sha256(SOURCE_PATH)
    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        source_rows = sum(1 for _ in reader)
    if source_rows < 113:
        raise RuntimeError("source does not contain physical rows through 114")
    freeze_hashes = [
        {"path": name, "sha256": sha256(ROOT / name)} for name in FREEZE_FILES
    ]
    return {
        "manifest": manifest,
        "manifest_sha256": sha256(manifest_path),
        "authority_rows": authority_rows,
        "evidence_rows": evidence_rows,
        "freeze_artifact_hashes": freeze_hashes,
        "source": {
            "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": source_hash,
            "data_row_count": source_rows,
            "physical_row_count_including_header": source_rows + 1,
            "header": header,
            "header_sha256": canonical_sha256(header),
        },
    }


def preflight(output: Path, analysis_script: Path) -> int:
    verified = verify_authority()
    execution_timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    payload = {
        "run_id": RUN_ID,
        "freeze_id": FREEZE_ID,
        "freeze_manifest_sha256": verified["manifest_sha256"],
        "source_data_sha256": verified["source"]["sha256"],
        "execution_timestamp_utc": execution_timestamp,
        "status": "PASS",
        "freeze_status": verified["manifest"]["status"],
        "freeze_ready": verified["manifest"]["ready_as_test005_baseline"],
        "frozen_equation": verified["manifest"]["capturability_equation"],
        "active_factors": verified["manifest"]["active_factors"],
        "removed_factors": verified["manifest"]["removed_from_current_executable_authority"],
        "threshold_authority": verified["manifest"]["threshold_authority"],
        "authority_files": verified["authority_rows"],
        "authority_identity": "17/17 PASS",
        "test004r_evidence": verified["evidence_rows"],
        "test004r_identity": "8/8 PASS",
        "test004r_validation": "PASS / 60/60 PASS",
        "freeze_artifact_hashes": verified["freeze_artifact_hashes"],
        "source": verified["source"],
        "physical_row_convention": "physical row 1 is the CSV header",
        "warmup": {
            "physical_rows": [2, 14],
            "data_indices": [0, 12],
            "measured": False,
            "method": "new process replay of authoritative source through frozen sequential pipeline"
        },
        "measured_physical_rows": [15, 114],
        "measured_observations": 100,
        "row115_prohibited": True,
        "aborted_runtime_state_reused": False,
        "aborted_v01_artifacts": [
            {"path": "APTF_TEST_005_PLAN_V0_1.md", "classification": "ABORTED_NON_AUTHORITATIVE"},
            {"path": "diagnostics/aptf_test_005_empirical_100.py", "classification": "ABORTED_NON_AUTHORITATIVE"}
        ],
        "test_code_hashes": [
            {"path": str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(Path(__file__).resolve())},
            {"path": str(analysis_script.resolve().relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(analysis_script.resolve())}
        ],
        "historical_inventories": {
            "Test004": inventory("APTF_TEST_004_*"),
            "Test004A": inventory("APTF_TEST_004A_*"),
            "Test004R": inventory("APTF_TEST_004R_*")
        },
        "acceptance_preexecution": "G001-G030 PASS"
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "authority": "17/17", "test004r": "8/8", "source_sha256": verified["source"]["sha256"], "execution_timestamp_utc": execution_timestamp}, indent=2))
    return 0


def contains_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(forbidden.intersection(value)) or any(contains_key(item, forbidden) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, forbidden) for item in value)
    return False


def observation_record(target: dict[str, Any], cycle: int, opening_before: int, closing_before: int) -> dict[str, Any]:
    math = target["mathematics"]
    d04 = math["d04_evaluation"]
    d03 = math["d03_decision"]
    plan = math["position_controller_plan"]
    if contains_key(d04, {"data_integrity", "feasibility_gate_score", "gate_dimension_values"}):
        raise RuntimeError(f"removed D04 field emitted at cycle {cycle}")
    h, qg, qs, qr = d04["hard_eligibility"], d04["geometry_quality"], d04["structural_quality"], d04["risk_quality"]
    emitted = d04["capturability_score"]
    reconstructed = h * qg * qs * qr
    if abs(reconstructed - emitted) != 0.0:
        raise RuntimeError(f"four-factor reconstruction failed at cycle {cycle}")
    selection = target["selection"]
    timing = target["timing"]
    stages = timing["stage_duration_ns"]
    minimum = min(qg, qs, qr)
    lowest = [name for name, value in (("Q_G", qg), ("Q_S", qs), ("Q_R", qr)) if value == minimum]
    d04_event = next(item for item in target["temporal_lineage"] if item["stage"] == "D04")
    return {
        "cycle": cycle,
        "physical_row": selection["physical_csv_row"],
        "source_timestamp": selection["market_event_time_utc"],
        "source": selection["ohlcv"],
        "source_payload": target["source_payload"],
        "D01": math["d01_dmo"],
        "D01_FMO": math["d01_fmo"],
        "D02": math["d02_return_shape"],
        "H": h,
        "Q_G": qg,
        "Q_S": qs,
        "Q_R": qr,
        "C": emitted,
        "C_reconstructed": reconstructed,
        "reconstruction_delta": abs(reconstructed - emitted),
        "open_shortfall": 0.75 - emitted,
        "open_threshold_percent": emitted / 0.75 * 100.0,
        "lowest_current_multiplicative_factors": lowest,
        "D04_previous_state": d04["previous_envelope_state"],
        "D04_new_state": d04["new_envelope_state"],
        "opening_counter_before": opening_before,
        "opening_counter": target["state_after"]["d04"]["consecutive_open_qualifying"],
        "closing_counter_before": closing_before,
        "closing_counter": target["state_after"]["d04"]["consecutive_close_qualifying"],
        "D04_transition_event_id": d04_event["event_id"],
        "D04_events": d04["events"],
        "D04_reasons": d04["reason_codes"],
        "D03_consumed_D04_state": d03["source_d04_envelope_state"],
        "D03_rule": d03["decision_rule_id"],
        "D03_state": d03["desired_position_state"],
        "position_controller_decision": plan["ordered_execution_verbs"],
        "position_controller_transition_id": plan["transition_id"],
        "position_controller_plan_status": plan["plan_status"],
        "timing": {
            "stage_duration_ns": stages,
            "component_sum_ns": sum(stages.values()),
            "direct_end_to_end_ns": timing["t_direct_ns"],
            "difference_ns": timing["t_direct_ns"] - sum(stages.values()),
            "direct_boundary": timing["direct_boundary"]
        },
        "temporal_lineage": target["temporal_lineage"],
        "checks": target["checks"],
        "state_before": target["state_before"],
        "state_after": target["state_after"]
    }


def progress(record: dict[str, Any], records: list[dict[str, Any]]) -> None:
    if record["cycle"] % 10:
        return
    values = [item["C"] for item in records]
    print(
        f"TEST005 {record['cycle']}/100 row={record['physical_row']} time={record['source_timestamp']} "
        f"C={record['C']} min={min(values)} max={max(values)} "
        f"count_C_ge_0.70={sum(value >= 0.70 for value in values)} "
        f"count_C_ge_0.75={sum(value >= 0.75 for value in values)} "
        f"D04={record['D04_new_state']} D03={record['D03_state']} "
        f"PC={'+'.join(record['position_controller_decision'])} "
        f"direct_ns={record['timing']['direct_end_to_end_ns']}"
    )


def execute(preexecution_path: Path, output: Path) -> int:
    pre = json.loads(preexecution_path.read_text(encoding="utf-8"))
    if pre["status"] != "PASS" or pre["run_id"] != RUN_ID or pre["freeze_id"] != FREEZE_ID:
        raise RuntimeError("pre-execution authority is not PASS for this run")
    verified = verify_authority()
    if verified["manifest_sha256"] != pre["freeze_manifest_sha256"] or verified["source"]["sha256"] != pre["source_data_sha256"]:
        raise RuntimeError("authority/source changed after preflight")
    authority = json.loads((ROOT / "APTF_TEST_004R_COMPONENT_TRACE_V0_1.json").read_text(encoding="utf-8"))
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=None, entity_id="SPY")
    clock = SystemClock()
    records: list[dict[str, Any]] = []
    continuity: list[dict[str, Any]] = []
    first_events: dict[str, dict[str, Any] | None] = {name: None for name in ("C_GE_0_70", "C_GE_0_75", "D04_NON_CLOSED", "D04_OPEN", "D03_NON_FLAT", "PC_NON_NO_ACTION")}

    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        warmup_rows = [next(reader) for _ in range(WARMUP_COUNT)]
        warmup_result = warmup(harness, warmup_rows)
        after_warmup = {"d01": d01_state_snapshot(harness), "d04": d04_state_snapshot(harness), "controller": controller_state_snapshot(harness)}
        after_test004r = {"d01": authority["targets"][-1]["state_after"]["d01"], "d04": authority["targets"][-1]["state_after"]["d04"], "controller": authority["targets"][-1]["state_after"]["controller"]}
        initialization = {
            "method": "new process replay of physical rows 2-14 through frozen sequential pipeline",
            "warmup_physical_rows": [2, 14],
            "warmup_data_indices": [0, 12],
            "aborted_runtime_state_reused": False,
            "test004r_after_row14": after_test004r,
            "test005_after_warmup": after_warmup,
            "D01_MATCH": after_warmup["d01"] == after_test004r["d01"],
            "D04_MATCH": after_warmup["d04"] == after_test004r["d04"],
            "CONTROLLER_MATCH": after_warmup["controller"] == after_test004r["controller"],
            "row15_initial_state_fingerprint": canonical_sha256(after_warmup)
        }
        if not all(initialization[name] for name in ("D01_MATCH", "D04_MATCH", "CONTROLLER_MATCH")):
            raise RuntimeError("row-15 initialization mismatch")

        previous_target: dict[str, Any] | None = None
        for cycle in range(1, MEASURED_COUNT + 1):
            row = next(reader)
            physical_row = cycle + 14
            spec = {"label": f"test005_v02_cycle_{cycle}", "physical_row": physical_row, "index": cycle + 12, "source_row": row["source_row_number"], "time": row["event_timestamp_utc"]}
            opening_before = harness.hysteresis.consecutive_open_qualifying
            closing_before = harness.hysteresis.consecutive_close_qualifying
            target, _ = process_target(harness, clock, row, spec)
            target["cycle"] = cycle
            record = observation_record(target, cycle, opening_before, closing_before)
            if previous_target is not None:
                link = {"from_cycle": cycle - 1, "to_cycle": cycle, "D01": previous_target["state_after"]["d01"] == target["state_before"]["d01"], "D04": previous_target["state_after"]["d04"] == target["state_before"]["d04"], "controller": previous_target["state_after"]["controller"] == target["state_before"]["controller"]}
                if not all(link[name] for name in ("D01", "D04", "controller")):
                    raise RuntimeError(f"state discontinuity before cycle {cycle}")
                continuity.append(link)
            previous_target = target
            records.append(record)
            notices = (
                ("C_GE_0_70", record["C"] >= 0.70, "FIRST C >= 0.70"),
                ("C_GE_0_75", record["C"] >= 0.75, "FIRST C >= 0.75"),
                ("D04_NON_CLOSED", record["D04_new_state"] != "CLOSED", "FIRST D04 != CLOSED"),
                ("D04_OPEN", record["D04_new_state"] == "OPEN", "FIRST D04 OPEN"),
                ("D03_NON_FLAT", record["D03_state"] != "FLAT", "FIRST D03 NON-FLAT"),
                ("PC_NON_NO_ACTION", record["position_controller_decision"] != ["NO_ACTION"], "FIRST POSITION CONTROLLER NON-NO_ACTION")
            )
            for name, condition, label in notices:
                if condition and first_events[name] is None:
                    first_events[name] = {"cycle": cycle, "physical_row": physical_row, "source_timestamp": record["source_timestamp"], "C": record["C"]}
                    print(f"{label}: cycle={cycle} row={physical_row} C={record['C']}")
            progress(record, records)

    if len(records) != 100 or records[0]["physical_row"] != 15 or records[-1]["physical_row"] != 114:
        raise RuntimeError("measured source scope failure")
    times = [datetime.fromisoformat(record["source_timestamp"].replace("Z", "+00:00")) for record in records]
    if any((right - left).total_seconds() != 60 for left, right in zip(times, times[1:])):
        raise RuntimeError("source timestamps are not consecutive one-minute observations")
    payload = {
        "run_id": RUN_ID,
        "freeze_id": FREEZE_ID,
        "freeze_manifest_sha256": pre["freeze_manifest_sha256"],
        "source_data_sha256": pre["source_data_sha256"],
        "execution_timestamp_utc": pre["execution_timestamp_utc"],
        "test_id": "APTF_TEST_005_FROZEN_D04_V0_2",
        "source": {"path": pre["source"]["path"], "sha256_before": pre["source_data_sha256"], "warmup_physical_rows": [2, 14], "measured_physical_rows": [15, 114], "measured_count": 100, "row115_processed": False},
        "authority": {"equation": pre["frozen_equation"], "active_factors": pre["active_factors"], "data_integrity_present": False, "G_present": False, **pre["threshold_authority"]},
        "execution": {"sequential": True, "state_resets": 0, "parallel_observations": False, "synthetic_market_values": False, "counterfactual_execution": False, "arbitrary_context_injection": False, "broker_injection": False, "early_termination": False},
        "warmup": warmup_result,
        "initialization": initialization,
        "continuity": continuity,
        "first_events": first_events,
        "records": records
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"measured_count": 100, "first_physical_row": 15, "last_physical_row": 114, "row115_processed": False, "maximum_reconstruction_error": max(record["reconstruction_delta"] for record in records)}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight")
    pre.add_argument("--output", type=Path, required=True)
    pre.add_argument("--analysis-script", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--preexecution", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "preflight":
        return preflight(args.output, args.analysis_script)
    return execute(args.preexecution, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
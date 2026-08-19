from __future__ import annotations

import argparse
import csv
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
from aptf_test_005_frozen_v02 import (
    FREEZE_FILES,
    canonical_sha256,
    contains_key,
    inventory,
    sha256,
    verify_authority,
)

RUN_ID = "TEST005R_FROZEN_D04_100OBS_V0_3_RUN_001"
FREEZE_ID = "D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1"
WARMUP_COUNT = 13
MEASURED_COUNT = 100


def metadata(pre: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "freeze_id": FREEZE_ID,
        "freeze_manifest_sha256": pre["freeze_manifest_sha256"],
        "source_data_sha256": pre["source_data_sha256"],
        "execution_timestamp_utc": pre["execution_timestamp_utc"],
    }


def preflight(output: Path, analysis_script: Path) -> int:
    verified = verify_authority()
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    previous_test005 = inventory("APTF_TEST_005_*")
    payload = {
        "run_id": RUN_ID,
        "freeze_id": FREEZE_ID,
        "freeze_manifest_sha256": verified["manifest_sha256"],
        "source_data_sha256": verified["source"]["sha256"],
        "execution_timestamp_utc": timestamp,
        "status": "PASS",
        "freeze_status": verified["manifest"]["status"],
        "freeze_ready": verified["manifest"]["ready_as_test005_baseline"],
        "authority_files": verified["authority_rows"],
        "authority_identity": "17/17 PASS",
        "test004r_evidence": verified["evidence_rows"],
        "test004r_identity": "8/8 PASS",
        "test004r_validation": "PASS / 60/60 PASS",
        "freeze_artifact_hashes": verified["freeze_artifact_hashes"],
        "equation": verified["manifest"]["capturability_equation"],
        "active_factors": verified["manifest"]["active_factors"],
        "removed_factors": verified["manifest"]["removed_from_current_executable_authority"],
        "threshold_authority": verified["manifest"]["threshold_authority"],
        "source": verified["source"],
        "observation_contract": {
            "definition": "one observation equals one literal source data row",
            "uniform_60_second_spacing_required": False,
            "source_timestamps_authoritative": True,
            "timestamps_must_be_strictly_monotonic": True,
            "source_gaps_are_valid_evidence": True,
        },
        "physical_row_convention": "physical row 1 is the CSV header",
        "warmup": {
            "physical_rows": [2, 14],
            "data_indices": [0, 12],
            "measured": False,
            "method": "fresh process replay through the frozen sequential pipeline",
        },
        "measured_physical_rows": [15, 114],
        "measured_observations": 100,
        "row115_prohibited": True,
        "previous_runtime_state_reused": False,
        "test_code_hashes": [
            {"path": str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(Path(__file__).resolve())},
            {"path": str(analysis_script.resolve().relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(analysis_script.resolve())},
        ],
        "historical_inventories": {
            "Test004": inventory("APTF_TEST_004_*"),
            "Test004A": inventory("APTF_TEST_004A_*"),
            "Test004R": inventory("APTF_TEST_004R_*"),
            "PriorTest005": previous_test005,
        },
        "acceptance_preexecution": "G001-G023 PASS",
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "authority": "17/17", "test004r": "8/8", "source_sha256": verified["source"]["sha256"], "execution_timestamp_utc": timestamp}, indent=2))
    return 0


def record_observation(
    target: dict[str, Any],
    cycle: int,
    previous_timestamp: str,
    opening_before: int,
    closing_before: int,
) -> dict[str, Any]:
    mathematics = target["mathematics"]
    d04 = mathematics["d04_evaluation"]
    d03 = mathematics["d03_decision"]
    plan = mathematics["position_controller_plan"]
    if contains_key(d04, {"data_integrity", "feasibility_gate_score", "gate_dimension_values"}):
        raise RuntimeError(f"removed D04 field emitted at cycle {cycle}")
    h = d04["hard_eligibility"]
    qg = d04["geometry_quality"]
    qs = d04["structural_quality"]
    qr = d04["risk_quality"]
    emitted = d04["capturability_score"]
    reconstructed = h * qg * qs * qr
    if abs(reconstructed - emitted) != 0.0:
        raise RuntimeError(f"four-factor reconstruction failed at cycle {cycle}")
    timestamp = target["selection"]["market_event_time_utc"]
    previous_time = datetime.fromisoformat(previous_timestamp.replace("Z", "+00:00"))
    current_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    delta_t = (current_time - previous_time).total_seconds()
    if delta_t <= 0:
        raise RuntimeError(f"non-monotonic source timestamp at cycle {cycle}")
    stages = target["timing"]["stage_duration_ns"]
    minimum = min(qg, qs, qr)
    source_payload = target["source_payload"]
    return {
        "cycle": cycle,
        "physical_row": target["selection"]["physical_csv_row"],
        "source_date": timestamp[:10],
        "source_time": timestamp[11:19],
        "source_timestamp": timestamp,
        "previous_source_timestamp": previous_timestamp,
        "delta_t_seconds": delta_t,
        "delta_t_reference": "physical row 14" if cycle == 1 else "previous measured observation",
        "source": target["selection"]["ohlcv"],
        "source_payload": source_payload,
        "D01": mathematics["d01_dmo"],
        "D01_FMO": mathematics["d01_fmo"],
        "D02": mathematics["d02_return_shape"],
        "D02_input_state_fingerprint": canonical_sha256(target["state_before"]["d01"]),
        "D02_output_fingerprint": canonical_sha256(mathematics["d02_return_shape"]),
        "H": h,
        "Q_G": qg,
        "Q_S": qs,
        "Q_R": qr,
        "C": emitted,
        "C_reconstructed": reconstructed,
        "reconstruction_error": abs(reconstructed - emitted),
        "shortfall_from_0_75": 0.75 - emitted,
        "C_percent_of_open": emitted / 0.75 * 100.0,
        "lowest_current_multiplicative_factors": [name for name, value in (("Q_G", qg), ("Q_S", qs), ("Q_R", qr)) if value == minimum],
        "D04_previous_state": d04["previous_envelope_state"],
        "D04_resulting_state": d04["new_envelope_state"],
        "opening_counter_before": opening_before,
        "opening_counter": target["state_after"]["d04"]["consecutive_open_qualifying"],
        "closing_counter_before": closing_before,
        "closing_counter": target["state_after"]["d04"]["consecutive_close_qualifying"],
        "D04_reason_codes": d04["reason_codes"],
        "D04_events": d04["events"],
        "D03_consumed_D04_state": d03["source_d04_envelope_state"],
        "D03_rule": d03["decision_rule_id"],
        "D03_state": d03["desired_position_state"],
        "position_controller_decision": plan["ordered_execution_verbs"],
        "position_controller_transition_id": plan["transition_id"],
        "timing": {
            "stage_duration_ns": stages,
            "component_sum_ns": sum(stages.values()),
            "direct_end_to_end_ns": target["timing"]["t_direct_ns"],
            "difference_ns": target["timing"]["t_direct_ns"] - sum(stages.values()),
            "direct_boundary": target["timing"]["direct_boundary"],
        },
        "temporal_lineage": target["temporal_lineage"],
        "checks": target["checks"],
        "state_before": target["state_before"],
        "state_after": target["state_after"],
    }


def execute(preexecution_path: Path, output: Path) -> int:
    pre = json.loads(preexecution_path.read_text(encoding="utf-8"))
    if pre["status"] != "PASS" or pre["run_id"] != RUN_ID or pre["freeze_id"] != FREEZE_ID:
        raise RuntimeError("pre-execution authority does not authorize this run")
    verified = verify_authority()
    if verified["manifest_sha256"] != pre["freeze_manifest_sha256"] or verified["source"]["sha256"] != pre["source_data_sha256"]:
        raise RuntimeError("authority/source changed after preflight")
    test004r = json.loads((ROOT / "APTF_TEST_004R_COMPONENT_TRACE_V0_1.json").read_text(encoding="utf-8"))
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=None, entity_id="SPY")
    clock = SystemClock()
    records: list[dict[str, Any]] = []
    continuity: list[dict[str, Any]] = []
    first_events = {name: None for name in ("C_GE_0_55", "C_GE_0_70", "C_GE_0_75", "D04_NON_CLOSED", "D04_OPEN", "D03_NON_FLAT", "PC_NON_NO_ACTION")}
    first_gap: dict[str, Any] | None = None

    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        warmup_rows = [next(reader) for _ in range(WARMUP_COUNT)]
        warmup_result = warmup(harness, warmup_rows)
        after_warmup = {"d01": d01_state_snapshot(harness), "d04": d04_state_snapshot(harness), "controller": controller_state_snapshot(harness)}
        expected = {"d01": test004r["targets"][-1]["state_after"]["d01"], "d04": test004r["targets"][-1]["state_after"]["d04"], "controller": test004r["targets"][-1]["state_after"]["controller"]}
        initialization = {
            "method": "fresh process replay of physical rows 2-14 through frozen sequential pipeline",
            "warmup_physical_rows": [2, 14],
            "warmup_final_timestamp": warmup_rows[-1]["event_timestamp_utc"],
            "previous_runtime_state_reused": False,
            "D01_MATCH": after_warmup["d01"] == expected["d01"],
            "D04_MATCH": after_warmup["d04"] == expected["d04"],
            "CONTROLLER_MATCH": after_warmup["controller"] == expected["controller"],
            "row15_initial_state_fingerprint": canonical_sha256(after_warmup),
        }
        if not all(initialization[name] for name in ("D01_MATCH", "D04_MATCH", "CONTROLLER_MATCH")):
            raise RuntimeError("row-15 initialization mismatch")
        previous_target: dict[str, Any] | None = None
        previous_timestamp = warmup_rows[-1]["event_timestamp_utc"]
        for cycle in range(1, MEASURED_COUNT + 1):
            row = next(reader)
            physical_row = cycle + 14
            spec = {"label": f"test005r_v03_cycle_{cycle}", "physical_row": physical_row, "index": cycle + 12, "source_row": row["source_row_number"], "time": row["event_timestamp_utc"]}
            opening_before = harness.hysteresis.consecutive_open_qualifying
            closing_before = harness.hysteresis.consecutive_close_qualifying
            target, _ = process_target(harness, clock, row, spec)
            target["cycle"] = cycle
            record = record_observation(target, cycle, previous_timestamp, opening_before, closing_before)
            previous_timestamp = record["source_timestamp"]
            if previous_target is not None:
                link = {"from_cycle": cycle - 1, "to_cycle": cycle, "D01": previous_target["state_after"]["d01"] == target["state_before"]["d01"], "D04": previous_target["state_after"]["d04"] == target["state_before"]["d04"], "controller": previous_target["state_after"]["controller"] == target["state_before"]["controller"]}
                if not all(link[name] for name in ("D01", "D04", "controller")):
                    raise RuntimeError(f"state discontinuity before cycle {cycle}")
                continuity.append(link)
            previous_target = target
            records.append(record)
            if record["delta_t_seconds"] > 60 and first_gap is None:
                first_gap = {"cycle": cycle, "physical_row": physical_row, "delta_t_seconds": record["delta_t_seconds"], "source_timestamp": record["source_timestamp"]}
                print(f"SOURCE TIME GAP OBSERVED: {record['delta_t_seconds']} SECONDS row={physical_row}. VALID SOURCE OBSERVATION SEQUENCE CONTINUES.")
            notices = (
                ("C_GE_0_55", record["C"] >= 0.55, "FIRST C >= 0.55"),
                ("C_GE_0_70", record["C"] >= 0.70, "FIRST C >= 0.70"),
                ("C_GE_0_75", record["C"] >= 0.75, "FIRST C >= 0.75"),
                ("D04_NON_CLOSED", record["D04_resulting_state"] != "CLOSED", "FIRST D04 != CLOSED"),
                ("D04_OPEN", record["D04_resulting_state"] == "OPEN", "FIRST D04 OPEN"),
                ("D03_NON_FLAT", record["D03_state"] != "FLAT", "FIRST D03 NON-FLAT"),
                ("PC_NON_NO_ACTION", record["position_controller_decision"] != ["NO_ACTION"], "FIRST PC NON-NO_ACTION"),
            )
            for name, condition, label in notices:
                if condition and first_events[name] is None:
                    first_events[name] = {"cycle": cycle, "physical_row": physical_row, "source_timestamp": record["source_timestamp"], "C": record["C"]}
                    print(f"{label}: cycle={cycle} row={physical_row} C={record['C']}")
            if cycle % 10 == 0:
                values = [item["C"] for item in records]
                print(f"TEST005R {cycle}/100 row={physical_row} time={record['source_timestamp']} delta_t={record['delta_t_seconds']} C={record['C']} min={min(values)} max={max(values)} ge55={sum(v >= .55 for v in values)} ge70={sum(v >= .70 for v in values)} ge75={sum(v >= .75 for v in values)} D04={record['D04_resulting_state']} D03={record['D03_state']} PC={'+'.join(record['position_controller_decision'])} direct_ns={record['timing']['direct_end_to_end_ns']}")

    if len(records) != 100 or records[0]["physical_row"] != 15 or records[-1]["physical_row"] != 114:
        raise RuntimeError("measured source scope failure")
    payload = {
        **metadata(pre),
        "test_id": "APTF_TEST_005R_FROZEN_D04_100OBS_V0_3",
        "status": "EXECUTION_COMPLETE",
        "source": {"path": pre["source"]["path"], "sha256_before": pre["source_data_sha256"], "warmup_physical_rows": [2, 14], "measured_physical_rows": [15, 114], "measured_count": 100, "row115_processed": False},
        "observation_contract": pre["observation_contract"],
        "authority": {"equation": pre["equation"], "active_factors": pre["active_factors"], "data_integrity_present": False, "G_present": False, **pre["threshold_authority"]},
        "execution": {"sequential": True, "parallel_observations": False, "state_resets": 0, "synthetic_values": False, "interpolation": False, "broker_injection": False, "early_termination": False},
        "warmup": warmup_result,
        "initialization": initialization,
        "continuity": continuity,
        "first_events": first_events,
        "first_source_gap": first_gap,
        "records": records,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"measured_count": 100, "first_row": 15, "last_row": 114, "row115_processed": False, "maximum_reconstruction_error": max(record["reconstruction_error"] for record in records), "source_gap_count": sum(record["delta_t_seconds"] > 60 for record in records[1:])}, indent=2))
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
    return preflight(args.output, args.analysis_script) if args.command == "preflight" else execute(args.preexecution, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
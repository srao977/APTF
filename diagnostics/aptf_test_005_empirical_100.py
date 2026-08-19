from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
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

TEST004R = ROOT / "APTF_TEST_004R_COMPONENT_TRACE_V0_1.json"
WARMUP_COUNT = 13
MEASURED_COUNT = 100
REMOVED_FIELDS = {"data_integrity", "feasibility_gate_score", "gate_dimension_values"}


def contains_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(forbidden.intersection(value)) or any(
            contains_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(contains_key(item, forbidden) for item in value)
    return False


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def observation_record(
    target: dict[str, Any],
    cycle: int,
    opening_before: int,
    closing_before: int,
) -> dict[str, Any]:
    math = target["mathematics"]
    d01 = math["d01_dmo"]
    d02 = math["d02_return_shape"]
    d04 = math["d04_evaluation"]
    d03 = math["d03_decision"]
    plan = math["position_controller_plan"]
    if contains_key(d04, REMOVED_FIELDS):
        raise RuntimeError(f"removed D04 field emitted at measured cycle {cycle}")
    h = d04["hard_eligibility"]
    qg = d04["geometry_quality"]
    qs = d04["structural_quality"]
    qr = d04["risk_quality"]
    emitted = d04["capturability_score"]
    reconstructed = h * qg * qs * qr
    reconstruction_delta = abs(reconstructed - emitted)
    if reconstruction_delta != 0.0:
        raise RuntimeError(f"four-factor reconstruction failed at measured cycle {cycle}")
    selection = target["selection"]
    timing = target["timing"]
    stages = timing["stage_duration_ns"]
    component_sum = sum(stages.values())
    opening_after = target["state_after"]["d04"]["consecutive_open_qualifying"]
    closing_after = target["state_after"]["d04"]["consecutive_close_qualifying"]
    verbs = plan["ordered_execution_verbs"]
    return {
        "cycle": cycle,
        "physical_row": selection["physical_csv_row"],
        "source_timestamp": selection["market_event_time_utc"],
        "source": selection["ohlcv"],
        "source_payload": target["source_payload"],
        "D01": math["d01_dmo"],
        "D01_FMO": math["d01_fmo"],
        "D02": d02,
        "H": h,
        "Q_G": qg,
        "Q_S": qs,
        "Q_R": qr,
        "C": emitted,
        "C_reconstructed": reconstructed,
        "reconstruction_delta": reconstruction_delta,
        "shortfall_from_0_75": 0.75 - emitted,
        "C_as_percent_of_open_threshold": emitted / 0.75 * 100.0,
        "lowest_current_multiplicative_factor": min(
            (("Q_G", qg), ("Q_S", qs), ("Q_R", qr)), key=lambda item: item[1]
        )[0],
        "D04_previous_state": d04["previous_envelope_state"],
        "D04_new_state": d04["new_envelope_state"],
        "opening_counter_before": opening_before,
        "opening_counter": opening_after,
        "closing_counter_before": closing_before,
        "closing_counter": closing_after,
        "threshold_relation": "AT_OR_ABOVE_OPEN" if emitted >= 0.75 else "BELOW_OPEN",
        "D04_events": d04["events"],
        "D04_reasons": d04["reason_codes"],
        "D03_consumed_D04_state": d03["source_d04_envelope_state"],
        "D03_rule": d03["decision_rule_id"],
        "D03_state": d03["desired_position_state"],
        "position_controller_decision": verbs,
        "position_controller_plan_status": plan["plan_status"],
        "timing": {
            "stage_duration_ns": stages,
            "component_sum_ns": component_sum,
            "direct_end_to_end_ns": timing["t_direct_ns"],
            "timing_difference_ns": timing["t_direct_ns"] - component_sum,
            "direct_boundary": timing["direct_boundary"],
        },
        "temporal_lineage": target["temporal_lineage"],
        "checks": target["checks"],
        "state_before": target["state_before"],
        "state_after": target["state_after"],
    }


def progress(record: dict[str, Any], records: list[dict[str, Any]]) -> None:
    cycle = record["cycle"]
    if cycle % 10 != 0:
        return
    values = [item["C"] for item in records]
    decision = "+".join(record["position_controller_decision"])
    print(
        f"TEST005 {cycle}/100 row={record['physical_row']} C={record['C']} "
        f"min={min(values)} max={max(values)} count_C_ge_0.75="
        f"{sum(value >= 0.75 for value in values)} D04={record['D04_new_state']} "
        f"D03={record['D03_state']} PC={decision}"
    )


def run() -> dict[str, Any]:
    authority = json.loads(TEST004R.read_text(encoding="utf-8"))
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=None, entity_id="SPY")
    clock = SystemClock()
    records: list[dict[str, Any]] = []
    continuity: list[dict[str, Any]] = []
    first_events: dict[str, dict[str, Any] | None] = {
        "C_GE_0_70": None,
        "C_GE_0_75": None,
        "D04_OPENING": None,
        "D04_OPEN": None,
        "D03_NON_FLAT": None,
        "PC_NON_NO_ACTION": None,
    }

    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        warmup_rows = [next(reader) for _ in range(WARMUP_COUNT)]
        warmup_result = warmup(harness, warmup_rows)
        after_warmup = {
            "d01": d01_state_snapshot(harness),
            "d04": d04_state_snapshot(harness),
            "controller": controller_state_snapshot(harness),
        }
        after_test004r = {
            "d01": authority["targets"][-1]["state_after"]["d01"],
            "d04": authority["targets"][-1]["state_after"]["d04"],
            "controller": authority["targets"][-1]["state_after"]["controller"],
        }
        initialization = {
            "method": "replay physical rows 2-14 through the same continuous pipeline",
            "warmup_physical_rows": [2, 14],
            "warmup_data_indices": [0, 12],
            "test004r_after_row14": after_test004r,
            "test005_after_warmup": after_warmup,
            "D01_MATCH": after_warmup["d01"] == after_test004r["d01"],
            "D04_MATCH": after_warmup["d04"] == after_test004r["d04"],
            "CONTROLLER_MATCH": after_warmup["controller"] == after_test004r["controller"],
        }
        if not all(
            initialization[name]
            for name in ("D01_MATCH", "D04_MATCH", "CONTROLLER_MATCH")
        ):
            raise RuntimeError("Test 005 row-15 initialization does not match Test 004R")

        previous_target: dict[str, Any] | None = None
        for cycle in range(1, MEASURED_COUNT + 1):
            row = next(reader)
            physical_row = cycle + 14
            spec = {
                "label": f"test005_cycle_{cycle}",
                "physical_row": physical_row,
                "index": cycle + 12,
                "source_row": row["source_row_number"],
                "time": row["event_timestamp_utc"],
            }
            opening_before = harness.hysteresis.consecutive_open_qualifying
            closing_before = harness.hysteresis.consecutive_close_qualifying
            target, _ = process_target(harness, clock, row, spec)
            target["cycle"] = cycle
            record = observation_record(
                target, cycle, opening_before, closing_before
            )
            if previous_target is not None:
                link = {
                    "from_cycle": cycle - 1,
                    "to_cycle": cycle,
                    "D01": previous_target["state_after"]["d01"]
                    == target["state_before"]["d01"],
                    "D04": previous_target["state_after"]["d04"]
                    == target["state_before"]["d04"],
                    "controller": previous_target["state_after"]["controller"]
                    == target["state_before"]["controller"],
                }
                if not all(link[name] for name in ("D01", "D04", "controller")):
                    raise RuntimeError(f"state discontinuity before measured cycle {cycle}")
                continuity.append(link)
            previous_target = target
            records.append(record)

            notices = (
                ("C_GE_0_70", record["C"] >= 0.70, "FIRST C >= 0.70"),
                ("C_GE_0_75", record["C"] >= 0.75, "FIRST C >= 0.75"),
                ("D04_OPENING", record["D04_new_state"].startswith("OPENING"), "FIRST D04 OPENING STATE"),
                ("D04_OPEN", record["D04_new_state"] == "OPEN", "FIRST D04 OPEN"),
                ("D03_NON_FLAT", record["D03_state"] != "FLAT", "FIRST D03 NON-FLAT"),
                ("PC_NON_NO_ACTION", record["position_controller_decision"] != ["NO_ACTION"], "FIRST POSITION CONTROLLER NON-NO_ACTION"),
            )
            for name, condition, label in notices:
                if condition and first_events[name] is None:
                    first_events[name] = {
                        "cycle": cycle,
                        "physical_row": physical_row,
                        "source_timestamp": record["source_timestamp"],
                        "C": record["C"],
                    }
                    print(f"{label}: cycle={cycle} row={physical_row} C={record['C']}")
            progress(record, records)

    return {
        "test_id": "APTF_TEST_005_EMPIRICAL_100_V0_1",
        "source": {
            "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256_before": source_sha256(),
            "warmup_physical_rows": [2, 14],
            "measured_physical_rows": [15, 114],
            "measured_count": len(records),
            "row115_processed": False,
        },
        "authority": {
            "equation": "C = H * Q_G * Q_S * Q_R",
            "data_integrity_present": False,
            "G_present": False,
            "open_threshold": harness.hysteresis.config.open_threshold,
            "close_threshold": harness.hysteresis.config.close_threshold,
            "open_persistence": harness.hysteresis.config.open_persistence_observations,
            "close_persistence": harness.hysteresis.config.close_persistence_observations,
        },
        "execution": {
            "sequential": True,
            "state_resets": 0,
            "synthetic_market_values": False,
            "counterfactual_execution": False,
            "broker_injection": False,
            "early_termination": False,
        },
        "warmup": warmup_result,
        "initialization": initialization,
        "continuity": continuity,
        "first_events": first_events,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "measured_count": len(result["records"]),
                "first_physical_row": result["records"][0]["physical_row"],
                "last_physical_row": result["records"][-1]["physical_row"],
                "row115_processed": result["source"]["row115_processed"],
                "maximum_reconstruction_error": max(
                    record["reconstruction_delta"] for record in result["records"]
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
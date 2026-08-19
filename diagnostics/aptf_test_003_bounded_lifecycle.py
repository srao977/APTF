from __future__ import annotations

import argparse
import csv
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
    process_target,
    warmup,
)

TEST_002_TRACE = ROOT / "APTF_TEST_002_COMPONENT_TRACE_V0_1.json"
OPEN_THRESHOLD = 0.75
MAX_CYCLES = 5
MEANINGFUL = {"BUY", "HOLD", "SELL", "SELL_SHORT", "BUY_TO_COVER"}
EXECUTION_CHANGING = {"BUY", "SELL", "SELL_SHORT", "BUY_TO_COVER"}


def target_spec(cycle: int, row: dict[str, str]) -> dict[str, Any]:
    index = 7 + cycle
    return {
        "label": f"cycle_{cycle}",
        "physical_row": index + 2,
        "index": index,
        "source_row": row["source_row_number"],
        "time": row["event_timestamp_utc"],
    }


def deterministic_math(target: dict[str, Any]) -> dict[str, Any]:
    return target["mathematics"]


def compare_test_002(target: dict[str, Any], golden: dict[str, Any]) -> dict[str, Any]:
    current = deterministic_math(target)
    expected = deterministic_math(golden)
    comparisons = {
        "D01_DMO": current["d01_dmo"] == expected["d01_dmo"],
        "D01_FMO": current["d01_fmo"] == expected["d01_fmo"],
        "D02": current["d02_return_shape"] == expected["d02_return_shape"],
        "D04": current["d04_evaluation"] == expected["d04_evaluation"],
        "D03_POSITION": current["d03_decision"]["desired_position_state"]
        == expected["d03_decision"]["desired_position_state"],
        "POSITION_CONTROLLER_DECISION": current["position_controller_plan"]["ordered_execution_verbs"]
        == expected["position_controller_plan"]["ordered_execution_verbs"],
    }
    return {"comparisons": comparisons, "pass": all(comparisons.values())}


def print_cycle(cycle: int, target: dict[str, Any], stop_met: bool) -> None:
    selection = target["selection"]
    math = target["mathematics"]
    d01 = math["d01_dmo"]
    d02 = math["d02_return_shape"]
    d04 = math["d04_evaluation"]
    d03 = math["d03_decision"]
    plan = math["position_controller_plan"]
    timing = target["timing"]
    stages = timing["stage_duration_ns"]
    print("=" * 50)
    print(f"LIFECYCLE CYCLE: {cycle}")
    print(f"PHYSICAL ROW: {selection['physical_csv_row']}")
    print(f"MARKET EVENT TIME: {selection['market_event_time_utc']}")
    print(f"OHLCV: {selection['ohlcv']}")
    print(f"D01 LEVEL/VELOCITY/ACCELERATION: {d01['state_level']} / {d01['state_velocity']} / {d01['state_acceleration']}")
    print(f"D01 KEY STATE: strength={d01['strength']} coherence={d01['coherence']} persistence={d01['persistence']} uncertainty={d01['uncertainty']} reversal={d01['reversal_propensity']}")
    print(f"D02 TERMINAL/MAX/DIRECTION: {d02['terminal_displacement']} / {d02['maximum_absolute_displacement']} / {d02['path_direction']}")
    print(f"D04 APERTURE: {d04['aperture_after']}")
    print(f"D04 CAPTURABILITY: {d04['capturability_score']}")
    print(f"D04 GATE MARGIN: {d04['capturability_score'] - OPEN_THRESHOLD}")
    print(f"D04 STATE/CANDIDATE: {d04['new_envelope_state']} / {d04['candidate_envelope']}")
    print(f"D04 REASONS: {d04['reason_codes']}")
    print(f"D03 RULE/POSITION: {d03['decision_rule_id']} / {d03['desired_position_state']}")
    print(f"INTERNAL CONTROLLER STATE BEFORE: {target['state_before']['controller']}")
    print(f"POSITION CONTROLLER DECISION: {plan['ordered_execution_verbs']}")
    print(f"INTERNAL CONTROLLER STATE AFTER: {target['state_after']['controller']}")
    print(f"TIMING E0/D01/D02/D04/D03/PC: {stages['E0']} / {stages['D01']} / {stages['D02']} / {stages['D04']} / {stages['D03']} / {stages['POSITION_CONTROLLER']}")
    print(f"T_DIRECT_NS/US/MS: {timing['t_direct_ns']} / {timing['t_direct_us']} / {timing['t_direct_ms']}")
    print(f"DELTA_ALL_STAGES_NS: {timing['delta_all_stages_ns']}")
    print(f"STOP CONDITION: {'MET' if stop_met else 'NOT MET'}")


def run() -> dict[str, Any]:
    golden = json.loads(TEST_002_TRACE.read_text(encoding="utf-8"))
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=None, entity_id="SPY")
    clock = SystemClock()
    processed: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    non_drift: dict[str, Any] = {}
    source_access: list[dict[str, Any]] = []
    stop_reason = "FIVE_CYCLE_HORIZON_EXHAUSTED"
    first_semantic: dict[str, Any] | None = None
    first_execution_changing: dict[str, Any] | None = None
    milestones: dict[str, dict[str, Any] | None] = {
        "M1_FIRST_D02_DIRECTION_CHANGE": None,
        "M2_FIRST_D04_STATE_CHANGE": None,
        "M3_FIRST_D04_THRESHOLD_CROSSING": None,
        "M4_FIRST_NON_NULL_D04_CANDIDATE": None,
        "M5_FIRST_D03_POSITION_CHANGE": None,
        "M6_FIRST_PC_DECISION_NOT_NO_ACTION": None,
        "FIRST_EXECUTION_CHANGING_PC_DECISION": None,
    }

    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        warmup_rows = [next(reader) for _ in range(8)]
        warmup_result = warmup(harness, warmup_rows)
        prior_stop_ns: int | None = None
        prior_direction: str | None = None

        for cycle in range(1, MAX_CYCLES + 1):
            row = next(reader)
            spec = target_spec(cycle, row)
            source_access.append(
                {
                    "cycle": cycle,
                    "physical_row": spec["physical_row"],
                    "zero_based_data_index": spec["index"],
                    "market_event_time_utc": spec["time"],
                    "read_condition": "cycle 1 start" if cycle == 1 else "preceding complete E5 decision was NO_ACTION",
                }
            )
            target, stop_ns = process_target(harness, clock, row, spec)
            target["cycle"] = cycle
            target["d04_open_threshold"] = OPEN_THRESHOLD
            target["d04_gate_margin"] = (
                target["mathematics"]["d04_evaluation"]["capturability_score"] - OPEN_THRESHOLD
            )
            if prior_stop_ns is not None:
                gap = target["timing"]["direct_boundary"]["start_monotonic_ns"] - prior_stop_ns
                gaps.append(
                    {
                        "from_cycle": cycle - 1,
                        "to_cycle": cycle,
                        "inter_lifecycle_runtime_gap_ns": gap,
                        "inter_lifecycle_runtime_gap_us": gap / 1_000.0,
                        "inter_lifecycle_runtime_gap_ms": gap / 1_000_000.0,
                    }
                )
            prior_stop_ns = stop_ns

            if cycle <= 2:
                check = compare_test_002(target, golden["targets"][cycle - 1])
                non_drift[f"row_{spec['physical_row']}"] = check
                if not check["pass"]:
                    raise RuntimeError("TEST 002 NON-DRIFT FAILURE; stopping before physical row 12")

            math = target["mathematics"]
            d02_direction = math["d02_return_shape"]["path_direction"]
            d04 = math["d04_evaluation"]
            d03_position = math["d03_decision"]["desired_position_state"]
            verbs = math["position_controller_plan"]["ordered_execution_verbs"]
            meaningful_verbs = [verb for verb in verbs if verb in MEANINGFUL]
            changing_verbs = [verb for verb in verbs if verb in EXECUTION_CHANGING]

            def milestone(value: Any) -> dict[str, Any]:
                return {
                    "cycle": cycle,
                    "physical_row": spec["physical_row"],
                    "market_event_time_utc": spec["time"],
                    "value": value,
                }

            if prior_direction is not None and d02_direction != prior_direction and milestones["M1_FIRST_D02_DIRECTION_CHANGE"] is None:
                milestones["M1_FIRST_D02_DIRECTION_CHANGE"] = milestone(d02_direction)
            prior_direction = d02_direction
            if d04["new_envelope_state"] != d04["previous_envelope_state"] and milestones["M2_FIRST_D04_STATE_CHANGE"] is None:
                milestones["M2_FIRST_D04_STATE_CHANGE"] = milestone(
                    f"{d04['previous_envelope_state']}->{d04['new_envelope_state']}"
                )
            if d04["capturability_score"] >= OPEN_THRESHOLD and milestones["M3_FIRST_D04_THRESHOLD_CROSSING"] is None:
                milestones["M3_FIRST_D04_THRESHOLD_CROSSING"] = milestone(d04["capturability_score"])
            if d04["candidate_envelope"] is not None and milestones["M4_FIRST_NON_NULL_D04_CANDIDATE"] is None:
                milestones["M4_FIRST_NON_NULL_D04_CANDIDATE"] = milestone(d04["candidate_envelope"])
            if d03_position != "FLAT" and milestones["M5_FIRST_D03_POSITION_CHANGE"] is None:
                milestones["M5_FIRST_D03_POSITION_CHANGE"] = milestone(d03_position)
            if meaningful_verbs and milestones["M6_FIRST_PC_DECISION_NOT_NO_ACTION"] is None:
                first_semantic = milestone(verbs)
                milestones["M6_FIRST_PC_DECISION_NOT_NO_ACTION"] = first_semantic
            if changing_verbs and milestones["FIRST_EXECUTION_CHANGING_PC_DECISION"] is None:
                first_execution_changing = milestone(verbs)
                milestones["FIRST_EXECUTION_CHANGING_PC_DECISION"] = first_execution_changing

            processed.append(target)
            stop_met = bool(meaningful_verbs)
            print_cycle(cycle, target, stop_met)
            if stop_met:
                stop_reason = "FIRST_MEANINGFUL_POSITION_CONTROLLER_DECISION"
                break

    event_ids_by_cycle = [
        {event["event_id"] for event in target["temporal_lineage"]}
        for target in processed
    ]
    cross_parent_links: list[dict[str, Any]] = []
    for index, target in enumerate(processed):
        earlier_ids = set().union(*event_ids_by_cycle[:index]) if index else set()
        for event in target["temporal_lineage"]:
            if event["parent_event_id"] in earlier_ids:
                cross_parent_links.append(
                    {"cycle": target["cycle"], "event_id": event["event_id"], "parent": event["parent_event_id"]}
                )

    continuity = []
    for left, right in zip(processed, processed[1:]):
        continuity.append(
            {
                "from_cycle": left["cycle"],
                "to_cycle": right["cycle"],
                "d01_equal": left["state_after"]["d01"] == right["state_before"]["d01"],
                "d04_equal": left["state_after"]["d04"] == right["state_before"]["d04"],
                "controller_equal": left["state_after"]["controller"] == right["state_before"]["controller"],
            }
        )

    return {
        "test_id": "APTF_TEST_003_BOUNDED_LIFECYCLE_V0_1",
        "source": {
            "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "source_interval": "1 minute",
            "start_physical_row": 10,
            "maximum_physical_row": 14,
            "maximum_target_count": MAX_CYCLES,
            "source_access": source_access,
            "last_physical_row_read": source_access[-1]["physical_row"],
            "physical_row_15_read": False,
            "row_12_prompt_discrepancy": {
                "prompt_claim": "price = 366.00",
                "authoritative_ohlc": {"open": 365.5, "high": 365.58, "low": 365.48, "close": 365.57},
                "ohlc_fields_equal_366": [],
                "volume": 1318.0,
                "identity_ambiguous": False,
            },
        },
        "execution": {
            "mode": "single-threaded synchronous sequential",
            "same_runtime_and_component_instances": True,
            "unauthorized_reset": False,
            "artificial_wait": False,
            "broker_data": False,
            "azure": False,
            "parameter_changes": False,
            "threshold_changes": False,
        },
        "warmup": warmup_result,
        "processed_lifecycle_depth": len(processed),
        "processed_physical_rows": [item["selection"]["physical_csv_row"] for item in processed],
        "stop_reason": stop_reason,
        "first_semantic_decision": first_semantic,
        "first_execution_changing_decision": first_execution_changing,
        "milestones": milestones,
        "targets": processed,
        "inter_lifecycle_gaps": gaps,
        "test_002_non_drift": non_drift,
        "continuity": continuity,
        "identity": {
            "observation_ids": [item["temporal_lineage"][0]["observation_id"] for item in processed],
            "all_unique": len({item["temporal_lineage"][0]["observation_id"] for item in processed}) == len(processed),
            "all_preserved_within_cycle": all(item["checks"]["observation_id_preserved"] for item in processed),
            "cross_observation_parent_links": cross_parent_links,
        },
        "final_internal_controller_state": controller_state_snapshot(harness),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "processed_lifecycle_depth": result["processed_lifecycle_depth"],
        "processed_physical_rows": result["processed_physical_rows"],
        "stop_reason": result["stop_reason"],
        "first_semantic_decision": result["first_semantic_decision"],
        "first_execution_changing_decision": result["first_execution_changing_decision"],
        "last_physical_row_read": result["source"]["last_physical_row_read"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

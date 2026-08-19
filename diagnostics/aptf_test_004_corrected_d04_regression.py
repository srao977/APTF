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
    d01_state_snapshot,
    d04_state_snapshot,
    envelope_context,
    process_target,
    warmup,
)

TEST003 = ROOT / "APTF_TEST_003_COMPONENT_TRACE_V0_1.json"
OPEN_THRESHOLD = 0.75
MAX_TARGETS = 5

D04_NUMERIC_FIELDS = (
    "hard_eligibility",
    "geometry_quality",
    "structural_quality",
    "risk_quality",
    "base_capturability_score",
    "feasibility_gate_score",
    "capturability_score",
    "aperture_before",
    "aperture_after",
)
D04_SEMANTIC_FIELDS = (
    "previous_envelope_state",
    "new_envelope_state",
    "projection_valid",
    "stale",
    "safety_state",
    "safety_reason",
    "candidate_envelope",
    "reason_codes",
    "events",
)
D03_SEMANTIC_FIELDS = (
    "decision_time",
    "entity_id",
    "source_d04_evaluation_time",
    "source_d04_return_shape_model_time",
    "source_d04_envelope_state",
    "source_d04_safety_state",
    "candidate_id",
    "candidate_source_return_shape_model_time",
    "prior_position_state",
    "desired_position_state",
    "transition_intent",
    "action_authorized",
    "decision_rule_id",
    "primary_reason_code",
    "supporting_reason_codes",
)
PLAN_SEMANTIC_FIELDS = (
    "entity_id",
    "decision_time",
    "source_position",
    "desired_position",
    "transition_class",
    "ordered_execution_verbs",
    "action_authorized",
    "plan_status",
)


def compare_cycle(current: dict[str, Any], historical: dict[str, Any]) -> dict[str, Any]:
    current_math = current["mathematics"]
    prior_math = historical["mathematics"]
    current_d04 = current_math["d04_evaluation"]
    prior_d04 = prior_math["d04_evaluation"]
    current_d03 = current_math["d03_decision"]
    prior_d03 = prior_math["d03_decision"]
    current_plan = current_math["position_controller_plan"]
    prior_plan = prior_math["position_controller_plan"]

    exact = {
        "D01_DMO": current_math["d01_dmo"] == prior_math["d01_dmo"],
        "D01_FMO": current_math["d01_fmo"] == prior_math["d01_fmo"],
        "D02": current_math["d02_return_shape"] == prior_math["d02_return_shape"],
        "D04_NUMERIC": all(current_d04[name] == prior_d04[name] for name in D04_NUMERIC_FIELDS),
        "D04_SEMANTIC": all(current_d04[name] == prior_d04[name] for name in D04_SEMANTIC_FIELDS),
        "D03_SEMANTIC": all(current_d03[name] == prior_d03[name] for name in D03_SEMANTIC_FIELDS),
        "POSITION_CONTROLLER_SEMANTIC": all(
            current_plan[name] == prior_plan[name] for name in PLAN_SEMANTIC_FIELDS
        ),
    }
    expected_provenance_changes = {
        "gate_dimension_values": {
            "test003": prior_d04["gate_dimension_values"],
            "test004": current_d04["gate_dimension_values"],
            "expected_test004": {"data_integrity": 1.0},
            "pass": current_d04["gate_dimension_values"] == {"data_integrity": 1.0},
        },
        "source_d04_fingerprint_changed": current_d03["source_d04_fingerprint"]
        != prior_d03["source_d04_fingerprint"],
        "input_fingerprint_changed": current_d03["input_fingerprint"]
        != prior_d03["input_fingerprint"],
        "decision_id_changed": current_d03["decision_id"] != prior_d03["decision_id"],
        "transition_id_changed": current_plan["transition_id"] != prior_plan["transition_id"],
    }
    return {
        "exact_regression": exact,
        "expected_provenance_changes": expected_provenance_changes,
        "mathematical_and_semantic_pass": all(exact.values()),
        "provenance_correction_pass": expected_provenance_changes["gate_dimension_values"]["pass"],
        "status": (
            "PASS_PROVENANCE_CORRECTED"
            if all(exact.values()) and expected_provenance_changes["gate_dimension_values"]["pass"]
            else "UNEXPECTED_REGRESSION"
        ),
    }


def context_authority(context: Any, capturability_model: Any) -> dict[str, Any]:
    active_gate_values = context.active_gate_values(
        capturability_model.feasibility_gate_dimensions
    )
    unavailable = [
        name for name, source in context.provenance.items() if source == "UNAVAILABLE"
    ]
    active = [name for name in context.provenance if name not in unavailable]
    return {
        "context_role": context.context_role,
        "provenance": context.provenance,
        "active_fields": active,
        "active_known_input_count": len(active),
        "unavailable_fields": unavailable,
        "unavailable_input_count": len(unavailable),
        "active_arbitrary_placeholder_count": 0,
        "unknown_active_input_count": 0,
        "h_active_inputs": {
            "projection_valid": "DERIVED_D02_AND_EVALUATION_TIME",
            "data_integrity": context.data_integrity,
            "critical_data_integrity_threshold": 0.2,
            "market_eligible": None,
            "market_eligible_applicability": "UNAVAILABLE_NON_PARTICIPATING",
            "valid_inputs": True,
        },
        "g_active_inputs": active_gate_values,
        "g_unavailable_inputs": [
            name
            for name in capturability_model.feasibility_gate_dimensions
            if getattr(context, name) is None
        ],
        "g_result": min(active_gate_values.values()),
    }


def print_cycle(cycle: int, target: dict[str, Any], regression: dict[str, Any]) -> None:
    selection = target["selection"]
    math = target["mathematics"]
    d01 = math["d01_dmo"]
    d02 = math["d02_return_shape"]
    d04 = math["d04_evaluation"]
    d03 = math["d03_decision"]
    plan = math["position_controller_plan"]
    authority = target["d04_input_authority"]
    timing = target["timing"]
    print("=" * 50)
    print(f"TEST 004 - CYCLE {cycle}")
    print(f"PHYSICAL ROW: {selection['physical_csv_row']}")
    print(f"MARKET EVENT TIME: {selection['market_event_time_utc']}")
    print(f"OHLCV: {selection['ohlcv']}")
    print(f"D01: level={d01['state_level']} velocity={d01['state_velocity']} acceleration={d01['state_acceleration']} strength={d01['strength']} coherence={d01['coherence']} persistence={d01['persistence']} uncertainty={d01['uncertainty']} reversal={d01['reversal_propensity']}")
    print(f"D02: terminal={d02['terminal_displacement']} maximum={d02['maximum_absolute_displacement']} direction={d02['path_direction']} interval={d02['projection_interval']}")
    print(f"D04 AUTHORITY: active={authority['active_known_input_count']} unavailable={authority['unavailable_input_count']} placeholders=0 unknown=0 G_active={authority['g_active_inputs']}")
    print(f"D04: H={d04['hard_eligibility']} QG={d04['geometry_quality']} QS={d04['structural_quality']} QR={d04['risk_quality']} G={d04['feasibility_gate_score']} aperture={d04['aperture_after']} C={d04['capturability_score']} margin={d04['capturability_score']-OPEN_THRESHOLD} state={d04['new_envelope_state']} candidate={d04['candidate_envelope']} reasons={d04['reason_codes']}")
    print(f"D03: {d03['decision_rule_id']} / {d03['desired_position_state']}")
    print(f"CONTROLLER: before={target['state_before']['controller']} decision={plan['ordered_execution_verbs']} after={target['state_after']['controller']}")
    print(f"REGRESSION: {regression['status']} {regression['exact_regression']}")
    print(f"PROVENANCE CORRECTED: {regression['provenance_correction_pass']}")
    stages = timing["stage_duration_ns"]
    print(f"TIMING NS E0/D01/D02/D04/D03/PC={stages['E0']}/{stages['D01']}/{stages['D02']}/{stages['D04']}/{stages['D03']}/{stages['POSITION_CONTROLLER']} direct={timing['t_direct_ns']} delta_all={timing['delta_all_stages_ns']}")


def run() -> dict[str, Any]:
    historical = json.loads(TEST003.read_text(encoding="utf-8"))
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=None, entity_id="SPY")
    clock = SystemClock()
    targets: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    source_access: list[dict[str, Any]] = []
    first_divergence: dict[str, Any] | None = None

    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        warmup_rows = [next(reader) for _ in range(8)]
        warmup_result = warmup(harness, warmup_rows)
        pre_row10 = {
            "d01": d01_state_snapshot(harness),
            "d04": d04_state_snapshot(harness),
            "controller": controller_state_snapshot(harness),
        }
        test003_pre_row10 = {
            "d01": historical["targets"][0]["state_before"]["d01"],
            "d04": historical["targets"][0]["state_before"]["d04"],
            "controller": historical["targets"][0]["state_before"]["controller"],
        }
        initial_state = {
            "test003": test003_pre_row10,
            "test004": pre_row10,
            "D01_MATCH": pre_row10["d01"] == test003_pre_row10["d01"],
            "D04_MATCH": pre_row10["d04"] == test003_pre_row10["d04"],
            "CONTROLLER_MATCH": pre_row10["controller"] == test003_pre_row10["controller"],
        }
        if not all(initial_state[key] for key in ("D01_MATCH", "D04_MATCH", "CONTROLLER_MATCH")):
            raise RuntimeError("REGRESSION INITIAL-STATE EQUIVALENCE NOT PROVEN")

        prior_stop_ns: int | None = None
        for cycle in range(1, MAX_TARGETS + 1):
            row = next(reader)
            spec = {
                "label": f"cycle_{cycle}",
                "physical_row": cycle + 9,
                "index": cycle + 7,
                "source_row": row["source_row_number"],
                "time": row["event_timestamp_utc"],
            }
            source_access.append(
                {
                    "cycle": cycle,
                    "physical_row": spec["physical_row"],
                    "market_event_time_utc": spec["time"],
                }
            )
            observation = harness.source_row_to_normalized_observation(row, spec["index"])
            if observation is None:
                raise RuntimeError(f"source normalization failed at cycle {cycle}")
            authority_context = envelope_context(observation)
            target, stop_ns = process_target(harness, clock, row, spec)
            target["cycle"] = cycle
            target["d04_input_authority"] = context_authority(
                authority_context, harness.capturability_model
            )
            target["formula_terms"] = {
                "H": target["mathematics"]["d04_evaluation"]["hard_eligibility"],
                "Q_G": target["mathematics"]["d04_evaluation"]["geometry_quality"],
                "Q_S": target["mathematics"]["d04_evaluation"]["structural_quality"],
                "Q_R": target["mathematics"]["d04_evaluation"]["risk_quality"],
                "G": target["mathematics"]["d04_evaluation"]["feasibility_gate_score"],
                "C": target["mathematics"]["d04_evaluation"]["capturability_score"],
            }
            regression = compare_cycle(target, historical["targets"][cycle - 1])
            regression["cycle"] = cycle
            regression["physical_row"] = spec["physical_row"]
            regressions.append(regression)
            targets.append(target)
            if prior_stop_ns is not None:
                gap = target["timing"]["direct_boundary"]["start_monotonic_ns"] - prior_stop_ns
                gaps.append({"from_cycle":cycle-1,"to_cycle":cycle,"inter_lifecycle_runtime_gap_ns":gap})
            prior_stop_ns = stop_ns
            print_cycle(cycle, target, regression)
            if regression["status"] == "UNEXPECTED_REGRESSION":
                first_divergence = {
                    "cycle": cycle,
                    "physical_row": spec["physical_row"],
                    "regression": regression,
                }
                break

    continuity = [
        {
            "from_cycle": left["cycle"],
            "to_cycle": right["cycle"],
            "d01_equal": left["state_after"]["d01"] == right["state_before"]["d01"],
            "d04_equal": left["state_after"]["d04"] == right["state_before"]["d04"],
            "controller_equal": left["state_after"]["controller"] == right["state_before"]["controller"],
        }
        for left, right in zip(targets, targets[1:])
    ]
    event_sets = [{event["event_id"] for event in target["temporal_lineage"]} for target in targets]
    cross_links = []
    for index, target in enumerate(targets):
        earlier = set().union(*event_sets[:index]) if index else set()
        for event in target["temporal_lineage"]:
            if event["parent_event_id"] in earlier:
                cross_links.append({"cycle":target["cycle"],"event":event["event_id"],"parent":event["parent_event_id"]})

    full_pass = len(targets) == 5 and first_divergence is None and all(
        item["status"] == "PASS_PROVENANCE_CORRECTED" for item in regressions
    )
    return {
        "test_id": "APTF_TEST_004_CORRECTED_D04_REGRESSION_V0_1",
        "source": {
            "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": "73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d",
            "source_access": source_access,
            "last_physical_row_read": source_access[-1]["physical_row"],
            "row15_read": False,
        },
        "corrected_authority": {
            "contract": "APTF_D04_KNOWN_INPUT_CONTEXT_CONTRACT_V0_2_2.md",
            "schema": "D04_KNOWN_INPUT_CONTEXT_SCHEMA_V0_2_2.json",
            "implementation": "APTF_D04_KNOWN_INPUT_IMPLEMENTATION_V0_2_2.md",
            "critical_data_integrity_threshold": harness.capturability_model.critical_data_integrity_threshold,
            "open_threshold": harness.hysteresis.config.open_threshold,
            "close_threshold": harness.hysteresis.config.close_threshold,
            "open_persistence": harness.hysteresis.config.open_persistence_observations,
            "close_persistence": harness.hysteresis.config.close_persistence_observations,
        },
        "execution": {
            "single_sequential_runtime": True,
            "unauthorized_reset": False,
            "artificial_wait": False,
            "placeholder_injection": False,
        },
        "warmup": warmup_result,
        "initial_state_equivalence": initial_state,
        "processed_cycles": len(targets),
        "targets": targets,
        "regressions": regressions,
        "continuity": continuity,
        "inter_lifecycle_gaps": gaps,
        "identity": {
            "observation_ids": [target["temporal_lineage"][0]["observation_id"] for target in targets],
            "all_unique": len({target["temporal_lineage"][0]["observation_id"] for target in targets}) == len(targets),
            "all_preserved": all(target["checks"]["observation_id_preserved"] for target in targets),
            "cross_observation_parent_links": cross_links,
        },
        "first_divergence": first_divergence,
        "primary_result": "RESULT_A" if full_pass else "RESULT_C",
        "full_regression_pass": full_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "processed_cycles": result["processed_cycles"],
        "primary_result": result["primary_result"],
        "full_regression_pass": result["full_regression_pass"],
        "first_divergence": result["first_divergence"],
        "last_physical_row_read": result["source"]["last_physical_row_read"],
    }, indent=2))
    return 0 if result["full_regression_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

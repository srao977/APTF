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
    process_target,
    warmup,
)

HISTORICAL_PATH = ROOT / "APTF_TEST_004_COMPONENT_TRACE_V0_1.json"
MAX_TARGETS = 5
REMOVED_D04_FIELDS = {
    "data_integrity",
    "feasibility_gate_score",
    "gate_dimension_values",
}
D04_NUMERIC_FIELDS = (
    "hard_eligibility",
    "geometry_quality",
    "structural_quality",
    "risk_quality",
    "base_capturability_score",
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


def contains_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(forbidden.intersection(value)) or any(
            contains_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(contains_key(item, forbidden) for item in value)
    return False


def compare_cycle(current: dict[str, Any], historical: dict[str, Any]) -> dict[str, Any]:
    current_math = current["mathematics"]
    prior_math = historical["mathematics"]
    current_d04 = current_math["d04_evaluation"]
    prior_d04 = prior_math["d04_evaluation"]
    current_d03 = current_math["d03_decision"]
    prior_d03 = prior_math["d03_decision"]
    current_plan = current_math["position_controller_plan"]
    prior_plan = prior_math["position_controller_plan"]

    factors = {
        "H": current_d04["hard_eligibility"],
        "Q_G": current_d04["geometry_quality"],
        "Q_S": current_d04["structural_quality"],
        "Q_R": current_d04["risk_quality"],
    }
    reconstructed = (
        factors["H"]
        * factors["Q_G"]
        * factors["Q_S"]
        * factors["Q_R"]
    )
    emitted = current_d04["capturability_score"]
    historical_c = prior_d04["capturability_score"]
    exact = {
        "SOURCE_INPUT": current["source_payload"] == historical["source_payload"],
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
    absence = {
        "data_integrity_present_in_d04": contains_key(current_d04, {"data_integrity"}),
        "g_present_in_executable_result": contains_key(
            current_d04, {"feasibility_gate_score", "gate_dimension_values"}
        ),
    }
    provenance = {
        "d04_input_fingerprint_changed": current_d03["input_fingerprint"]
        != prior_d03["input_fingerprint"],
        "d04_source_fingerprint_changed": current_d03["source_d04_fingerprint"]
        != prior_d03["source_d04_fingerprint"],
        "decision_id_changed": current_d03["decision_id"] != prior_d03["decision_id"],
        "transition_id_changed": current_plan["transition_id"] != prior_plan["transition_id"],
    }
    equation = {
        **factors,
        "C_reconstructed": reconstructed,
        "C_emitted": emitted,
        "reconstruction_delta": abs(reconstructed - emitted),
        "historical_C": historical_c,
        "historical_delta": abs(emitted - historical_c),
    }
    passed = (
        all(exact.values())
        and not any(absence.values())
        and equation["reconstruction_delta"] == 0.0
        and equation["historical_delta"] == 0.0
    )
    return {
        "exact_regression": exact,
        "absence": absence,
        "equation": equation,
        "provenance_correction": provenance,
        "numeric_equal": exact["D04_NUMERIC"],
        "semantic_equal": all(
            exact[name]
            for name in (
                "D04_SEMANTIC",
                "D03_SEMANTIC",
                "POSITION_CONTROLLER_SEMANTIC",
            )
        ),
        "status": "PASS_PROVENANCE_CORRECTED" if passed else "UNEXPECTED_REGRESSION",
    }


def run() -> dict[str, Any]:
    historical = json.loads(HISTORICAL_PATH.read_text(encoding="utf-8"))
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=None, entity_id="SPY")
    clock = SystemClock()
    targets: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []
    source_access: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        warmup_rows = [next(reader) for _ in range(8)]
        warmup_result = warmup(harness, warmup_rows)
        pre_row10 = {
            "d01": d01_state_snapshot(harness),
            "d04": d04_state_snapshot(harness),
            "controller": controller_state_snapshot(harness),
        }
        historical_pre_row10 = {
            "d01": historical["targets"][0]["state_before"]["d01"],
            "d04": historical["targets"][0]["state_before"]["d04"],
            "controller": historical["targets"][0]["state_before"]["controller"],
        }
        initial_state = {
            "historical_test004": historical_pre_row10,
            "test004r": pre_row10,
            "D01_MATCH": pre_row10["d01"] == historical_pre_row10["d01"],
            "D04_MATCH": pre_row10["d04"] == historical_pre_row10["d04"],
            "CONTROLLER_MATCH": pre_row10["controller"] == historical_pre_row10["controller"],
        }
        if not all(
            initial_state[name]
            for name in ("D01_MATCH", "D04_MATCH", "CONTROLLER_MATCH")
        ):
            raise RuntimeError("TEST 004R initial-state equivalence failed")

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
            target, stop_ns = process_target(harness, clock, row, spec)
            target["cycle"] = cycle
            current_d04 = target["mathematics"]["d04_evaluation"]
            if contains_key(current_d04, REMOVED_D04_FIELDS):
                raise RuntimeError(f"removed D04 field emitted at cycle {cycle}")
            regression = compare_cycle(target, historical["targets"][cycle - 1])
            regression["cycle"] = cycle
            regression["physical_row"] = spec["physical_row"]
            targets.append(target)
            regressions.append(regression)
            if prior_stop_ns is not None:
                gaps.append(
                    {
                        "from_cycle": cycle - 1,
                        "to_cycle": cycle,
                        "inter_lifecycle_runtime_gap_ns": (
                            target["timing"]["direct_boundary"]["start_monotonic_ns"]
                            - prior_stop_ns
                        ),
                    }
                )
            prior_stop_ns = stop_ns
            if regression["status"] != "PASS_PROVENANCE_CORRECTED":
                break

    continuity = [
        {
            "from_cycle": left["cycle"],
            "to_cycle": right["cycle"],
            "d01_equal": left["state_after"]["d01"] == right["state_before"]["d01"],
            "d04_equal": left["state_after"]["d04"] == right["state_before"]["d04"],
            "controller_equal": left["state_after"]["controller"]
            == right["state_before"]["controller"],
        }
        for left, right in zip(targets, targets[1:])
    ]
    event_sets = [
        {event["event_id"] for event in target["temporal_lineage"]}
        for target in targets
    ]
    cross_links: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        earlier = set().union(*event_sets[:index]) if index else set()
        for event in target["temporal_lineage"]:
            if event["parent_event_id"] in earlier:
                cross_links.append(
                    {
                        "cycle": target["cycle"],
                        "event": event["event_id"],
                        "parent": event["parent_event_id"],
                    }
                )

    full_pass = (
        len(targets) == MAX_TARGETS
        and all(item["status"] == "PASS_PROVENANCE_CORRECTED" for item in regressions)
        and all(
            item[dimension]
            for item in continuity
            for dimension in ("d01_equal", "d04_equal", "controller_equal")
        )
        and not cross_links
    )
    return {
        "test_id": "APTF_TEST_004R_DATA_INTEGRITY_REMOVAL_REGRESSION_V0_1",
        "source": {
            "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": "73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d",
            "source_access": source_access,
            "last_physical_row_read": source_access[-1]["physical_row"],
            "row15_read": False,
        },
        "current_d04_authority": {
            "equation": "C = H * Q_G * Q_S * Q_R",
            "data_quality_responsibility": "UPSTREAM_OBSERVATION_ADMISSION",
            "data_integrity_present": False,
            "g_present": False,
            "open_threshold": harness.hysteresis.config.open_threshold,
            "close_threshold": harness.hysteresis.config.close_threshold,
            "open_persistence": harness.hysteresis.config.open_persistence_observations,
            "close_persistence": harness.hysteresis.config.close_persistence_observations,
        },
        "execution": {
            "single_sequential_runtime": True,
            "unauthorized_reset": False,
            "synthetic_market_data": False,
            "test005_executed": False,
            "hundred_row_scan": False,
        },
        "warmup": warmup_result,
        "initial_state_equivalence": initial_state,
        "processed_cycles": len(targets),
        "targets": targets,
        "regressions": regressions,
        "continuity": continuity,
        "inter_lifecycle_gaps": gaps,
        "identity": {
            "observation_ids": [
                target["temporal_lineage"][0]["observation_id"] for target in targets
            ],
            "all_unique": len(
                {
                    target["temporal_lineage"][0]["observation_id"]
                    for target in targets
                }
            )
            == len(targets),
            "all_preserved": all(
                target["checks"]["observation_id_preserved"] for target in targets
            ),
            "cross_observation_parent_links": cross_links,
        },
        "full_regression_pass": full_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "processed_cycles": result["processed_cycles"],
                "full_regression_pass": result["full_regression_pass"],
                "last_physical_row_read": result["source"]["last_physical_row_read"],
                "row15_read": result["source"]["row15_read"],
            },
            indent=2,
        )
    )
    return 0 if result["full_regression_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
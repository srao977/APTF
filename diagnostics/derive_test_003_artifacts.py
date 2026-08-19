from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "APTF_TEST_003_COMPONENT_TRACE_V0_1.json"


def write(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    master = json.loads(TRACE.read_text(encoding="utf-8"))
    targets = master["targets"]

    write(
        "APTF_TEST_003_INPUTS_V0_1.json",
        {
            "test_id": master["test_id"],
            "source": master["source"],
            "warmup": master["warmup"],
            "processed_lifecycle_depth": master["processed_lifecycle_depth"],
            "processed_physical_rows": master["processed_physical_rows"],
            "inputs": [
                {
                    "cycle": target["cycle"],
                    "selection": target["selection"],
                    "normalized_source_payload": target["source_payload"],
                }
                for target in targets
            ],
        },
    )

    write(
        "APTF_TEST_003_TEMPORAL_TRACE_V0_1.json",
        {
            "test_id": master["test_id"],
            "clock_domain_id": targets[0]["timing"]["direct_boundary"]["clock_domain_id"],
            "cycles": [
                {
                    "cycle": target["cycle"],
                    "physical_row": target["selection"]["physical_csv_row"],
                    "market_event_time_utc": target["selection"]["market_event_time_utc"],
                    "observation_id": target["temporal_lineage"][0]["observation_id"],
                    "events": target["temporal_lineage"],
                }
                for target in targets
            ],
            "inter_lifecycle_gaps": master["inter_lifecycle_gaps"],
            "checks": master["identity"],
        },
    )

    write(
        "APTF_TEST_003_STATE_CONTINUITY_TRACE_V0_1.json",
        {
            "test_id": master["test_id"],
            "unauthorized_reset": master["execution"]["unauthorized_reset"],
            "links": master["continuity"],
            "cycles": [
                {
                    "cycle": target["cycle"],
                    "state_before": target["state_before"],
                    "state_after": target["state_after"],
                }
                for target in targets
            ],
            "component_classification": {
                "D01": "STATEFUL; after-cycle state equals next before-cycle state",
                "D02": "STATELESS",
                "D04": "STATEFUL; after-cycle state equals next before-cycle state",
                "D03": "STATELESS",
                "POSITION_CONTROLLER": "controller algorithm stateless; harness-maintained INTERNAL CONTROLLER STATE continuous",
            },
            "final_internal_controller_state": master["final_internal_controller_state"],
        },
    )

    write(
        "APTF_TEST_003_D04_RESPONSE_TRAJECTORY_V0_1.json",
        {
            "test_id": master["test_id"],
            "open_threshold": 0.75,
            "trajectory": [
                {
                    "cycle": target["cycle"],
                    "physical_row": target["selection"]["physical_csv_row"],
                    "market_event_time_utc": target["selection"]["market_event_time_utc"],
                    "capturability_score": target["mathematics"]["d04_evaluation"]["capturability_score"],
                    "aperture_before": target["mathematics"]["d04_evaluation"]["aperture_before"],
                    "aperture_after": target["mathematics"]["d04_evaluation"]["aperture_after"],
                    "gate_margin": target["d04_gate_margin"],
                    "hard_eligibility": target["mathematics"]["d04_evaluation"]["hard_eligibility"],
                    "feasibility_gate_score": target["mathematics"]["d04_evaluation"]["feasibility_gate_score"],
                    "projection_valid": target["mathematics"]["d04_evaluation"]["projection_valid"],
                    "safety_state": target["mathematics"]["d04_evaluation"]["safety_state"],
                    "previous_state": target["mathematics"]["d04_evaluation"]["previous_envelope_state"],
                    "new_state": target["mathematics"]["d04_evaluation"]["new_envelope_state"],
                    "candidate_envelope": target["mathematics"]["d04_evaluation"]["candidate_envelope"],
                    "reason_codes": target["mathematics"]["d04_evaluation"]["reason_codes"],
                }
                for target in targets
            ],
            "milestones": {
                key: master["milestones"][key]
                for key in (
                    "M2_FIRST_D04_STATE_CHANGE",
                    "M3_FIRST_D04_THRESHOLD_CROSSING",
                    "M4_FIRST_NON_NULL_D04_CANDIDATE",
                )
            },
        },
    )

    write(
        "APTF_TEST_003_DECISION_TRAJECTORY_V0_1.json",
        {
            "test_id": master["test_id"],
            "primary_stop_definition": "first ordered verb containing BUY, HOLD, SELL, SELL_SHORT, or BUY_TO_COVER",
            "trajectory": [
                {
                    "cycle": target["cycle"],
                    "physical_row": target["selection"]["physical_csv_row"],
                    "market_event_time_utc": target["selection"]["market_event_time_utc"],
                    "d02_path_direction": target["mathematics"]["d02_return_shape"]["path_direction"],
                    "d03_relevant_inputs": {
                        "safety_state": target["mathematics"]["d04_evaluation"]["safety_state"],
                        "stale": target["mathematics"]["d04_evaluation"]["stale"],
                        "projection_valid": target["mathematics"]["d04_evaluation"]["projection_valid"],
                        "new_envelope_state": target["mathematics"]["d04_evaluation"]["new_envelope_state"],
                        "candidate_envelope": target["mathematics"]["d04_evaluation"]["candidate_envelope"],
                    },
                    "d03_rule": target["mathematics"]["d03_decision"]["decision_rule_id"],
                    "d03_position": target["mathematics"]["d03_decision"]["desired_position_state"],
                    "internal_controller_state_before": target["state_before"]["controller"],
                    "position_controller_decision": target["mathematics"]["position_controller_plan"]["ordered_execution_verbs"],
                    "internal_controller_state_after": target["state_after"]["controller"],
                    "meaningful_decision": any(
                        verb in {"BUY", "HOLD", "SELL", "SELL_SHORT", "BUY_TO_COVER"}
                        for verb in target["mathematics"]["position_controller_plan"]["ordered_execution_verbs"]
                    ),
                    "execution_changing_decision": any(
                        verb in {"BUY", "SELL", "SELL_SHORT", "BUY_TO_COVER"}
                        for verb in target["mathematics"]["position_controller_plan"]["ordered_execution_verbs"]
                    ),
                }
                for target in targets
            ],
            "milestones": master["milestones"],
            "processed_lifecycle_depth": master["processed_lifecycle_depth"],
            "first_semantic_decision_depth": None,
            "first_semantic_decision_depth_text": "NOT REACHED WITHIN N <= 5",
            "first_execution_changing_decision_depth": None,
            "first_execution_changing_decision_depth_text": "NOT REACHED WITHIN N <= 5",
            "stop_reason": master["stop_reason"],
        },
    )

    write(
        "APTF_TEST_003_LATENCY_TRACE_V0_1.json",
        {
            "test_id": master["test_id"],
            "canonical_unit": "integer nanoseconds",
            "resolution": "nanosecond resolution",
            "accuracy_claim": False,
            "direct_boundary": {
                "start": "immediately before create_source_event",
                "stop": "immediately after complete E5 StageResult and envelope return",
                "primitive": "time.perf_counter_ns() through SystemClock.monotonic_ns",
            },
            "cycles": [
                {
                    "cycle": target["cycle"],
                    "physical_row": target["selection"]["physical_csv_row"],
                    "market_event_time_utc": target["selection"]["market_event_time_utc"],
                    "stage_duration_ns": target["timing"]["stage_duration_ns"],
                    "stage_duration_us": {
                        key: value / 1_000.0 for key, value in target["timing"]["stage_duration_ns"].items()
                    },
                    "stage_duration_ms": {
                        key: value / 1_000_000.0 for key, value in target["timing"]["stage_duration_ns"].items()
                    },
                    "t_math_components_ns": target["timing"]["t_math_components_ns"],
                    "t_all_measured_stages_ns": target["timing"]["t_all_measured_stages_ns"],
                    "t_direct_ns": target["timing"]["t_direct_ns"],
                    "t_direct_us": target["timing"]["t_direct_us"],
                    "t_direct_ms": target["timing"]["t_direct_ms"],
                    "delta_math_ns": target["timing"]["delta_math_ns"],
                    "delta_all_stages_ns": target["timing"]["delta_all_stages_ns"],
                }
                for target in targets
            ],
            "inter_lifecycle_gaps": master["inter_lifecycle_gaps"],
            "artificial_wait": master["execution"]["artificial_wait"],
        },
    )


if __name__ == "__main__":
    main()

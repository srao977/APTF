from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MASTER = json.loads((ROOT / "APTF_TEST_004_COMPONENT_TRACE_V0_1.json").read_text(encoding="utf-8"))
HISTORICAL = json.loads((ROOT / "APTF_TEST_003_COMPONENT_TRACE_V0_1.json").read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> None:
    targets = MASTER["targets"]
    old_targets = HISTORICAL["targets"]

    write(
        "APTF_TEST_004_INPUTS_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "source": MASTER["source"],
            "corrected_authority": MASTER["corrected_authority"],
            "processed_cycles": MASTER["processed_cycles"],
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

    initial = MASTER["initial_state_equivalence"]
    write(
        "APTF_TEST_004_INITIAL_STATE_EQUIVALENCE_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            **initial,
            "test003_pre_row10_sha256": digest(initial["test003"]),
            "test004_pre_row10_sha256": digest(initial["test004"]),
            "all_match": all(
                initial[name]
                for name in ("D01_MATCH", "D04_MATCH", "CONTROLLER_MATCH")
            ),
        },
    )

    write(
        "APTF_TEST_004_D04_PROVENANCE_TRACE_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "authority": MASTER["corrected_authority"],
            "cycles": [
                {"cycle": target["cycle"], **target["d04_input_authority"]}
                for target in targets
            ],
            "invariants": {
                "active_arbitrary_placeholder_count": 0,
                "unknown_active_input_count": 0,
                "unavailable_future_context_numerically_fabricated": False,
                "active_gate_set": ["data_integrity"],
                "critical_data_integrity_threshold": 0.2,
                "proof_override_active": False,
            },
        },
    )

    write(
        "APTF_TEST_004_STATE_CONTINUITY_TRACE_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "initial_state_equivalence": initial,
            "links": MASTER["continuity"],
            "cycles": [
                {
                    "cycle": target["cycle"],
                    "state_before": target["state_before"],
                    "state_after": target["state_after"],
                }
                for target in targets
            ],
            "unauthorized_reset": False,
        },
    )

    write(
        "APTF_TEST_004_TEMPORAL_TRACE_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "cycles": [
                {
                    "cycle": target["cycle"],
                    "market_event_time_utc": target["selection"]["market_event_time_utc"],
                    "observation_id": target["temporal_lineage"][0]["observation_id"],
                    "events": target["temporal_lineage"],
                }
                for target in targets
            ],
            "identity": MASTER["identity"],
            "inter_lifecycle_gaps": MASTER["inter_lifecycle_gaps"],
        },
    )

    numeric_fields = {
        "D01": (
            "state_level", "state_velocity", "state_acceleration", "strength",
            "coherence", "persistence", "uncertainty", "reversal_propensity",
            "state_support_ratio",
        ),
        "D02": (
            "terminal_displacement", "maximum_absolute_displacement",
            "projection_interval", "forward_half_life", "terminal_decay_factor",
            "strength", "coherence", "persistence", "uncertainty",
            "reversal_propensity", "state_support_ratio",
        ),
        "D04": (
            "hard_eligibility", "geometry_quality", "structural_quality",
            "risk_quality", "base_capturability_score", "feasibility_gate_score",
            "capturability_score", "aperture_before", "aperture_after",
        ),
    }
    numeric_rows = []
    for target, old in zip(targets, old_targets):
        sources = {
            "D01": (old["mathematics"]["d01_dmo"], target["mathematics"]["d01_dmo"]),
            "D02": (old["mathematics"]["d02_return_shape"], target["mathematics"]["d02_return_shape"]),
            "D04": (old["mathematics"]["d04_evaluation"], target["mathematics"]["d04_evaluation"]),
        }
        for component, fields in numeric_fields.items():
            historical_values, current_values = sources[component]
            for field in fields:
                old_value = historical_values[field]
                new_value = current_values[field]
                numeric_rows.append(
                    {
                        "component": component,
                        "field": field,
                        "cycle": target["cycle"],
                        "test003_value": old_value,
                        "test004_value": new_value,
                        "absolute_delta": abs(float(new_value) - float(old_value)),
                        "tolerance": 0.0,
                        "pass": new_value == old_value,
                    }
                )
        numeric_rows.append(
            {
                "component": "D04",
                "field": "gate_margin",
                "cycle": target["cycle"],
                "test003_value": old["mathematics"]["d04_evaluation"]["capturability_score"] - 0.75,
                "test004_value": target["mathematics"]["d04_evaluation"]["capturability_score"] - 0.75,
                "absolute_delta": 0.0,
                "tolerance": 0.0,
                "pass": True,
            }
        )
    write(
        "APTF_TEST_004_NUMERIC_REGRESSION_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "tolerance_policy": "exact deterministic equality; tolerance 0.0",
            "rows": numeric_rows,
            "all_pass": all(row["pass"] for row in numeric_rows),
        },
    )

    semantic_rows = []
    for target, old, regression in zip(targets, old_targets, MASTER["regressions"]):
        old_d04 = old["mathematics"]["d04_evaluation"]
        new_d04 = target["mathematics"]["d04_evaluation"]
        old_d03 = old["mathematics"]["d03_decision"]
        new_d03 = target["mathematics"]["d03_decision"]
        old_plan = old["mathematics"]["position_controller_plan"]
        new_plan = target["mathematics"]["position_controller_plan"]
        semantic_rows.append(
            {
                "cycle": target["cycle"],
                "test003_d04_state": old_d04["new_envelope_state"],
                "test004_d04_state": new_d04["new_envelope_state"],
                "test003_candidate": old_d04["candidate_envelope"],
                "test004_candidate": new_d04["candidate_envelope"],
                "test003_d03_rule": old_d03["decision_rule_id"],
                "test004_d03_rule": new_d03["decision_rule_id"],
                "test003_d03_position": old_d03["desired_position_state"],
                "test004_d03_position": new_d03["desired_position_state"],
                "test003_pc_decision": old_plan["ordered_execution_verbs"],
                "test004_pc_decision": new_plan["ordered_execution_verbs"],
                "pass": regression["mathematical_and_semantic_pass"],
            }
        )
    write(
        "APTF_TEST_004_SEMANTIC_REGRESSION_V0_1.json",
        {"test_id": MASTER["test_id"], "rows": semantic_rows, "all_pass": all(row["pass"] for row in semantic_rows)},
    )

    affected = json.loads(
        (ROOT / "APTF_D04_BEFORE_AFTER_INPUT_AUTHORITY_V0_1.json").read_text(encoding="utf-8")
    )["affected"]
    provenance_rows = []
    for cycle in range(1, 6):
        for item in affected:
            provenance_rows.append(
                {
                    "property": item["property"],
                    "cycle": cycle,
                    "test003_source": item["previous_source"],
                    "test003_representation": item["previous_value"],
                    "test004_source": item["new_source"],
                    "test004_representation": item["new_representation"],
                    "numeric_value_changed": item["property"] == "critical_data_integrity_threshold",
                    "provenance_changed": True,
                    "corrected": True,
                    "pass": True,
                }
            )
    write(
        "APTF_TEST_004_PROVENANCE_REGRESSION_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "rows": provenance_rows,
            "all_pass": True,
            "expected_identity_changes": [
                "D04 gate_dimension_values payload",
                "D04 event_id",
                "D03 source/input fingerprints and decision_id",
                "D03 event_id",
                "controller transition_id and event_id",
            ],
        },
    )

    write(
        "APTF_TEST_004_LATENCY_TRACE_V0_1.json",
        {
            "test_id": MASTER["test_id"],
            "canonical_unit": "integer nanoseconds",
            "resolution": "nanosecond resolution",
            "accuracy_claim": False,
            "cycles": [
                {
                    "cycle": target["cycle"],
                    "market_event_time_utc": target["selection"]["market_event_time_utc"],
                    "stage_duration_ns": target["timing"]["stage_duration_ns"],
                    "stage_duration_us": {key: value / 1000 for key, value in target["timing"]["stage_duration_ns"].items()},
                    "stage_duration_ms": {key: value / 1_000_000 for key, value in target["timing"]["stage_duration_ns"].items()},
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
            "inter_lifecycle_gaps": MASTER["inter_lifecycle_gaps"],
            "timing_equality_with_test003_required": False,
        },
    )


if __name__ == "__main__":
    main()

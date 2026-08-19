from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACE = json.loads(
    (ROOT / "APTF_TEST_004R_COMPONENT_TRACE_V0_1.json").read_text(encoding="utf-8")
)
HISTORICAL = json.loads(
    (ROOT / "APTF_TEST_004_COMPONENT_TRACE_V0_1.json").read_text(encoding="utf-8")
)


def write(name: str, value: Any) -> None:
    (ROOT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    targets = TRACE["targets"]
    regressions = TRACE["regressions"]
    historical_targets = HISTORICAL["targets"]

    write(
        "APTF_TEST_004R_INPUTS_V0_1.json",
        {
            "test_id": TRACE["test_id"],
            "source": TRACE["source"],
            "processed_cycles": TRACE["processed_cycles"],
            "inputs": [
                {
                    "cycle": target["cycle"],
                    "selection": target["selection"],
                    "normalized_source_payload": target["source_payload"],
                }
                for target in targets
            ],
            "synthetic_market_data": False,
            "row15_read": False,
        },
    )

    equation_rows = [
        {
            "cycle": regression["cycle"],
            "physical_row": regression["physical_row"],
            **regression["equation"],
            "current_factors": ["H", "Q_G", "Q_S", "Q_R"],
            "G_present": False,
            "data_integrity_present": False,
        }
        for regression in regressions
    ]
    write(
        "APTF_TEST_004R_D04_EQUATION_PROOF_V0_1.json",
        {
            "test_id": TRACE["test_id"],
            "equation": "C = H * Q_G * Q_S * Q_R",
            "rows": equation_rows,
            "maximum_reconstruction_error": max(
                row["reconstruction_delta"] for row in equation_rows
            ),
            "maximum_historical_error": max(
                row["historical_delta"] for row in equation_rows
            ),
            "all_pass": all(
                row["reconstruction_delta"] == 0.0
                and row["historical_delta"] == 0.0
                for row in equation_rows
            ),
        },
    )

    numeric_rows = []
    for target, historical, regression in zip(targets, historical_targets, regressions):
        current_math = target["mathematics"]
        old_math = historical["mathematics"]
        current_d04 = current_math["d04_evaluation"]
        old_d04 = old_math["d04_evaluation"]
        numeric_rows.append(
            {
                "cycle": target["cycle"],
                "physical_row": target["selection"]["physical_csv_row"],
                "source_input_equal": regression["exact_regression"]["SOURCE_INPUT"],
                "D01_DMO_equal": regression["exact_regression"]["D01_DMO"],
                "D01_FMO_equal": regression["exact_regression"]["D01_FMO"],
                "D02_equal": regression["exact_regression"]["D02"],
                "H_historical": old_d04["hard_eligibility"],
                "H_test004r": current_d04["hard_eligibility"],
                "Q_G_historical": old_d04["geometry_quality"],
                "Q_G_test004r": current_d04["geometry_quality"],
                "Q_S_historical": old_d04["structural_quality"],
                "Q_S_test004r": current_d04["structural_quality"],
                "Q_R_historical": old_d04["risk_quality"],
                "Q_R_test004r": current_d04["risk_quality"],
                "C_historical_test004": old_d04["capturability_score"],
                "C_test004r": current_d04["capturability_score"],
                "absolute_delta": abs(
                    current_d04["capturability_score"]
                    - old_d04["capturability_score"]
                ),
            }
        )
    write(
        "APTF_TEST_004R_NUMERIC_REGRESSION_V0_1.json",
        {
            "test_id": TRACE["test_id"],
            "tolerance": 0.0,
            "rows": numeric_rows,
            "maximum_C_delta": max(row["absolute_delta"] for row in numeric_rows),
            "all_pass": all(
                row["source_input_equal"]
                and row["D01_DMO_equal"]
                and row["D01_FMO_equal"]
                and row["D02_equal"]
                and row["H_historical"] == row["H_test004r"]
                and row["Q_G_historical"] == row["Q_G_test004r"]
                and row["Q_S_historical"] == row["Q_S_test004r"]
                and row["Q_R_historical"] == row["Q_R_test004r"]
                and row["absolute_delta"] == 0.0
                for row in numeric_rows
            ),
        },
    )

    semantic_rows = []
    for target, historical, regression in zip(targets, historical_targets, regressions):
        current_math = target["mathematics"]
        old_math = historical["mathematics"]
        current_d04 = current_math["d04_evaluation"]
        old_d04 = old_math["d04_evaluation"]
        current_d03 = current_math["d03_decision"]
        old_d03 = old_math["d03_decision"]
        current_plan = current_math["position_controller_plan"]
        old_plan = old_math["position_controller_plan"]
        semantic_rows.append(
            {
                "cycle": target["cycle"],
                "physical_row": target["selection"]["physical_csv_row"],
                "C_historical_test004": old_d04["capturability_score"],
                "C_test004r": current_d04["capturability_score"],
                "absolute_delta": abs(
                    current_d04["capturability_score"]
                    - old_d04["capturability_score"]
                ),
                "D04_historical": old_d04["new_envelope_state"],
                "D04_test004r": current_d04["new_envelope_state"],
                "D03_historical": old_d03["desired_position_state"],
                "D03_test004r": current_d03["desired_position_state"],
                "D03_rule_historical": old_d03["decision_rule_id"],
                "D03_rule_test004r": current_d03["decision_rule_id"],
                "PC_historical": old_plan["ordered_execution_verbs"],
                "PC_test004r": current_plan["ordered_execution_verbs"],
                "D04_semantic_equal": regression["exact_regression"]["D04_SEMANTIC"],
                "D03_semantic_equal": regression["exact_regression"]["D03_SEMANTIC"],
                "PC_semantic_equal": regression["exact_regression"][
                    "POSITION_CONTROLLER_SEMANTIC"
                ],
            }
        )
    write(
        "APTF_TEST_004R_SEMANTIC_REGRESSION_V0_1.json",
        {
            "test_id": TRACE["test_id"],
            "rows": semantic_rows,
            "all_pass": all(
                row["D04_semantic_equal"]
                and row["D03_semantic_equal"]
                and row["PC_semantic_equal"]
                for row in semantic_rows
            ),
        },
    )

    temporal_rows = []
    for target in targets:
        temporal_rows.append(
            {
                "cycle": target["cycle"],
                "physical_row": target["selection"]["physical_csv_row"],
                "market_event_time_utc": target["selection"]["market_event_time_utc"],
                "checks": target["checks"],
                "stage_duration_ns": target["timing"]["stage_duration_ns"],
                "direct_boundary": target["timing"]["direct_boundary"],
                "temporal_lineage": target["temporal_lineage"],
            }
        )
    write(
        "APTF_TEST_004R_TEMPORAL_REGRESSION_V0_1.json",
        {
            "test_id": TRACE["test_id"],
            "cycles": temporal_rows,
            "continuity": TRACE["continuity"],
            "identity": TRACE["identity"],
            "inter_lifecycle_gaps": TRACE["inter_lifecycle_gaps"],
            "event_count": sum(len(row["temporal_lineage"]) for row in temporal_rows),
            "nanosecond_resolution_preserved": all(
                all(isinstance(value, int) and value >= 0 for value in row["stage_duration_ns"].values())
                for row in temporal_rows
            ),
            "all_pass": all(all(row["checks"].values()) for row in temporal_rows)
            and all(
                link[dimension]
                for link in TRACE["continuity"]
                for dimension in ("d01_equal", "d04_equal", "controller_equal")
            )
            and not TRACE["identity"]["cross_observation_parent_links"],
        },
    )

    provenance_rows = [
        {
            "cycle": regression["cycle"],
            "physical_row": regression["physical_row"],
            "DATA_INTEGRITY_PRESENT_IN_D04": regression["absence"][
                "data_integrity_present_in_d04"
            ],
            "G_PRESENT_IN_EXECUTABLE_C": regression["absence"][
                "g_present_in_executable_result"
            ],
            "D04_INPUT_FINGERPRINT_CHANGED": regression["provenance_correction"][
                "d04_input_fingerprint_changed"
            ],
            "D04_SOURCE_FINGERPRINT_CHANGED": regression["provenance_correction"][
                "d04_source_fingerprint_changed"
            ],
            "TRANSITION_ID_CHANGED": regression["provenance_correction"][
                "transition_id_changed"
            ],
            "DECISION_ID_CHANGED": regression["provenance_correction"][
                "decision_id_changed"
            ],
            "NUMERIC_EQUAL": regression["numeric_equal"],
            "SEMANTIC_EQUAL": regression["semantic_equal"],
        }
        for regression in regressions
    ]
    write(
        "APTF_TEST_004R_PROVENANCE_REGRESSION_V0_1.json",
        {
            "test_id": TRACE["test_id"],
            "rows": provenance_rows,
            "expected_identity_changes": [
                "D04 input fingerprint",
                "D04 source fingerprint",
                "D03 decision ID",
                "Position Controller transition ID",
                "downstream logical event IDs",
            ],
            "all_pass": all(
                not row["DATA_INTEGRITY_PRESENT_IN_D04"]
                and not row["G_PRESENT_IN_EXECUTABLE_C"]
                and row["D04_INPUT_FINGERPRINT_CHANGED"]
                and row["D04_SOURCE_FINGERPRINT_CHANGED"]
                and row["TRANSITION_ID_CHANGED"]
                and row["DECISION_ID_CHANGED"]
                and row["NUMERIC_EQUAL"]
                and row["SEMANTIC_EQUAL"]
                for row in provenance_rows
            ),
        },
    )


if __name__ == "__main__":
    main()
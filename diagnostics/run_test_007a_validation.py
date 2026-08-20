from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for path in (
    ROOT / "aptf_runtime" / "src",
    ROOT / "d01_adaptive_parametric_model" / "src",
    ROOT / "d02_return_shape" / "src",
    ROOT / "d04_trading_envelope" / "src",
):
    sys.path.insert(0, str(path))

from aptf_runtime.emitter import AdaptiveEmitter  # noqa: E402
from aptf_runtime.models import EmitterDecision, PositionState  # noqa: E402
from aptf_runtime.observation import Observation  # noqa: E402
from aptf_runtime.position import apply_position_decision  # noqa: E402
from aptf_runtime.runtime import RuntimeCore  # noqa: E402


RULE_FINGERPRINT = "c4c5bbf36ab97b3e7fc4628dfe11708947f996bcd79901a9d19b6a0f2049e9e2"
CODE_FINGERPRINT = "e8b736dfba03b454633831585222d5270c18b7f8eae510b34ee19dc1f5c58410"
EXECUTION_SPECIFIC_FIELDS = {
    "emission_id",
    "lifecycle_start_ns",
    "lifecycle_end_ns",
    "direct_lifecycle_ns",
    "component_lifecycle_ns",
}


def stable_emission(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in EXECUTION_SPECIFIC_FIELDS
    }


def stable_feedback(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in record.items() if key != "source_emission_id"}
        for record in records
    ]


def stable_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def development_observations() -> list[Observation]:
    observations = []
    path = ROOT / "data/market/normalized/SPY_1min_normalized_v0_1.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        for physical_row, row in enumerate(csv.DictReader(handle), start=2):
            if 115 <= physical_row <= 1114:
                observations.append(Observation.from_source_row(physical_row, row))
            if physical_row > 1114:
                break
    if len(observations) != 1000:
        raise RuntimeError("Test 006A development source count changed")
    return observations


def emitter_equivalence(observations: list[Observation]) -> dict[str, Any]:
    oracle_path = ROOT / "APTF_TEST_006A_WALK_FORWARD_EMISSIONS_V0_1.json"
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    expected = oracle["initialization"] + oracle["emissions"]
    emitter = AdaptiveEmitter("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    actual = [emitter.process(observation).as_dict() for observation in observations]
    actionable_pairs = list(zip(actual[15:], expected[15:], strict=True))

    field_matches = {
        name: sum(
            produced["mathematics"][name] == frozen["mathematics"][name]
            for produced, frozen in actionable_pairs
        )
        for name in ("H", "Q_G", "Q_S", "Q_R", "C")
    }
    field_matches.update(
        {
            "position_decision": sum(
                produced["position_decision"] == frozen["position_decision"]
                for produced, frozen in actionable_pairs
            ),
            "state_evolution": sum(
                produced["state_before"] == frozen["state_before"]
                and produced["state_after"] == frozen["state_after"]
                for produced, frozen in actionable_pairs
            ),
            "context_identity": sum(
                produced["prior_context_ids"] == frozen["prior_context_ids"]
                for produced, frozen in actionable_pairs
            ),
            "emission_ordering": sum(
                produced["observation_index"] == frozen["observation_index"]
                and produced["physical_row"] == frozen["physical_row"]
                for produced, frozen in actionable_pairs
            ),
        }
    )
    deterministic_matches = sum(
        stable_emission(produced) == stable_emission(frozen)
        for produced, frozen in zip(actual, expected, strict=True)
    )
    feedback_match = stable_feedback(emitter.feedback_audit) == stable_feedback(
        oracle["feedback_audit"]
    )
    adaptation_match = emitter.adaptation_audit == oracle["adaptation_audit"]
    decision_counts = Counter(item["position_decision"] for item in actual[15:])
    passed = (
        deterministic_matches == 1000
        and all(value == 985 for value in field_matches.values())
        and feedback_match
        and adaptation_match
        and decision_counts == {"BUY": 131, "SELL": 102, "HOLD": 752}
    )
    return {
        "test_id": "APTF_TEST_007A_EMITTER_EQUIVALENCE_V0_1",
        "oracle": "APTF_TEST_006A_WALK_FORWARD_EMISSIONS_V0_1.json",
        "oracle_sha256": hashlib.sha256(oracle_path.read_bytes()).hexdigest(),
        "development_physical_rows": [115, 1114],
        "total_observations": 1000,
        "initialization": 15,
        "actionable_expected": 985,
        "actionable_compared": 985,
        "field_matches": field_matches,
        "deterministic_record_matches": deterministic_matches,
        "feedback_records_expected": len(oracle["feedback_audit"]),
        "feedback_records_actual": len(emitter.feedback_audit),
        "feedback_match": feedback_match,
        "adaptation_records_expected": len(oracle["adaptation_audit"]),
        "adaptation_records_actual": len(emitter.adaptation_audit),
        "adaptation_match": adaptation_match,
        "decision_counts": dict(decision_counts),
        "numeric_tolerance": 0.0,
        "excluded_execution_specific_fields": sorted(EXECUTION_SPECIFIC_FIELDS),
        "difference_classification": (
            "PROCESSING_TELEMETRY_AND_TELEMETRY_DERIVED_EMISSION_ID_ONLY"
        ),
        "reserve_emitter_rerun": False,
        "status": "PASS" if passed else "FAIL",
    }


def position_equivalence() -> dict[str, Any]:
    oracle_path = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
    counts: Counter[str] = Counter()
    state_after_matches = 0
    classification_matches = 0
    actionable = 0
    with oracle_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["position_decision"] == "INITIALIZING":
                continue
            transition = apply_position_decision(
                PositionState(row["test007_position_state_before"]),
                EmitterDecision(row["position_decision"]),
            )
            actionable += 1
            state_after_matches += (
                transition.state_after.value == row["test007_position_state_after"]
            )
            classification_matches += (
                transition.structural_classification
                == row["test007_structural_classification"]
            )
            counts[transition.structural_classification] += 1
    expected_counts = {
        "EPISODE_OPEN": 2051,
        "REPEATED_BUY_WHILE_LONG": 12198,
        "EPISODE_CLOSE": 2051,
        "UNMATCHED_SELL_WHILE_FLAT": 7728,
        "EPISODE_HOLD": 39787,
        "FLAT_HOLD": 37391,
    }
    truth_table = [
        (PositionState.FLAT, EmitterDecision.BUY, PositionState.LONG, "BUY"),
        (PositionState.FLAT, EmitterDecision.HOLD, PositionState.FLAT, "NONE"),
        (PositionState.FLAT, EmitterDecision.SELL, PositionState.FLAT, "NONE"),
        (PositionState.LONG, EmitterDecision.BUY, PositionState.LONG, "NONE"),
        (PositionState.LONG, EmitterDecision.HOLD, PositionState.LONG, "NONE"),
        (PositionState.LONG, EmitterDecision.SELL, PositionState.FLAT, "SELL"),
    ]
    truth_matches = sum(
        apply_position_decision(state, decision).state_after is after
        and apply_position_decision(state, decision).execution_intent.value == intent
        for state, decision, after, intent in truth_table
    )
    passed = (
        actionable == state_after_matches == classification_matches == 101206
        and dict(counts) == expected_counts
        and truth_matches == 6
    )
    return {
        "test_id": "APTF_TEST_007A_POSITION_EQUIVALENCE_V0_1",
        "oracle": "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv",
        "oracle_sha256": hashlib.sha256(oracle_path.read_bytes()).hexdigest(),
        "actionable_expected": 101206,
        "actionable_compared": actionable,
        "state_after_matches": state_after_matches,
        "classification_matches": classification_matches,
        "structural_counts": dict(counts),
        "truth_table_matches": truth_matches,
        "truth_table_expected": 6,
        "reserve_emitter_rerun": False,
        "status": "PASS" if passed else "FAIL",
    }


def determinism(observations: list[Observation]) -> dict[str, Any]:
    left = RuntimeCore("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    right = RuntimeCore("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    left_results = [left.process(observation) for observation in observations]
    right_results = [right.process(observation) for observation in observations]
    left_emissions = [stable_emission(item.emission.as_dict()) for item in left_results]
    right_emissions = [stable_emission(item.emission.as_dict()) for item in right_results]
    left_transitions = [
        None
        if item.position_transition is None
        else {
            "state_before": item.position_transition.state_before.value,
            "decision": item.position_transition.emitter_decision.value,
            "state_after": item.position_transition.state_after.value,
            "classification": item.position_transition.structural_classification,
            "intent": item.position_transition.execution_intent.value,
        }
        for item in left_results
    ]
    right_transitions = [
        None
        if item.position_transition is None
        else {
            "state_before": item.position_transition.state_before.value,
            "decision": item.position_transition.emitter_decision.value,
            "state_after": item.position_transition.state_after.value,
            "classification": item.position_transition.structural_classification,
            "intent": item.position_transition.execution_intent.value,
        }
        for item in right_results
    ]
    passed = left_emissions == right_emissions and left_transitions == right_transitions
    return {
        "test_id": "APTF_TEST_007A_DETERMINISM_V0_1",
        "replays": 2,
        "observations_per_replay": 1000,
        "deterministic_emission_sha256_left": stable_sha256(left_emissions),
        "deterministic_emission_sha256_right": stable_sha256(right_emissions),
        "position_transition_sha256_left": stable_sha256(left_transitions),
        "position_transition_sha256_right": stable_sha256(right_transitions),
        "emissions_identical": left_emissions == right_emissions,
        "position_transitions_identical": left_transitions == right_transitions,
        "final_position_state_identical": left.position_state == right.position_state,
        "context_identity_identical": (
            left.emitter.context.observation_ids == right.emitter.context.observation_ids
        ),
        "excluded_execution_specific_fields": sorted(EXECUTION_SPECIFIC_FIELDS),
        "status": "PASS" if passed else "FAIL",
    }


def write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    observations = development_observations()
    emitter = emitter_equivalence(observations)
    position = position_equivalence()
    replay = determinism(observations)
    write(ROOT / "APTF_TEST_007A_EMITTER_EQUIVALENCE_V0_1.json", emitter)
    write(ROOT / "APTF_TEST_007A_POSITION_EQUIVALENCE_V0_1.json", position)
    write(ROOT / "APTF_TEST_007A_DETERMINISM_V0_1.json", replay)
    print(json.dumps({
        "emitter": emitter["status"],
        "emitter_actionable": emitter["actionable_compared"],
        "position": position["status"],
        "position_actionable": position["actionable_compared"],
        "truth_table": position["truth_table_matches"],
        "determinism": replay["status"],
        "reserve_emitter_rerun": False,
    }, indent=2, sort_keys=True))
    return 0 if all(item["status"] == "PASS" for item in (emitter, position, replay)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
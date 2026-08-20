from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from aptf_runtime.emitter import AdaptiveEmitter
from aptf_runtime.models import EmitterDecision, PositionState
from aptf_runtime.observation import Observation
from aptf_runtime.position import apply_position_decision
from aptf_runtime.runtime import RuntimeCore


ROOT = Path(__file__).resolve().parents[2]
RULE_FINGERPRINT = "c4c5bbf36ab97b3e7fc4628dfe11708947f996bcd79901a9d19b6a0f2049e9e2"
CODE_FINGERPRINT = "e8b736dfba03b454633831585222d5270c18b7f8eae510b34ee19dc1f5c58410"
EXECUTION_SPECIFIC_FIELDS = {
    "emission_id",
    "lifecycle_start_ns",
    "lifecycle_end_ns",
    "direct_lifecycle_ns",
    "component_lifecycle_ns",
}


def development_observations() -> list[Observation]:
    observations = []
    path = ROOT / "data/market/normalized/SPY_1min_normalized_v0_1.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        for physical_row, row in enumerate(csv.DictReader(handle), start=2):
            if 115 <= physical_row <= 1114:
                observations.append(Observation.from_source_row(physical_row, row))
            if physical_row > 1114:
                break
    assert len(observations) == 1000
    return observations


def oracle_records() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = ROOT / "APTF_TEST_006A_WALK_FORWARD_EMISSIONS_V0_1.json"
    oracle = json.loads(path.read_text(encoding="utf-8"))
    return oracle, oracle["initialization"] + oracle["emissions"]


def deterministic_emission(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in EXECUTION_SPECIFIC_FIELDS
    }


def deterministic_feedback(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in record.items() if key != "source_emission_id"}
        for record in records
    ]


def test_test006a_emitter_equivalence_985_of_985() -> None:
    oracle, expected = oracle_records()
    emitter = AdaptiveEmitter("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    actual = [emitter.process(observation).as_dict() for observation in development_observations()]

    assert len(actual) == len(expected) == 1000
    assert sum(item["status"] == "INITIALIZING" for item in actual) == 15
    assert sum(item["status"] == "ACTIONABLE" for item in actual) == 985
    for produced, frozen in zip(actual, expected, strict=True):
        assert deterministic_emission(produced) == deterministic_emission(frozen)
    assert emitter.adaptation_audit == oracle["adaptation_audit"]
    assert deterministic_feedback(emitter.feedback_audit) == deterministic_feedback(
        oracle["feedback_audit"]
    )
    assert Counter(item["position_decision"] for item in actual[15:]) == {
        "BUY": 131,
        "SELL": 102,
        "HOLD": 752,
    }


def test_initialization_context_rollover_feedback_and_no_future_access() -> None:
    observations = development_observations()[:45]
    emitter = AdaptiveEmitter("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    records = [emitter.process(observation).as_dict() for observation in observations]

    assert all(record["status"] == "INITIALIZING" for record in records[:15])
    assert all(record["position_decision"] is None for record in records[:15])
    assert records[15]["prior_context_ids"] == [record["observation_id"] for record in records[:15]]
    assert records[16]["prior_context_ids"] == [record["observation_id"] for record in records[1:16]]
    assert records[29]["prior_context_ids"] == [record["observation_id"] for record in records[14:29]]
    assert records[44]["prior_context_ids"] == [record["observation_id"] for record in records[29:44]]
    assert all(record["observation_id"] not in record["prior_context_ids"] for record in records)
    assert all(record["future_access_count"] == 0 for record in records)
    assert all(item["effective_observation"] > 16 for item in emitter.feedback_audit[:2])


def test_test007_position_equivalence_101206_of_101206() -> None:
    path = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
    matches = 0
    counts: Counter[str] = Counter()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["position_decision"] == "INITIALIZING":
                continue
            transition = apply_position_decision(
                PositionState(row["test007_position_state_before"]),
                EmitterDecision(row["position_decision"]),
            )
            assert transition.state_after.value == row["test007_position_state_after"]
            assert transition.structural_classification == row["test007_structural_classification"]
            counts[transition.structural_classification] += 1
            matches += 1
    assert matches == 101206
    assert counts == {
        "EPISODE_OPEN": 2051,
        "REPEATED_BUY_WHILE_LONG": 12198,
        "EPISODE_CLOSE": 2051,
        "UNMATCHED_SELL_WHILE_FLAT": 7728,
        "EPISODE_HOLD": 39787,
        "FLAT_HOLD": 37391,
    }


def test_deterministic_replay_and_isolated_runtime_instances() -> None:
    observations = development_observations()
    left = RuntimeCore("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    right = RuntimeCore("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    left_results = [left.process(observation) for observation in observations]
    right_results = [right.process(observation) for observation in observations]

    assert [deterministic_emission(item.emission.as_dict()) for item in left_results] == [
        deterministic_emission(item.emission.as_dict()) for item in right_results
    ]
    assert [item.position_transition for item in left_results] == [
        item.position_transition for item in right_results
    ]
    assert [item.execution_intent for item in left_results] == [
        item.execution_intent for item in right_results
    ]
    assert left.position_state == right.position_state
    assert left.emitter.context.observation_ids == right.emitter.context.observation_ids

    untouched = RuntimeCore("SPY", RULE_FINGERPRINT, CODE_FINGERPRINT)
    assert untouched.position_state is PositionState.FLAT
    assert untouched.emitter.state.completed_count == 0
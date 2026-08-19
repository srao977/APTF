from __future__ import annotations

import importlib.util
from itertools import product
import os
from pathlib import Path
import subprocess
import sys

import pytest
from pydantic import ValidationError

from aptf_d04.models.envelope_state import EnvelopeEvaluation
from d03.v01 import DecisionContext, DecisionRecord, D03Input, InvalidD03InputError, evaluate_decision


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "design_validation" / "validate_d03_design_v01.py"
SPEC = importlib.util.spec_from_file_location("frozen_d03_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
FROZEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FROZEN)


def _current_d04_payload(state: dict) -> dict:
    payload = FROZEN.d04_payload(state)
    payload.pop("feasibility_gate_score", None)
    payload.pop("gate_dimension_values", None)
    return payload


def _state_space():
    names = (
        "actual",
        "candidate",
        "envelope",
        "system_enabled",
        "trading_enabled",
        "emergency",
        "execution_available",
        "safety_closed",
        "pending",
    )
    values = product(
        FROZEN.POSITIONS,
        FROZEN.CANDIDATES,
        FROZEN.ENVELOPES,
        (False, True),
        (False, True),
        (False, True),
        (False, True),
        (False, True),
        FROZEN.PENDING,
    )
    for combination in values:
        yield dict(zip(names, combination))


def _actual_decision(state: dict) -> dict:
    input_value = D03Input(
        d04_evaluation=EnvelopeEvaluation.model_validate(_current_d04_payload(state)),
        decision_context=DecisionContext.model_validate(FROZEN.context_payload(state)),
    )
    return evaluate_decision(input_value).model_dump(mode="json")


def test_complete_frozen_policy_space_matches_all_semantic_fields() -> None:
    mismatches: list[tuple[dict, dict, dict]] = []
    identity_fields = {"decision_id", "source_d04_fingerprint", "input_fingerprint"}
    count = 0
    for state in _state_space():
        count += 1
        expected, _ = FROZEN.decision_for(state)
        actual = _actual_decision(state)
        expected_semantic = {key: value for key, value in expected.items() if key not in identity_fields}
        actual_semantic = {key: value for key, value in actual.items() if key not in identity_fields}
        if actual_semantic != expected_semantic and len(mismatches) < 3:
            mismatches.append((state, expected, actual))

    assert count == 7680
    assert not mismatches, mismatches


def test_all_frozen_invalid_classes_reject_before_commitment() -> None:
    state = {
        "actual": "FLAT",
        "candidate": "ABSENT",
        "envelope": "CLOSED",
        "system_enabled": True,
        "trading_enabled": True,
        "emergency": False,
        "execution_available": True,
        "safety_closed": False,
        "pending": "NONE",
    }
    d04_payload = _current_d04_payload(state)
    valid = FROZEN.context_payload(state)
    invalid_cases = [
        {key: value for key, value in valid.items() if key != "context_time"},
        valid | {"extra": 1},
        valid | {"actual_position_state": "UNKNOWN"},
        valid | {"pending_target_state": "UNKNOWN"},
        valid | {"position_candidate_id": "X"},
        valid | {"actual_position_state": "LONG"},
        valid | {"pending_decision_id": "X"},
        valid | {"pending_target_state": "LONG"},
        valid | {"control_state_valid": False},
        valid | {"context_time": 99.0},
        valid | {"entity_id": "OTHER"},
    ]

    rejected = 0
    for context_payload in invalid_cases:
        try:
            input_value = D03Input(
                d04_evaluation=EnvelopeEvaluation.model_validate(d04_payload),
                decision_context=DecisionContext.model_validate(context_payload),
            )
            evaluate_decision(input_value)
        except (InvalidD03InputError, ValidationError):
            rejected += 1

    assert len(invalid_cases) == 11
    assert rejected == 11


def test_exhaustive_repeatability_is_bit_stable() -> None:
    nondeterministic = 0
    for state in _state_space():
        first = _actual_decision(state)
        second = _actual_decision(state)
        if first != second:
            nondeterministic += 1
    assert nondeterministic == 0


def test_feed_replay_transport_labels_are_external_to_d03() -> None:
    def invoke(_transport: str, state: dict) -> dict:
        return _actual_decision(state)

    assert all(invoke("FEED", state) == invoke("REPLAY", state) for state in _state_space())


def test_contract_field_counts_match_frozen_schemas() -> None:
    input_schema = FROZEN.load(ROOT / "D03_INPUT_SCHEMA_V0_1.json")
    output_schema = FROZEN.load(ROOT / "D03_DECISION_SCHEMA_V0_1.json")
    expected_context = [field["canonical_name"] for field in input_schema["decision_context"]["fields"]]
    expected_output = [field["canonical_name"] for field in output_schema["fields"]]

    assert len(EnvelopeEvaluation.model_fields) == 21
    assert len(DecisionContext.model_fields) == 12
    assert list(DecisionContext.model_fields) == expected_context
    assert len(DecisionRecord.model_fields) == 21
    assert list(DecisionRecord.model_fields) == expected_output


def test_fresh_process_output_digest_is_hash_seed_independent() -> None:
    script = Path(__file__).with_name("fresh_process_digest.py")
    digests = []
    for seed in ("1", "777"):
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = seed
        result = subprocess.run(
            [sys.executable, str(script)],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        digests.append(result.stdout.strip())
    assert digests[0] == digests[1]

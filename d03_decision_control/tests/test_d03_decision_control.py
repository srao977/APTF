from __future__ import annotations

import pytest
from pydantic import ValidationError

from aptf_d04.models.enums import CandidateStatus, EnvelopeState, SafetyState
from aptf_d04.models.opportunity import CandidateEnvelope
from aptf_d04.models.envelope_state import EnvelopeEvaluation
from d03.v01 import DecisionContext, D03Input, InvalidD03InputError, evaluate_decision


def make_evaluation(*, entity_id: str = "ENTITY", evaluation_time: float = 100.0, envelope_state: EnvelopeState = EnvelopeState.OPEN, safety_state: SafetyState = SafetyState.CLEAR, candidate: CandidateEnvelope | None = None, projection_valid: bool = True, stale: bool = False) -> EnvelopeEvaluation:
    return EnvelopeEvaluation(
        evaluation_time=evaluation_time,
        entity_id=entity_id,
        return_shape_model_time=90.0,
        source_model_version="0.2",
        hard_eligibility=1,
        geometry_quality=1.0,
        structural_quality=1.0,
        risk_quality=1.0,
        base_capturability_score=1.0,
        capturability_score=1.0,
        previous_envelope_state=envelope_state,
        new_envelope_state=envelope_state,
        aperture_before=0.5,
        aperture_after=0.5,
        projection_valid=projection_valid,
        stale=stale,
        safety_state=safety_state,
        safety_reason=None,
        candidate_envelope=candidate,
        reason_codes=[],
        events=[],
    )


def make_candidate(*, direction: str, candidate_id: str = "CANDIDATE-1") -> CandidateEnvelope:
    return CandidateEnvelope(
        candidate_id=candidate_id,
        entity_id="ENTITY",
        source_return_shape_model_time=90.0,
        qualified_at=95.0,
        status=CandidateStatus.QUALIFIED,
        path_direction=direction,
    )


def make_context(*, actual_position_state: str = "FLAT", system_enabled: bool = True, trading_enabled: bool = True, execution_available: bool = True, emergency_flatten: bool = False, pending_target_state: str = "NONE", control_state_valid: bool = True) -> DecisionContext:
    return DecisionContext(
        context_time=100.0,
        entity_id="ENTITY",
        actual_position_state=actual_position_state,
        position_candidate_id=None if actual_position_state == "FLAT" else "POSITION-1",
        position_source_return_shape_model_time=None if actual_position_state == "FLAT" else 80.0,
        pending_target_state=pending_target_state,
        pending_decision_id=None if pending_target_state == "NONE" else "PENDING-1",
        execution_available=execution_available,
        system_enabled=system_enabled,
        trading_enabled=trading_enabled,
        emergency_flatten=emergency_flatten,
        control_state_valid=control_state_valid,
    )


def test_emergency_flatten_overrides_direction() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD")),
            decision_context=make_context(actual_position_state="LONG", emergency_flatten=True),
        )
    )
    assert decision.desired_position_state == "FLAT"
    assert decision.transition_intent == "CLOSE"
    assert decision.primary_reason_code == "EMERGENCY_FLATTEN"
    assert decision.candidate_id is None


def test_disabled_control_preserves_position() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD")),
            decision_context=make_context(actual_position_state="LONG", system_enabled=False),
        )
    )
    assert decision.desired_position_state == "LONG"
    assert decision.transition_intent == "NO_CHANGE"
    assert decision.primary_reason_code == "SYSTEM_DISABLED"
    assert decision.candidate_id is None


def test_upward_candidate_maps_to_long() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD")),
            decision_context=make_context(actual_position_state="FLAT"),
        )
    )
    assert decision.desired_position_state == "LONG"
    assert decision.transition_intent == "OPEN"
    assert decision.candidate_id == "CANDIDATE-1"
    assert decision.decision_rule_id.startswith("TARGET:R40|TRANSITION:T21|")


def test_blocked_if_execution_unavailable() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="DOWNWARD")),
            decision_context=make_context(actual_position_state="FLAT", execution_available=False),
        )
    )
    assert decision.transition_intent == "BLOCKED"
    assert decision.action_authorized is False
    assert decision.primary_reason_code == "CANDIDATE_QUALIFIED"


def test_invalid_input_rejected_before_commitment() -> None:
    with pytest.raises(InvalidD03InputError):
        evaluate_decision(
            D03Input(
                d04_evaluation=make_evaluation(),
                decision_context=make_context(control_state_valid=False),
            )
        )


def test_t00_retarget_requires_pending_conflict() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD")),
            decision_context=make_context(actual_position_state="LONG", pending_target_state="SHORT"),
        )
    )
    assert decision.transition_intent == "RETARGET"
    assert decision.decision_rule_id.startswith("TARGET:R40|TRANSITION:T00|")


def test_repeated_identical_input_is_stable() -> None:
    input_value = D03Input(
        d04_evaluation=make_evaluation(candidate=make_candidate(direction="DOWNWARD")),
        decision_context=make_context(actual_position_state="FLAT"),
    )
    first = evaluate_decision(input_value)
    second = evaluate_decision(input_value)
    assert first.model_dump() == second.model_dump()


@pytest.mark.parametrize(
    ("actual", "desired_direction", "expected"),
    [
        ("FLAT", "FLAT", "NO_CHANGE"),
        ("FLAT", "UPWARD", "OPEN"),
        ("FLAT", "DOWNWARD", "OPEN"),
        ("LONG", "FLAT", "CLOSE"),
        ("LONG", "UPWARD", "NO_CHANGE"),
        ("LONG", "DOWNWARD", "REVERSE"),
        ("SHORT", "FLAT", "CLOSE"),
        ("SHORT", "UPWARD", "REVERSE"),
        ("SHORT", "DOWNWARD", "NO_CHANGE"),
    ],
)
def test_complete_transition_matrix(actual: str, desired_direction: str, expected: str) -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction=desired_direction)),
            decision_context=make_context(actual_position_state=actual),
        )
    )
    assert decision.transition_intent == expected


@pytest.mark.parametrize("actual", ["FLAT", "LONG", "SHORT"])
@pytest.mark.parametrize(("system_enabled", "trading_enabled"), [(False, True), (True, False), (False, False)])
def test_disabled_control_preserves_each_actual_state(
    actual: str,
    system_enabled: bool,
    trading_enabled: bool,
) -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="DOWNWARD")),
            decision_context=make_context(
                actual_position_state=actual,
                system_enabled=system_enabled,
                trading_enabled=trading_enabled,
            ),
        )
    )
    assert decision.desired_position_state == actual
    assert decision.transition_intent == "NO_CHANGE"
    assert decision.candidate_id is None
    assert "|TRANSITION:NONE|" in decision.decision_rule_id


@pytest.mark.parametrize(
    ("actual", "expected"),
    [("FLAT", "NO_CHANGE"), ("LONG", "CLOSE"), ("SHORT", "CLOSE")],
)
def test_emergency_flatten_precedence(actual: str, expected: str) -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD")),
            decision_context=make_context(
                actual_position_state=actual,
                system_enabled=False,
                trading_enabled=False,
                emergency_flatten=True,
            ),
        )
    )
    assert decision.desired_position_state == "FLAT"
    assert decision.transition_intent == expected
    assert decision.primary_reason_code == "EMERGENCY_FLATTEN"
    assert decision.candidate_id is None


def test_reenable_uses_only_current_candidate() -> None:
    disabled = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD", candidate_id="A")),
            decision_context=make_context(system_enabled=False),
        )
    )
    enabled = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="DOWNWARD", candidate_id="B")),
            decision_context=make_context(system_enabled=True),
        )
    )
    assert disabled.candidate_id is None
    assert enabled.candidate_id == "B"
    assert enabled.desired_position_state == "SHORT"


@pytest.mark.parametrize(
    ("pending", "direction", "expected_rule"),
    [("NONE", "UPWARD", "T21"), ("LONG", "UPWARD", "T10"), ("SHORT", "UPWARD", "T00")],
)
def test_t00_and_pending_boundaries(pending: str, direction: str, expected_rule: str) -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction=direction)),
            decision_context=make_context(pending_target_state=pending),
        )
    )
    assert f"|TRANSITION:{expected_rule}|" in decision.decision_rule_id


def test_qualified_flat_preserves_current_candidate_lineage() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="FLAT")),
            decision_context=make_context(),
        )
    )
    assert decision.desired_position_state == "FLAT"
    assert decision.candidate_id == "CANDIDATE-1"


def test_committed_record_is_immutable() -> None:
    decision = evaluate_decision(
        D03Input(
            d04_evaluation=make_evaluation(candidate=make_candidate(direction="UPWARD")),
            decision_context=make_context(),
        )
    )
    with pytest.raises(ValidationError):
        decision.desired_position_state = "SHORT"

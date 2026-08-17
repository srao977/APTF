from pathlib import Path

import pytest
from pydantic import ValidationError

from aptf_d04.cli.main import build_envelope
from aptf_d04.envelope.trading_envelope import candidate_identity
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator
from aptf_d04.models.enums import CandidateStatus, EnvelopeState, EventType, SafetyReason
from d02.v02.models import PathDirection


ROOT = Path(__file__).resolve().parents[1]


def _observation(index: int = 1):
    scenario = load_scenario(ROOT / "scenarios" / "02_shape_becomes_capturable.yaml")
    return SyntheticGenerator(scenario).generate()[index]


def _shape(direction: PathDirection, model_time: float):
    terminal = {
        PathDirection.UPWARD: 1.0,
        PathDirection.DOWNWARD: -1.0,
        PathDirection.FLAT: 0.0,
    }[direction]
    maximum = 0.0 if direction == PathDirection.FLAT else 1.0
    values = {
        "terminal_displacement": terminal,
        "maximum_absolute_displacement": maximum,
        "strength": 0.98,
        "coherence": 0.98,
        "persistence": 0.98,
        "uncertainty": 0.02,
        "reversal_propensity": 0.02,
        "state_support_ratio": 2.0,
    }
    return SyntheticGenerator._return_shape("DIRECTION", model_time, values)


def _open_envelope(shape, evaluation_time: float | None = None):
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = _observation()
    envelope.current_state = EnvelopeState.OPEN
    context = item.context.model_copy(
        update={"evaluation_time": shape.model_time if evaluation_time is None else evaluation_time}
    )
    result = envelope.process(shape, context)
    assert result.candidate_envelope is not None
    return envelope, context, result


def test_candidate_creation_preserves_source_path_direction() -> None:
    shape = _shape(PathDirection.DOWNWARD, 10.0)
    _, _, result = _open_envelope(shape)
    assert result.candidate_envelope.path_direction is shape.path_direction


def test_candidate_reevaluation_preserves_path_direction() -> None:
    shape = _shape(PathDirection.UPWARD, 10.0)
    envelope, context, first = _open_envelope(shape)
    second = envelope.process(shape, context.model_copy(update={"spread_quality": 0.8}))
    assert second.candidate_envelope.path_direction == first.candidate_envelope.path_direction
    assert second.candidate_envelope.candidate_id == first.candidate_envelope.candidate_id


def test_candidate_path_direction_is_immutable() -> None:
    shape = _shape(PathDirection.UPWARD, 10.0)
    _, _, result = _open_envelope(shape)
    with pytest.raises(ValidationError):
        result.candidate_envelope.path_direction = PathDirection.DOWNWARD


def test_superseding_candidate_receives_new_shape_direction() -> None:
    first_shape = _shape(PathDirection.UPWARD, 10.0)
    envelope, context, _ = _open_envelope(first_shape)
    next_shape = _shape(PathDirection.DOWNWARD, 11.0)
    result = envelope.process(next_shape, context.model_copy(update={"evaluation_time": 11.0}))
    assert EventType.SHAPE_SUPERSEDED in result.events
    assert result.candidate_envelope.path_direction == PathDirection.DOWNWARD


def test_old_candidate_direction_does_not_leak_on_supersession() -> None:
    first_shape = _shape(PathDirection.DOWNWARD, 10.0)
    envelope, context, first = _open_envelope(first_shape)
    next_shape = _shape(PathDirection.UPWARD, 11.0)
    second = envelope.process(next_shape, context.model_copy(update={"evaluation_time": 11.0}))
    assert first.candidate_envelope.path_direction == PathDirection.DOWNWARD
    assert second.candidate_envelope.path_direction == PathDirection.UPWARD


def test_candidate_serialization_preserves_enum_value() -> None:
    shape = _shape(PathDirection.DOWNWARD, 10.0)
    _, _, result = _open_envelope(shape)
    payload = result.candidate_envelope.model_dump(mode="json")
    assert payload["path_direction"] == "DOWNWARD"
    assert len(payload) == 6


def test_stale_invalidation_preserves_existing_direction() -> None:
    shape = _shape(PathDirection.UPWARD, 10.0)
    envelope, context, _ = _open_envelope(shape)
    stale_time = shape.model_time + shape.projection_interval + 0.001
    result = envelope.process(shape, context.model_copy(update={"evaluation_time": stale_time}))
    assert result.safety_reason == SafetyReason.SHAPE_STALE
    assert result.candidate_envelope.status == CandidateStatus.INVALIDATED
    assert result.candidate_envelope.path_direction == PathDirection.UPWARD


def test_direction_propagation_does_not_change_formulas() -> None:
    upward = _shape(PathDirection.UPWARD, 10.0)
    downward = _shape(PathDirection.DOWNWARD, 10.0)
    envelope_up, context, _ = _open_envelope(upward)
    envelope_down, _ = build_envelope(ROOT / "config" / "default.yaml")
    up = envelope_up.capturability_model.evaluate(upward, context)
    down = envelope_down.capturability_model.evaluate(downward, context)
    assert up.model_dump() == down.model_dump()


def test_candidate_identity_is_direction_independent_and_unchanged() -> None:
    upward = _shape(PathDirection.UPWARD, 10.0)
    downward = _shape(PathDirection.DOWNWARD, 10.0)
    _, _, up = _open_envelope(upward)
    _, _, down = _open_envelope(downward)
    expected = candidate_identity("DIRECTION", 10.0, 10.0)
    assert up.candidate_envelope.candidate_id == expected
    assert down.candidate_envelope.candidate_id == expected


def test_identical_input_produces_identical_candidate_direction() -> None:
    shape = _shape(PathDirection.UPWARD, 10.0)
    first = _open_envelope(shape)[2].candidate_envelope.model_dump(mode="json")
    second = _open_envelope(shape)[2].candidate_envelope.model_dump(mode="json")
    assert first == second
    assert first["path_direction"] == "UPWARD"

from dataclasses import fields, replace
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from aptf_d04.cli.main import build_envelope
from aptf_d04.envelope.capturability_model import CapturabilityModelV0_2, InvalidReturnShapeError
from aptf_d04.envelope.trading_envelope import candidate_identity
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator
from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.envelope_state import EnvelopeEvaluation
from aptf_d04.models.enums import CandidateStatus, EnvelopeState, EventType, SafetyReason, SafetyState
from aptf_d04.models.opportunity import CandidateEnvelope
from d01.v02.outputs import DMOOutput, FMOSample, FMOOutput
from d02.v02 import build_return_shape
from d02.v02.models import PathDirection, ReturnShape


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FIELDS = {
    "evaluation_time", "market_eligible",
}
OUTPUT_FIELDS = {
    "evaluation_time", "entity_id", "return_shape_model_time", "source_model_version",
    "hard_eligibility", "geometry_quality", "structural_quality", "risk_quality",
    "base_capturability_score", "capturability_score",
    "previous_envelope_state", "new_envelope_state", "aperture_before", "aperture_after",
    "projection_valid", "stale", "safety_state", "safety_reason", "candidate_envelope",
    "reason_codes", "events",
}
CANDIDATE_FIELDS = {
    "candidate_id", "entity_id", "source_return_shape_model_time", "qualified_at", "status",
    "path_direction",
}
PROHIBITED_OUTPUT_FIELDS = {
    "buy", "sell", "hold", "enter", "exit", "reduce", "reverse", "position_open",
    "order_state", "position_sizing", "candidate_reward", "candidate_risk",
    "trade_recommendation",
}


def observation(name: str = "02_shape_becomes_capturable", index: int = 1):
    scenario = load_scenario(ROOT / "scenarios" / f"{name}.yaml")
    return SyntheticGenerator(scenario).generate()[index]


def model_and_observation():
    envelope, config = build_envelope(ROOT / "config" / "default.yaml")
    return envelope.capturability_model, observation(), config


def test_context_schema_has_two_current_values_plus_provenance_control() -> None:
    assert set(EnvelopeContext.model_fields) == CONTEXT_FIELDS | {
        "context_role", "provenance"
    }
    assert len(CONTEXT_FIELDS) == 2


def test_output_schema_removes_two_gate_fields() -> None:
    assert set(EnvelopeEvaluation.model_fields) == OUTPUT_FIELDS
    assert len(EnvelopeEvaluation.model_fields) == 21


def test_candidate_schema_is_exactly_amended_6_fields() -> None:
    assert set(CandidateEnvelope.model_fields) == CANDIDATE_FIELDS
    assert len(CandidateEnvelope.model_fields) == 6


def test_context_forbids_untyped_metadata() -> None:
    payload = observation().context.model_dump()
    payload["metadata"] = {}
    with pytest.raises(ValidationError):
        EnvelopeContext(**payload)


def test_candidate_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CandidateEnvelope(
            candidate_id="id", entity_id="entity", source_return_shape_model_time=1.0,
            qualified_at=2.0, status=CandidateStatus.QUALIFIED,
            path_direction=PathDirection.UPWARD, recommendation="BUY",
        )


@pytest.mark.parametrize(
    ("entity_id", "model_time", "qualified_at", "expected"),
    [
        ("ABC", 1.0, 2.0, "D04C|ABC|1|2"),
        ("A B/C", 0.1, 0.2, "D04C|A%20B%2FC|0.10000000000000001|0.20000000000000001"),
        ("x|y", -0.0, 10.5, "D04C|x%7Cy|-0|10.5"),
        ("alpha-beta_1.2~z", 1.25, 1.5, "D04C|alpha-beta_1.2~z|1.25|1.5"),
    ],
)
def test_candidate_identity_rule(entity_id, model_time, qualified_at, expected) -> None:
    assert candidate_identity(entity_id, model_time, qualified_at) == expected


def test_zero_maximum_displacement_forces_zero_geometry() -> None:
    model, item, _ = model_and_observation()
    shape, _ = _frozen_vector_input(
        {"inputs": {"terminal_displacement": 0.0, "maximum_absolute_displacement": 0.0}}
    )
    result = model.evaluate(shape, item.context)
    assert result.geometry_quality == 0.0
    assert result.base_capturability_score == 0.0


def test_geometry_uses_terminal_to_maximum_ratio() -> None:
    model, item, _ = model_and_observation()
    shape, _ = _frozen_vector_input(
        {"inputs": {"terminal_displacement": -0.25, "maximum_absolute_displacement": 1.0}}
    )
    assert model.evaluate(shape, item.context).geometry_quality == 0.25


@pytest.mark.parametrize(
    ("strength", "coherence", "persistence", "expected"),
    [(1.0, 1.0, 1.0, 1.0), (0.0, 1.0, 1.0, 0.0), (0.125, 0.125, 0.125, 0.125)],
)
def test_structural_quality_geometric_mean(strength, coherence, persistence, expected) -> None:
    model, item, _ = model_and_observation()
    shape = replace(item.return_shape, strength=strength, coherence=coherence, persistence=persistence)
    assert model.evaluate(shape, item.context).structural_quality == pytest.approx(expected)


@pytest.mark.parametrize(
    ("uncertainty", "reversal", "expected"),
    [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.75, 0.0, 0.5)],
)
def test_risk_quality_complement_product(uncertainty, reversal, expected) -> None:
    model, item, _ = model_and_observation()
    shape = replace(item.return_shape, uncertainty=uncertainty, reversal_propensity=reversal)
    assert model.evaluate(shape, item.context).risk_quality == pytest.approx(expected)


@pytest.mark.parametrize(
    ("updates", "time_offset", "expected_reason"),
    [
        ({"market_eligible": False}, 0.0, "MARKET_INELIGIBLE"),
        ({}, 31.0, "SHAPE_STALE"),
    ],
)
def test_hard_eligibility_failure_branches(updates, time_offset, expected_reason) -> None:
    model, item, _ = model_and_observation()
    context = item.context.model_copy(
        update={**updates, "evaluation_time": item.return_shape.model_time + time_offset}
    )
    result = model.evaluate(item.return_shape, context)
    assert result.hard_eligibility == 0
    assert result.capturability_score == 0.0
    assert expected_reason in result.reason_codes


def test_current_equation_emits_no_gate_fields() -> None:
    model, item, _ = model_and_observation()
    result = model.evaluate(item.return_shape, item.context)
    assert "feasibility_gate_score" not in result.model_dump()
    assert "gate_dimension_values" not in result.model_dump()


@pytest.mark.parametrize("prior_state", list(EnvelopeState))
def test_stale_forces_immediate_closed_from_every_state(prior_state: EnvelopeState) -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    envelope.current_state = prior_state
    envelope.current_aperture = 0.8
    envelope.current_entity_id = item.return_shape.entity_id
    envelope.current_model_time = item.return_shape.model_time
    if prior_state == EnvelopeState.OPEN:
        envelope.current_candidate = CandidateEnvelope(
            candidate_id="old", entity_id=item.return_shape.entity_id,
            source_return_shape_model_time=item.return_shape.model_time,
            qualified_at=item.context.evaluation_time, status=CandidateStatus.QUALIFIED,
            path_direction=item.return_shape.path_direction,
        )
    stale_context = item.context.model_copy(
        update={"evaluation_time": item.return_shape.model_time + item.return_shape.projection_interval + 0.001}
    )
    result = envelope.process(item.return_shape, stale_context)
    assert result.new_envelope_state == EnvelopeState.CLOSED
    assert result.aperture_after == 0.0
    assert result.stale is True
    assert result.projection_valid is False
    assert result.safety_state == SafetyState.SAFETY_CLOSED
    assert result.safety_reason == SafetyReason.SHAPE_STALE
    assert EventType.SHAPE_STALE in result.events
    assert envelope.hysteresis.consecutive_open_qualifying == 0
    assert envelope.hysteresis.consecutive_close_qualifying == 0


def test_projection_boundary_is_inclusive() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    boundary = item.context.model_copy(
        update={"evaluation_time": item.return_shape.model_time + item.return_shape.projection_interval}
    )
    result = envelope.process(item.return_shape, boundary)
    assert result.projection_valid is True
    assert result.stale is False


def test_context_only_reevaluation_emits_factual_event() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    envelope.process(item.return_shape, item.context)
    context = item.context.model_copy(update={"evaluation_time": item.context.evaluation_time + 0.1})
    result = envelope.process(item.return_shape, context)
    assert EventType.CONTEXT_REEVALUATED in result.events
    assert EventType.RETURN_SHAPE_ACCEPTED not in result.events


def test_newer_shape_supersedes_without_forced_closure() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    envelope.current_state = EnvelopeState.OPEN
    envelope.current_entity_id = item.return_shape.entity_id
    envelope.current_model_time = item.return_shape.model_time - 1.0
    envelope.current_candidate = CandidateEnvelope(
        candidate_id="old", entity_id=item.return_shape.entity_id,
        source_return_shape_model_time=item.return_shape.model_time - 1.0,
        qualified_at=item.context.evaluation_time - 1.0, status=CandidateStatus.QUALIFIED,
        path_direction=item.return_shape.path_direction,
    )
    result = envelope.process(item.return_shape, item.context)
    assert EventType.SHAPE_SUPERSEDED in result.events
    assert EventType.CANDIDATE_INVALIDATED in result.events
    assert result.new_envelope_state == EnvelopeState.OPEN


def test_backward_model_time_is_rejected() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    envelope.process(item.return_shape, item.context)
    with pytest.raises(ValueError, match="cannot move backward"):
        envelope.process(replace(item.return_shape, model_time=item.return_shape.model_time - 1.0), item.context)


def test_envelope_instance_rejects_entity_change() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    envelope.process(item.return_shape, item.context)
    with pytest.raises(ValueError, match="bound to one entity"):
        envelope.process(replace(item.return_shape, entity_id="OTHER"), item.context)


def test_repeated_runs_are_deterministic() -> None:
    item = observation()
    outputs = []
    for _ in range(3):
        envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
        outputs.append(envelope.process(item.return_shape, item.context).model_dump(mode="json"))
    assert outputs[0] == outputs[1] == outputs[2]


def test_output_contains_no_d03_decision_fields() -> None:
    names = {name.lower() for name in EnvelopeEvaluation.model_fields}
    assert names.isdisjoint(PROHIBITED_OUTPUT_FIELDS)


def test_actual_d01_types_flow_through_d02_into_d04() -> None:
    dmo = DMOOutput(
        model_time=100.0, entity_id="D01:D02:D04", model_version="0.2", state_level=1.0,
        state_velocity=0.1, state_acceleration=0.01, state_curvature=0.01, strength=0.8,
        coherence=0.7, persistence=0.6, perturbation_magnitude=0.2,
        perturbation_class="NONE", uncertainty=0.3, reversal_propensity=0.25,
        state_support_ratio=0.9, observation_half_life=120.0, forward_half_life=60.0,
        parameter_state={}, parameter_update_magnitude={}, data_quality=1.0, model_health="OK",
        dmo_schema_version="0.2", fmo_schema_version="0.2", config_hash="config",
        state_hash="state", trace_id="trace",
    )
    samples = [
        FMOSample(10.0, 1.1, 0.1, 0.3, 0.8, 0.6, 0.25),
        FMOSample(20.0, 1.2, 0.1, 0.3, 0.8, 0.6, 0.25),
        FMOSample(30.0, 1.3, 0.1, 0.3, 0.8, 0.6, 0.25),
    ]
    shape = build_return_shape(dmo, FMOOutput(100.0, "D01:D02:D04", 30.0, samples))
    assert isinstance(shape, ReturnShape)
    context = observation().context.model_copy(update={"evaluation_time": 100.0})
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    result = envelope.process(shape, context)
    assert result.entity_id == dmo.entity_id
    assert result.return_shape_model_time == dmo.model_time
    assert result.source_model_version == "0.2"


def test_recovery_after_stale_starts_closed_with_reset_memory() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    envelope.current_state = EnvelopeState.OPEN
    envelope.current_aperture = 0.9
    envelope.current_entity_id = item.return_shape.entity_id
    envelope.current_model_time = item.return_shape.model_time
    stale = item.context.model_copy(
        update={"evaluation_time": item.return_shape.model_time + item.return_shape.projection_interval + 1.0}
    )
    envelope.process(item.return_shape, stale)
    new_shape = replace(item.return_shape, model_time=item.return_shape.model_time + 40.0)
    new_context = item.context.model_copy(update={"evaluation_time": new_shape.model_time})
    recovered = envelope.process(new_shape, new_context)
    assert recovered.previous_envelope_state == EnvelopeState.CLOSED
    assert recovered.new_envelope_state == EnvelopeState.OPENING
    assert recovered.aperture_before == 0.0


def _frozen_vector_input(vector: dict) -> tuple[ReturnShape, EnvelopeContext]:
    inputs = vector["inputs"]
    values = {
        "terminal_displacement": inputs.get("terminal_displacement", 1.0),
        "maximum_absolute_displacement": inputs.get("maximum_absolute_displacement", 1.0),
        "projection_interval": inputs.get("projection_interval", 30.0),
        "forward_half_life": 60.0,
        "strength": inputs.get("strength", 1.0),
        "coherence": inputs.get("coherence", 1.0),
        "persistence": inputs.get("persistence", 1.0),
        "uncertainty": inputs.get("uncertainty", 0.0),
        "reversal_propensity": inputs.get("reversal_propensity", 0.0),
        "state_support_ratio": 1.0,
    }
    model_time = inputs.get("model_time", 100.0)
    shape = SyntheticGenerator._return_shape("VECTOR", model_time, values)
    if "terminal_decay_factor" in inputs:
        shape = replace(shape, terminal_decay_factor=inputs["terminal_decay_factor"])
    context_values = {
        "evaluation_time": inputs.get("evaluation_time", model_time),
        "market_eligible": inputs.get("market_eligible", True),
    }
    return shape, EnvelopeContext(**context_values)


def test_all_14_frozen_formula_vectors() -> None:
    vector_path = ROOT.parent / "D04_CAPTURABILITY_DETERMINISTIC_TEST_VECTORS_V0_2.json"
    vectors = json.loads(vector_path.read_text(encoding="utf-8"))["vectors"]
    assert len(vectors) == 14
    model, _, _ = model_and_observation()
    for vector in vectors:
        if vector["id"] == "invalid_geometry_invariant":
            item = observation()
            invalid = replace(
                item.return_shape,
                terminal_displacement=1.0,
                maximum_absolute_displacement=0.0,
            )
            with pytest.raises(InvalidReturnShapeError, match="INVALID_RETURNSHAPE"):
                model.evaluate(invalid, item.context)
            continue
        shape, context = _frozen_vector_input(vector)
        result = model.evaluate(shape, context)
        expected = vector["expected"]
        assert result.geometry_quality == pytest.approx(expected["geometry_quality"]), vector["id"]
        assert result.structural_quality == pytest.approx(expected["structural_quality"]), vector["id"]
        assert result.risk_quality == pytest.approx(expected["risk_quality"]), vector["id"]
        assert result.base_capturability_score == pytest.approx(expected["B"]), vector["id"]
        expected_h = int(
            context.evaluation_time <= shape.model_time + shape.projection_interval
            and context.market_eligible is not False
        )
        assert result.hard_eligibility == expected_h, vector["id"]
        assert result.capturability_score == pytest.approx(expected_h * expected["B"]), vector["id"]


def test_invalid_shape_fails_closed_with_canonical_output() -> None:
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    item = observation()
    invalid = replace(
        item.return_shape,
        terminal_displacement=1.0,
        maximum_absolute_displacement=0.0,
    )
    envelope.current_state = EnvelopeState.OPEN
    envelope.current_aperture = 0.8
    result = envelope.process(invalid, item.context)
    assert result.hard_eligibility == 0
    assert result.capturability_score == 0.0
    assert result.new_envelope_state == EnvelopeState.CLOSED
    assert result.aperture_after == 0.0
    assert result.safety_reason == SafetyReason.INVALID_RETURNSHAPE
    assert EventType.INVALID_RETURNSHAPE in result.events
    assert "INVALID_RETURNSHAPE" in result.reason_codes

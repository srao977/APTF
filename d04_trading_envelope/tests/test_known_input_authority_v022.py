from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from aptf_d04.cli.main import build_envelope
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator
from aptf_d04.models.envelope_context import (
    CONTEXT_VALUE_FIELDS,
    ContextRole,
    EnvelopeContext,
    InputProvenance,
)


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parent


def shape():
    scenario = load_scenario(ROOT / "scenarios" / "07_strong_shape_hard_gate.yaml")
    return SyntheticGenerator(scenario).generate()[0].return_shape


def model():
    envelope, _ = build_envelope(ROOT / "config" / "default.yaml")
    return envelope.capturability_model


def production_context(**overrides):
    values = overrides.pop("values", {})
    provenance = overrides.pop("provenance", {})
    return EnvelopeContext.production(
        evaluation_time=overrides.pop("evaluation_time", 1.0),
        values=values | overrides,
        provenance=provenance,
    )


def test_production_context_classifies_every_value_field() -> None:
    context = production_context()
    assert context.context_role == ContextRole.PRODUCTION
    assert set(context.provenance) == set(CONTEXT_VALUE_FIELDS)
    assert context.provenance["evaluation_time"] == InputProvenance.DERIVED
    assert all(
        context.provenance[name] == InputProvenance.UNAVAILABLE
        for name in CONTEXT_VALUE_FIELDS
        if name != "evaluation_time"
    )


def test_current_equation_has_no_gate_or_integrity_input() -> None:
    result = model().evaluate(shape(), production_context())
    payload = result.model_dump(mode="json")
    assert "feasibility_gate_score" not in payload
    assert "gate_dimension_values" not in payload
    assert "data_integrity" not in EnvelopeContext.model_fields
    assert result.capturability_score == (
        result.hard_eligibility
        * result.geometry_quality
        * result.structural_quality
        * result.risk_quality
    )


def test_unavailable_market_eligibility_does_not_fabricate_boolean() -> None:
    unavailable = model().evaluate(shape(), production_context())
    ineligible = model().evaluate(
        shape(),
        production_context(
            values={"market_eligible": False},
            provenance={"market_eligible": InputProvenance.OBSERVED},
        ),
    )
    assert unavailable.hard_eligibility == 1
    assert "MARKET_INELIGIBLE" not in unavailable.reason_codes
    assert ineligible.hard_eligibility == 0
    assert "MARKET_INELIGIBLE" in ineligible.reason_codes


def test_provenance_rejects_numeric_unavailable_and_null_active() -> None:
    with pytest.raises(ValidationError, match="UNAVAILABLE context field must be null"):
        EnvelopeContext(
            context_role=ContextRole.PRODUCTION,
            provenance={name: InputProvenance.UNAVAILABLE for name in CONTEXT_VALUE_FIELDS},
            evaluation_time=1.0,
        )
    with pytest.raises(ValidationError, match="null context field must be UNAVAILABLE"):
        production_context(
            provenance={"market_eligible": InputProvenance.OBSERVED},
        )


def test_production_context_rejects_test_fixture_provenance() -> None:
    with pytest.raises(ValidationError, match="production context cannot use TEST_FIXTURE"):
        production_context(
            values={"market_eligible": True},
            provenance={"market_eligible": InputProvenance.TEST_FIXTURE},
        )


def test_test_fixture_context_is_mechanically_distinct() -> None:
    fixture = EnvelopeContext(
        evaluation_time=1.0,
        market_eligible=True,
    )
    assert fixture.context_role == ContextRole.TEST_FIXTURE
    assert set(fixture.provenance.values()) == {InputProvenance.TEST_FIXTURE}


def test_real_market_builders_contain_no_fixed_neutral_context() -> None:
    paths = [
        REPOSITORY_ROOT / "position_transition_controller" / "real_causal_replay_harness_v0_2.py",
        REPOSITORY_ROOT / "aptf_runtime" / "src" / "aptf_runtime" / "single_observation_pipeline.py",
        REPOSITORY_ROOT / "diagnostics" / "aptf_test_001_row_10.py",
        REPOSITORY_ROOT / "diagnostics" / "aptf_test_002_two_observations.py",
    ]
    forbidden = (
        "data_integrity=",
        "market_eligible=True",
        "clock_event_quality=1.0",
        "capital_available=1.0",
        "portfolio_capacity=1.0",
        "position_capacity=1.0",
        "liquidity_quality=1.0",
        "spread_quality=1.0",
        "latency_quality=1.0",
        "execution_feasibility=1.0",
        "risk_capacity=1.0",
        "broker_health=1.0",
        "_FIXED_CONTEXT",
    )
    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert "EnvelopeContext.production(" in source
        assert not any(token in source for token in forbidden)

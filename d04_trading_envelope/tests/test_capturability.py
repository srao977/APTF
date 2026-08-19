import math
from pathlib import Path

import pytest

from aptf_d04.configuration import load_config
from aptf_d04.envelope.capturability_model import CapturabilityModelV0_2
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator


ROOT = Path(__file__).resolve().parents[1]


def _model_v02() -> CapturabilityModelV0_2:
    load_config(ROOT / "config" / "default.yaml")
    return CapturabilityModelV0_2()


def _strong_observation():
    observations = SyntheticGenerator(
        load_scenario(ROOT / "scenarios" / "07_strong_shape_hard_gate.yaml")
    ).generate()
    return observations[0]


def test_capturability_range() -> None:
    observations = SyntheticGenerator(
        load_scenario(ROOT / "scenarios" / "02_shape_becomes_capturable.yaml")
    ).generate()
    model = _model_v02()
    for observation in observations:
        result = model.evaluate(observation.return_shape, observation.context)
        assert 0.0 <= result.capturability_score <= 1.0
        assert 0.0 <= result.base_capturability_score <= 1.0


def test_market_ineligible_forces_zero() -> None:
    observation = _strong_observation()
    context = observation.context.model_copy(update={"market_eligible": False})
    result = _model_v02().evaluate(observation.return_shape, context)
    assert result.hard_eligibility == 0
    assert result.capturability_score == 0.0


def test_current_result_emits_no_gate_fields() -> None:
    observation = _strong_observation()
    result = _model_v02().evaluate(observation.return_shape, observation.context)
    assert "feasibility_gate_score" not in type(result).model_fields
    assert "gate_dimension_values" not in type(result).model_fields


def test_final_capturability_never_exceeds_base() -> None:
    observation = _strong_observation()
    result = _model_v02().evaluate(observation.return_shape, observation.context)
    assert result.capturability_score <= result.base_capturability_score


def test_eligible_final_equals_base_without_gate_multiplier() -> None:
    observation = _strong_observation()
    result = _model_v02().evaluate(observation.return_shape, observation.context)
    assert result.hard_eligibility == 1
    assert result.capturability_score == result.base_capturability_score


def test_frozen_component_equations() -> None:
    observation = _strong_observation()
    shape = observation.return_shape
    result = _model_v02().evaluate(shape, observation.context)
    expected_geometry = abs(shape.terminal_displacement) / shape.maximum_absolute_displacement
    expected_structural = (shape.strength * shape.coherence * shape.persistence) ** (1.0 / 3.0)
    expected_risk = math.sqrt((1.0 - shape.uncertainty) * (1.0 - shape.reversal_propensity))
    assert result.geometry_quality == pytest.approx(expected_geometry)
    assert result.structural_quality == pytest.approx(expected_structural)
    assert result.risk_quality == pytest.approx(expected_risk)
    assert result.base_capturability_score == pytest.approx(
        expected_geometry * expected_structural * expected_risk
    )
    assert result.capturability_score == pytest.approx(
        result.hard_eligibility * expected_geometry * expected_structural * expected_risk
    )

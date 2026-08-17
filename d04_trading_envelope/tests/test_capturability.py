import math
from pathlib import Path

import pytest

from aptf_d04.configuration import load_config
from aptf_d04.envelope.capturability_model import CapturabilityModelV0_2
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator


ROOT = Path(__file__).resolve().parents[1]


def _model_v02() -> CapturabilityModelV0_2:
    cfg = load_config(ROOT / "config" / "default.yaml")
    gate = cfg.capturability.feasibility_gate
    return CapturabilityModelV0_2(
        feasibility_gate_dimensions=gate["dimensions"],
        gate_warning_threshold=gate["warning_threshold"],
        critical_data_integrity_threshold=cfg.runtime.critical_data_integrity_threshold,
    )


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
        assert 0.0 <= result.feasibility_gate_score <= 1.0


def test_market_ineligible_forces_zero() -> None:
    observation = _strong_observation()
    context = observation.context.model_copy(update={"market_eligible": False})
    result = _model_v02().evaluate(observation.return_shape, context)
    assert result.hard_eligibility == 0
    assert result.capturability_score == 0.0


def test_minimum_gate_mode_uses_min_dimension() -> None:
    observation = _strong_observation()
    result = _model_v02().evaluate(observation.return_shape, observation.context)
    assert result.feasibility_gate_score == min(result.gate_dimension_values.values())
    assert len(result.gate_dimension_values) == 10


def test_final_capturability_never_exceeds_base() -> None:
    observation = _strong_observation()
    result = _model_v02().evaluate(observation.return_shape, observation.context)
    assert result.capturability_score <= result.base_capturability_score


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("liquidity_quality", 0.01),
        ("spread_quality", 0.01),
        ("execution_feasibility", 0.02),
        ("risk_capacity", 0.01),
    ],
)
def test_poor_gate_dimension_reduces_final(field: str, value: float) -> None:
    observation = _strong_observation()
    context = observation.context.model_copy(update={field: value})
    result = _model_v02().evaluate(observation.return_shape, context)
    assert result.capturability_score < 0.1


def test_all_gate_values_high_final_close_to_base() -> None:
    observation = _strong_observation()
    updates = {name: 0.95 for name in _model_v02().feasibility_gate_dimensions}
    context = observation.context.model_copy(update=updates)
    result = _model_v02().evaluate(observation.return_shape, context)
    assert result.capturability_score == pytest.approx(result.base_capturability_score * 0.95)


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

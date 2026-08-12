from pathlib import Path

from aptf_d04.configuration import load_config
from aptf_d04.envelope.capturability_model import CapturabilityModelV0, CapturabilityModelV0_2
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator


ROOT = Path(__file__).resolve().parents[1]


def _model_v0() -> CapturabilityModelV0:
    cfg = load_config(ROOT / "config" / "default.yaml")
    return CapturabilityModelV0(
        shape_weights=cfg.capturability.shape_weights,
        envelope_weights=cfg.capturability.envelope_weights,
        target_lifetime_seconds=cfg.capturability.target_lifetime_seconds,
    )


def _model_v02() -> CapturabilityModelV0_2:
    cfg = load_config(ROOT / "config" / "default.yaml")
    gate = cfg.capturability.feasibility_gate
    return CapturabilityModelV0_2(
        shape_weights=cfg.capturability.shape_weights,
        envelope_weights=cfg.capturability.envelope_weights,
        target_lifetime_seconds=cfg.capturability.target_lifetime_seconds,
        feasibility_gate_mode=gate["mode"],
        feasibility_gate_dimensions=gate["dimensions"],
        gate_warning_threshold=gate["warning_threshold"],
    )


def _strong_observation():
    obs = SyntheticGenerator(load_scenario(ROOT / "scenarios" / "07_strong_shape_hard_gate.yaml")).generate()
    return obs[0]


def test_capturability_range() -> None:
    path = ROOT / "scenarios" / "02_shape_becomes_capturable.yaml"
    obs = SyntheticGenerator(load_scenario(path)).generate()
    model = _model_v02()
    for o in obs:
        r = model.evaluate(o.return_shape, o.context)
        assert 0.0 <= r.capturability_score <= 1.0
        assert 0.0 <= r.base_capturability_score <= 1.0
        assert 0.0 <= r.feasibility_gate_score <= 1.0


def test_market_ineligible_forces_zero() -> None:
    path = ROOT / "scenarios" / "02_shape_becomes_capturable.yaml"
    o = SyntheticGenerator(load_scenario(path)).generate()[0]
    model = _model_v02()
    ctx = o.context.model_copy(update={"market_eligible": False})
    r = model.evaluate(o.return_shape, ctx)
    assert r.capturability_score == 0.0


def test_minimum_gate_mode_uses_min_dimension() -> None:
    o = _strong_observation()
    model = _model_v02()
    r = model.evaluate(o.return_shape, o.context)
    expected_min = min(r.gate_dimension_values.values())
    assert r.feasibility_gate_score == expected_min


def test_final_capturability_never_exceeds_base() -> None:
    o = _strong_observation()
    model = _model_v02()
    r = model.evaluate(o.return_shape, o.context)
    assert r.capturability_score <= r.base_capturability_score


def test_strong_shape_poor_liquidity_reduces_final() -> None:
    o = _strong_observation()
    model = _model_v02()
    ctx = o.context.model_copy(update={"liquidity_quality": 0.01})
    r = model.evaluate(o.return_shape, ctx)
    assert r.capturability_score < 0.1


def test_strong_shape_poor_spread_reduces_final() -> None:
    o = _strong_observation()
    model = _model_v02()
    ctx = o.context.model_copy(update={"spread_quality": 0.01})
    r = model.evaluate(o.return_shape, ctx)
    assert r.capturability_score < 0.1


def test_strong_shape_poor_execution_reduces_final() -> None:
    o = _strong_observation()
    model = _model_v02()
    ctx = o.context.model_copy(update={"execution_feasibility": 0.02})
    r = model.evaluate(o.return_shape, ctx)
    assert r.capturability_score < 0.1


def test_strong_shape_poor_risk_reduces_final() -> None:
    o = _strong_observation()
    model = _model_v02()
    ctx = o.context.model_copy(update={"risk_capacity": 0.01})
    r = model.evaluate(o.return_shape, ctx)
    assert r.capturability_score < 0.1


def test_all_gate_values_high_final_close_to_base() -> None:
    o = _strong_observation()
    model = _model_v02()
    ctx = o.context.model_copy(
        update={
            "liquidity_quality": 0.95,
            "spread_quality": 0.95,
            "latency_quality": 0.95,
            "execution_feasibility": 0.95,
            "capital_available": 0.95,
            "portfolio_capacity": 0.95,
            "position_capacity": 0.95,
            "risk_capacity": 0.95,
            "broker_health": 0.95,
            "data_integrity": 0.95,
        }
    )
    r = model.evaluate(o.return_shape, ctx)
    assert abs(r.capturability_score - r.base_capturability_score) < 0.1


def test_v0_vs_v02_hard_gate_comparison() -> None:
    o = _strong_observation()
    v0 = _model_v0().evaluate(o.return_shape, o.context)
    v02 = _model_v02().evaluate(o.return_shape, o.context)
    assert v02.capturability_score < v0.capturability_score

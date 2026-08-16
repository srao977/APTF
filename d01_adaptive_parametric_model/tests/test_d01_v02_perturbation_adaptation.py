from __future__ import annotations

import math

from d01.v02.adaptation import update_parameters
from d01.v02.config import AblationConfig, D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d01.v02.perturbation import classify_perturbation


def _obs(seq: int, t: float, price: float, volume: float) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="TEST:PA",
        event_time=t,
        receive_time=t,
        sequence_id=seq,
        price=price,
        volume=volume,
        source_quality=1.0,
        availability_mask={"price": True, "volume": True},
    )


def _eta_ref(cfg: D01V02Config, strength: float, uncertainty: float, multiplier: float) -> float:
    eta0 = cfg.adaptation.base_learning_rates["ref_alpha"]
    eta = eta0 * max(0.2, 1.0 - uncertainty) * max(0.5, strength) * multiplier
    return max(cfg.adaptation.min_learning_rate, min(cfg.adaptation.max_learning_rate, eta))


def test_off_mode_forces_neutral_multiplier_even_if_raw_multiplier_non_neutral() -> None:
    cfg = D01V02Config(ablation=AblationConfig(perturbation_adaptation=False))
    model = D01V02Model(entity_id="TEST:PA", config=cfg)

    dmo1, _ = model.step(_obs(1, 1.0, 100.0, 1000.0))
    theta_before = dmo1.parameter_state["ref_alpha"]
    dmo2, _ = model.step(_obs(2, 2.0, 100.5, 1000.0))

    strength = dmo2.strength
    uncertainty = dmo2.uncertainty
    neutral_eta = _eta_ref(cfg, strength, uncertainty, 1.0)
    update_driver = (strength - uncertainty) * 0.1
    expected_raw = neutral_eta * update_driver
    lo, hi = cfg.adaptation.parameter_bounds["ref_alpha"]
    expected_after = max(lo, min(hi, theta_before + expected_raw))
    expected_projected = abs(expected_after - theta_before)

    _, q, raw_mult = classify_perturbation(
        innovation=1.0,
        prev_velocity=0.0,
        velocity=1.0,
        source_quality=1.0,
        cfg=cfg.perturbation,
    )
    assert q > 0.0
    assert raw_mult >= 1.0

    updated, mags, _ = update_parameters(
        params={"ref_alpha": model.state.parameter_state["ref_alpha"]},
        uncertainty=uncertainty,
        strength=strength,
        perturbation_multiplier=1.0,
        cfg=cfg.adaptation,
    )
    assert math.isfinite(updated["ref_alpha"])
    assert mags["ref_alpha"] > 0.0
    assert math.isclose(dmo2.parameter_update_magnitude["ref_alpha"], expected_projected, rel_tol=0.0, abs_tol=1e-15)
    assert neutral_eta == _eta_ref(cfg, strength, uncertainty, 1.0)


def test_on_mode_meaningful_perturbation_produces_non_neutral_multiplier() -> None:
    cfg = D01V02Config()
    _cls, q, mult = classify_perturbation(
        innovation=1.0,
        prev_velocity=0.1,
        velocity=0.2,
        source_quality=1.0,
        cfg=cfg.perturbation,
    )
    assert q > 0.0
    assert mult != 1.0


def test_none_perturbation_is_neutral_when_innovation_is_zero() -> None:
    cfg = D01V02Config()
    cls, q, mult = classify_perturbation(
        innovation=0.0,
        prev_velocity=0.0,
        velocity=0.0,
        source_quality=1.0,
        cfg=cfg.perturbation,
    )
    assert cls == "NONE"
    assert q == 0.0
    assert mult == 1.0


def test_multiplier_always_within_configured_bounds() -> None:
    cfg = D01V02Config()
    lo, hi = cfg.perturbation.adaptation_multiplier_bounds
    for innovation in [0.0, 0.05, 0.25, 1.0, 10.0, 1e6]:
        _cls, _q, mult = classify_perturbation(
            innovation=innovation,
            prev_velocity=0.0,
            velocity=0.0,
            source_quality=1.0,
            cfg=cfg.perturbation,
        )
        assert lo <= mult <= hi


def test_effective_eta_differs_on_vs_off_for_meaningful_perturbation() -> None:
    cfg = D01V02Config()
    strength = 0.8
    uncertainty = 0.2
    _cls, _q, on_mult = classify_perturbation(
        innovation=1.0,
        prev_velocity=0.0,
        velocity=1.0,
        source_quality=1.0,
        cfg=cfg.perturbation,
    )
    eta_on = _eta_ref(cfg, strength, uncertainty, on_mult)
    eta_off = _eta_ref(cfg, strength, uncertainty, 1.0)
    assert eta_on != eta_off


def test_raw_update_differs_on_vs_off_when_update_driver_nonzero() -> None:
    cfg = D01V02Config()
    params = {"ref_alpha": 0.05}
    strength = 0.8
    uncertainty = 0.2
    _cls, _q, on_mult = classify_perturbation(
        innovation=1.0,
        prev_velocity=0.0,
        velocity=1.0,
        source_quality=1.0,
        cfg=cfg.perturbation,
    )

    _u_on, mags_on, _ = update_parameters(
        params=params,
        uncertainty=uncertainty,
        strength=strength,
        perturbation_multiplier=on_mult,
        cfg=cfg.adaptation,
    )
    _u_off, mags_off, _ = update_parameters(
        params=params,
        uncertainty=uncertainty,
        strength=strength,
        perturbation_multiplier=1.0,
        cfg=cfg.adaptation,
    )
    assert mags_on["ref_alpha"] != mags_off["ref_alpha"]


def test_no_future_observation_used_for_prefix_state() -> None:
    seq = [_obs(1, 1.0, 100.0, 1000.0), _obs(2, 2.0, 100.2, 1000.0), _obs(3, 3.0, 100.1, 1000.0)]
    future = _obs(4, 4.0, 100.8, 9000.0)

    model_a = D01V02Model(entity_id="TEST:PA:A")
    for obs in seq:
        dmo_a, _ = model_a.step(obs)

    model_b = D01V02Model(entity_id="TEST:PA:B")
    for obs in seq + [future]:
        dmo_b, _ = model_b.step(obs)

    assert dmo_a.state_hash != ""
    assert dmo_b.state_hash != ""

    model_c = D01V02Model(entity_id="TEST:PA:C")
    for obs in seq:
        dmo_c, _ = model_c.step(obs)

    assert dmo_a.state_hash == dmo_c.state_hash


def test_deterministic_for_same_inputs_and_config() -> None:
    seq = [_obs(i, float(i), 100.0 + 0.03 * i, 1000.0 + 10.0 * i) for i in range(1, 40)]

    model_1 = D01V02Model(entity_id="TEST:PA:1")
    hashes_1 = [model_1.step(obs)[0].state_hash for obs in seq]

    model_2 = D01V02Model(entity_id="TEST:PA:2")
    hashes_2 = [model_2.step(obs)[0].state_hash for obs in seq]

    assert hashes_1 == hashes_2

from __future__ import annotations

from d01.v02.adaptation import update_parameters
from d01.v02.config import AblationConfig, D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d01.v02.perturbation import classify_perturbation


def _effective_multiplier(enabled: bool, innovation: float, prev_velocity: float, velocity: float, source_quality: float, cfg: D01V02Config) -> float:
    _cls, _q, raw = classify_perturbation(
        innovation=innovation,
        prev_velocity=prev_velocity,
        velocity=velocity,
        source_quality=source_quality,
        cfg=cfg.perturbation,
    )
    return raw if enabled else 1.0


def _eta(cfg: D01V02Config, strength: float, uncertainty: float, multiplier: float) -> float:
    eta0 = cfg.adaptation.base_learning_rates["ref_alpha"]
    eta = eta0 * max(0.2, 1.0 - uncertainty) * max(0.5, strength) * multiplier
    return max(cfg.adaptation.min_learning_rate, min(cfg.adaptation.max_learning_rate, eta))


def _obs(seq: int, t: float, price: float, volume: float) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="TEST:PA:SRC",
        event_time=t,
        receive_time=t,
        sequence_id=seq,
        price=price,
        volume=volume,
        source_quality=1.0,
        availability_mask={"price": True, "volume": True},
    )


def test_pa01_off_neutral() -> None:
    cfg = D01V02Config()
    m = _effective_multiplier(False, innovation=1.0, prev_velocity=0.1, velocity=0.2, source_quality=1.0, cfg=cfg)
    assert m == 1.0


def test_pa02_on_moderate() -> None:
    cfg = D01V02Config()
    m = _effective_multiplier(True, innovation=0.4, prev_velocity=0.1, velocity=0.2, source_quality=1.0, cfg=cfg)
    assert m != 1.0


def test_pa03_on_strong_bounded() -> None:
    cfg = D01V02Config()
    lo, hi = cfg.perturbation.adaptation_multiplier_bounds
    m = _effective_multiplier(True, innovation=3.0, prev_velocity=0.1, velocity=0.2, source_quality=1.0, cfg=cfg)
    assert m != 1.0
    assert lo <= m <= hi


def test_pa04_none_neutral() -> None:
    cfg = D01V02Config()
    on_m = _effective_multiplier(True, innovation=0.0, prev_velocity=0.0, velocity=0.0, source_quality=1.0, cfg=cfg)
    off_m = _effective_multiplier(False, innovation=0.0, prev_velocity=0.0, velocity=0.0, source_quality=1.0, cfg=cfg)
    assert on_m == 1.0
    assert off_m == 1.0


def test_pa05_effective_eta() -> None:
    cfg = D01V02Config()
    strength = 0.8
    uncertainty = 0.2
    on_m = _effective_multiplier(True, innovation=0.4, prev_velocity=0.1, velocity=0.2, source_quality=1.0, cfg=cfg)
    off_m = _effective_multiplier(False, innovation=0.4, prev_velocity=0.1, velocity=0.2, source_quality=1.0, cfg=cfg)
    assert _eta(cfg, strength, uncertainty, on_m) != _eta(cfg, strength, uncertainty, off_m)


def test_pa06_raw_parameter_update() -> None:
    cfg = D01V02Config()
    params = {"ref_alpha": 0.05}
    strength = 0.8
    uncertainty = 0.2
    on_m = _effective_multiplier(True, innovation=0.4, prev_velocity=0.1, velocity=0.2, source_quality=1.0, cfg=cfg)

    _u_on, mag_on, _ = update_parameters(params, uncertainty=uncertainty, strength=strength, perturbation_multiplier=on_m, cfg=cfg.adaptation)
    _u_off, mag_off, _ = update_parameters(params, uncertainty=uncertainty, strength=strength, perturbation_multiplier=1.0, cfg=cfg.adaptation)
    assert mag_on["ref_alpha"] != mag_off["ref_alpha"]


def test_pa07_determinism() -> None:
    cfg = D01V02Config()
    case = dict(innovation=0.4, prev_velocity=0.1, velocity=0.2, source_quality=1.0)
    m1 = _effective_multiplier(True, cfg=cfg, **case)
    m2 = _effective_multiplier(True, cfg=cfg, **case)
    assert m1 == m2


def test_pa08_causality() -> None:
    seq = [_obs(1, 1.0, 100.0, 1000.0), _obs(2, 2.0, 100.1, 1000.0), _obs(3, 3.0, 100.2, 1000.0)]
    future = _obs(4, 4.0, 100.9, 9000.0)

    m1 = D01V02Model(entity_id="TEST:PA:CAUSAL:A", config=D01V02Config(ablation=AblationConfig(perturbation_adaptation=True)))
    h1 = [m1.step(o)[0].state_hash for o in seq]

    m2 = D01V02Model(entity_id="TEST:PA:CAUSAL:B", config=D01V02Config(ablation=AblationConfig(perturbation_adaptation=True)))
    h2_prefix = []
    for o in seq + [future]:
        d, _ = m2.step(o)
        if o.sequence_id <= 3:
            h2_prefix.append(d.state_hash)

    assert h1 == h2_prefix

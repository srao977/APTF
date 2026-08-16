from __future__ import annotations

from dataclasses import replace

from d01.v02.config import AblationConfig, D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation


def make_obs(seq: int, t: float, price: float, volume: float) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="TEST:V02",
        event_time=t,
        receive_time=t,
        sequence_id=seq,
        price=price,
        volume=volume,
        source_quality=1.0,
        availability_mask={"price": True, "volume": True},
    )


def test_causality_rejects_out_of_order() -> None:
    model = D01V02Model(entity_id="TEST:V02")
    model.step(make_obs(1, 1.0, 100.0, 1000.0))
    try:
        model.step(make_obs(1, 0.5, 100.0, 1000.0))
    except ValueError as exc:
        assert "OUT_OF_ORDER" in str(exc) or "NON_MONOTONIC" in str(exc)
    else:
        raise AssertionError("Expected causal sequence violation")


def test_outputs_bounded_and_forward_ordered() -> None:
    model = D01V02Model(entity_id="TEST:V02")
    for i in range(1, 80):
        dmo, fmo = model.step(make_obs(i, float(i), 100.0 + i * 0.03, 1200.0))
        assert 0.0 <= dmo.strength <= 1.0
        assert 0.0 <= dmo.persistence <= 1.0
        assert 0.0 <= dmo.uncertainty <= 1.0
        assert 0.0 <= dmo.reversal_propensity <= 1.0
        taus = [row.tau for row in fmo.samples]
        assert taus == sorted(taus)
        assert all(t > 0.0 for t in taus)


def test_volume_ablation_changes_strength_for_same_price_path() -> None:
    cfg_base = D01V02Config(ablation=AblationConfig(volume_influence=True))
    cfg_no_volume = D01V02Config(ablation=AblationConfig(volume_influence=False))
    model_a = D01V02Model(entity_id="TEST:V02", config=cfg_base)
    model_b = D01V02Model(entity_id="TEST:V02", config=cfg_no_volume)

    for i in range(1, 120):
        obs = make_obs(i, float(i), 100.0 + i * 0.02, 5000.0 if i > 60 else 900.0)
        dmo_a, _ = model_a.step(obs)
        dmo_b, _ = model_b.step(obs)

    assert abs(dmo_a.strength - dmo_b.strength) > 1e-4


def test_snapshot_is_stable_for_repeated_replay() -> None:
    seq = [make_obs(i, float(i), 100.0 + i * 0.01, 1000.0) for i in range(1, 60)]

    model_1 = D01V02Model(entity_id="TEST:V02")
    out_1 = [model_1.step(obs)[0].state_hash for obs in seq]

    model_2 = D01V02Model(entity_id="TEST:V02")
    out_2 = [model_2.step(obs)[0].state_hash for obs in seq]

    assert out_1 == out_2
    snap = model_1.snapshot()
    assert "state_hash" in snap
    assert snap["configuration_hash"] == model_1.config_hash


def test_elastic_forward_toggle() -> None:
    elastic = D01V02Model(entity_id="TEST:V02", config=D01V02Config(ablation=AblationConfig(elastic_forward_interval=True)))
    fixed = D01V02Model(entity_id="TEST:V02", config=D01V02Config(ablation=AblationConfig(elastic_forward_interval=False)))

    for i in range(1, 100):
        obs = make_obs(i, float(i), 100.0 + i * 0.05, 1400.0)
        _, fmo_elastic = elastic.step(obs)
        _, fmo_fixed = fixed.step(obs)

    assert fmo_elastic.interval_length != fmo_fixed.interval_length

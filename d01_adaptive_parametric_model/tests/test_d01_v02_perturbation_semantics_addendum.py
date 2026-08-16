from __future__ import annotations

import math

from d01.v02.config import D01V02Config
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d01.v02.perturbation import classify_perturbation


def _classify(innovation: float, prev_velocity: float, velocity: float, source_quality: float = 1.0) -> tuple[str, float, float]:
    cfg = D01V02Config()
    return classify_perturbation(
        innovation=innovation,
        prev_velocity=prev_velocity,
        velocity=velocity,
        source_quality=source_quality,
        cfg=cfg.perturbation,
        numerical_epsilon=cfg.numerical.epsilon,
    )


def _obs(seq: int, price: float) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="TEST:PERTURBATION:ADDENDUM",
        event_time=float(seq),
        receive_time=float(seq),
        sequence_id=seq,
        price=price,
        volume=1000.0,
        source_quality=1.0,
        availability_mask={"price": True, "volume": True},
    )


def test_immaterial_innovation_is_none() -> None:
    cls, q, _multiplier = _classify(innovation=5e-5, prev_velocity=0.1, velocity=0.11)
    assert q <= math.sqrt(D01V02Config().numerical.epsilon)
    assert cls == "NONE"


def test_material_compatible_innovation_is_reinforcing() -> None:
    cls, q, _multiplier = _classify(innovation=0.01, prev_velocity=0.1, velocity=0.12)
    assert q > math.sqrt(D01V02Config().numerical.epsilon)
    assert cls == "REINFORCING"


def test_material_opposing_change_is_contradicting() -> None:
    cls, _q, _multiplier = _classify(innovation=0.01, prev_velocity=0.1, velocity=0.05)
    assert cls == "CONTRADICTING"


def test_material_sign_flip_is_reversing() -> None:
    cls, _q, _multiplier = _classify(innovation=0.01, prev_velocity=0.1, velocity=-0.05)
    assert cls == "REVERSING"


def test_degraded_source_is_structural_even_without_innovation() -> None:
    cls, q, _multiplier = _classify(innovation=0.0, prev_velocity=0.0, velocity=0.0, source_quality=0.4)
    assert q == 0.0
    assert cls == "STRUCTURAL/UNKNOWN"


def test_trace_records_material_detection_inputs() -> None:
    model = D01V02Model(entity_id="TEST:PERTURBATION:TRACE")
    model.step(_obs(1, 100.0))
    model.step(_obs(2, 100.5))

    trace = model.trace_records[-1].to_dict()
    assert trace["innovation_magnitude"] > 0.0
    assert trace["perturbation_materiality_floor"] == math.sqrt(model.config.numerical.epsilon)
    assert trace["perturbation_detected"] is True
    assert trace["perturbation_class"] != "NONE"
    assert trace["source_quality"] == 1.0
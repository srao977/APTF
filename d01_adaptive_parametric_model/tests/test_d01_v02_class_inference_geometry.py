from __future__ import annotations

from d01.v02.config import D01V02Config
from d01.v02.perturbation import classify_perturbation


def _classify(
    *,
    magnitude_input: float,
    prior_level: float,
    previous_velocity: float,
    current_velocity: float,
    signed_innovation: float,
    source_quality: float = 1.0,
) -> str:
    cfg = D01V02Config()
    semantic_class, _magnitude, _multiplier = classify_perturbation(
        innovation=magnitude_input,
        prev_velocity=previous_velocity,
        velocity=current_velocity,
        source_quality=source_quality,
        cfg=cfg.perturbation,
        numerical_epsilon=cfg.numerical.epsilon,
        innovation_residual=signed_innovation,
        prior_level=prior_level,
    )
    return semantic_class


def test_class01_positive_reinforcement() -> None:
    assert _classify(magnitude_input=0.1, prior_level=1.0, previous_velocity=0.2, current_velocity=0.3, signed_innovation=0.1) == "REINFORCING"


def test_class02_negative_reinforcement() -> None:
    assert _classify(magnitude_input=0.1, prior_level=-1.0, previous_velocity=-0.2, current_velocity=-0.3, signed_innovation=-0.1) == "REINFORCING"


def test_class03_positive_trajectory_contradiction() -> None:
    assert _classify(magnitude_input=0.1, prior_level=1.0, previous_velocity=0.2, current_velocity=0.1, signed_innovation=-0.1) == "CONTRADICTING"


def test_class04_negative_trajectory_contradiction() -> None:
    assert _classify(magnitude_input=0.1, prior_level=-1.0, previous_velocity=-0.2, current_velocity=-0.1, signed_innovation=0.1) == "CONTRADICTING"


def test_class05_positive_to_negative_reversal() -> None:
    assert _classify(magnitude_input=0.1, prior_level=1.0, previous_velocity=0.2, current_velocity=-0.2, signed_innovation=-0.4) == "REVERSING"


def test_class06_negative_to_positive_reversal() -> None:
    assert _classify(magnitude_input=0.1, prior_level=-1.0, previous_velocity=-0.2, current_velocity=0.2, signed_innovation=0.4) == "REVERSING"


def test_class07_material_ambiguous() -> None:
    assert _classify(magnitude_input=0.1, prior_level=0.0, previous_velocity=0.0, current_velocity=0.0, signed_innovation=0.1) == "STRUCTURAL/UNKNOWN"


def test_class08_nonmaterial() -> None:
    assert _classify(magnitude_input=5e-5, prior_level=1.0, previous_velocity=0.2, current_velocity=0.2, signed_innovation=5e-5) == "NONE"


def test_class09_mirror_reinforcing() -> None:
    positive = _classify(magnitude_input=0.1, prior_level=1.0, previous_velocity=0.2, current_velocity=0.3, signed_innovation=0.1)
    negative = _classify(magnitude_input=0.1, prior_level=-1.0, previous_velocity=-0.2, current_velocity=-0.3, signed_innovation=-0.1)
    assert positive == negative == "REINFORCING"


def test_class10_mirror_contradicting() -> None:
    positive = _classify(magnitude_input=0.1, prior_level=1.0, previous_velocity=0.2, current_velocity=0.1, signed_innovation=-0.1)
    negative = _classify(magnitude_input=0.1, prior_level=-1.0, previous_velocity=-0.2, current_velocity=-0.1, signed_innovation=0.1)
    assert positive == negative == "CONTRADICTING"


def test_class11_mirror_reversing() -> None:
    positive = _classify(magnitude_input=0.1, prior_level=1.0, previous_velocity=0.2, current_velocity=-0.2, signed_innovation=-0.4)
    negative = _classify(magnitude_input=0.1, prior_level=-1.0, previous_velocity=-0.2, current_velocity=0.2, signed_innovation=0.4)
    assert positive == negative == "REVERSING"


def test_class12_magnitude_independence() -> None:
    moderate = _classify(magnitude_input=0.01, prior_level=1.0, previous_velocity=0.2, current_velocity=0.1, signed_innovation=-0.1)
    strong = _classify(magnitude_input=2.0, prior_level=1.0, previous_velocity=0.2, current_velocity=0.1, signed_innovation=-0.1)
    assert moderate == strong == "CONTRADICTING"
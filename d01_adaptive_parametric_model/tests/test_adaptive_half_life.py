from aptf_d01.temporal.adaptive_half_life import AdaptiveHalfLife
from aptf_d01.temporal.half_life import HalfLifeState


def test_perturbation_can_shorten_and_reinforcement_can_lengthen() -> None:
    a = AdaptiveHalfLife(HalfLifeState.from_bounds(5.0, 60.0, 300.0))
    h1 = a.update(perturbation_magnitude=0.8, reinforcement=0.0, enabled=True, perturbation_responsive=True)
    assert h1 < 60.0
    h2 = a.update(perturbation_magnitude=0.0, reinforcement=1.0, enabled=True, perturbation_responsive=True)
    assert h2 >= h1

from aptf_d01.temporal.half_life import HalfLifeState


def test_half_life_bounds_respected() -> None:
    s = HalfLifeState.from_bounds(5.0, 60.0, 300.0)
    assert s.clamp(1.0) == 5.0
    assert s.clamp(1000.0) == 300.0

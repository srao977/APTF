from aptf_d01.temporal.decay import half_life_decay


def test_half_life_decay_values() -> None:
    assert abs(half_life_decay(10.0, 10.0) - 0.5) < 1e-9
    assert abs(half_life_decay(20.0, 10.0) - 0.25) < 1e-9
    assert 0.0 <= half_life_decay(5.0, 10.0) <= 1.0

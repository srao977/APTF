def is_ohlc_valid(o: float, h: float, l: float, c: float) -> bool:
    return h >= o and h >= c and h >= l and l <= o and l <= c and o > 0 and h > 0 and l > 0 and c > 0


def test_valid_ohlc_rule() -> None:
    assert is_ohlc_valid(100.0, 101.0, 99.5, 100.2)


def test_invalid_ohlc_rule() -> None:
    assert not is_ohlc_valid(100.0, 99.0, 98.0, 100.5)

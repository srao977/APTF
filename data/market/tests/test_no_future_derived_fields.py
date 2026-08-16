def compute_returns(closes: list[float]) -> list[float | None]:
    out: list[float | None] = [None]
    for i in range(1, len(closes)):
        out.append(closes[i] / closes[i - 1] - 1.0)
    return out


def test_returns_use_only_previous_close() -> None:
    closes = [100.0, 101.0, 103.0]
    ret = compute_returns(closes)
    assert abs((ret[1] or 0.0) - 0.01) < 1e-12
    assert abs((ret[2] or 0.0) - (103.0 / 101.0 - 1.0)) < 1e-12

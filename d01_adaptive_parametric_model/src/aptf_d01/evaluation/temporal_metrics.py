from __future__ import annotations


def persistence_error(pred: list[float], actual: list[float]) -> float:
    if not pred:
        return 0.0
    return sum(abs(p - a) for p, a in zip(pred, actual)) / len(pred)


def half_life_error(pred: list[float], actual: list[float]) -> float:
    if not pred:
        return 0.0
    return sum(abs(p - a) for p, a in zip(pred, actual)) / len(pred)

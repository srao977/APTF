from __future__ import annotations


def directional_accuracy(pred: list[float], actual: list[float]) -> float:
    if not pred:
        return 0.0
    match = 0
    for p, a in zip(pred, actual):
        ps = 1 if p > 0 else (-1 if p < 0 else 0)
        as_ = 1 if a > 0 else (-1 if a < 0 else 0)
        if ps == as_:
            match += 1
    return match / len(pred)

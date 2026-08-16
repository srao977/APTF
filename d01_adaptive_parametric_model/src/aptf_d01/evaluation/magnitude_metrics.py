from __future__ import annotations

import math


def mae(pred: list[float], actual: list[float]) -> float:
    if not pred:
        return 0.0
    return sum(abs(p - a) for p, a in zip(pred, actual)) / len(pred)


def rmse(pred: list[float], actual: list[float]) -> float:
    if not pred:
        return 0.0
    mse = sum((p - a) ** 2 for p, a in zip(pred, actual)) / len(pred)
    return math.sqrt(mse)

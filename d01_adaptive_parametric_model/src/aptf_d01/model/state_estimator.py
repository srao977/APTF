from __future__ import annotations


def bounded_tanh(x: float, scale: float = 1.0) -> float:
    import math

    if scale <= 0:
        scale = 1.0
    return math.tanh(x / scale)

from __future__ import annotations


def half_life_decay(delta_t: float, half_life_seconds: float) -> float:
    if half_life_seconds <= 0:
        raise ValueError("half_life_seconds must be > 0")
    if delta_t <= 0:
        return 1.0
    w = 2.0 ** (-delta_t / half_life_seconds)
    if w < 0.0:
        return 0.0
    if w > 1.0:
        return 1.0
    return w

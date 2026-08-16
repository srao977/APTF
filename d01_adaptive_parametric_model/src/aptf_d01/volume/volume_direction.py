from __future__ import annotations


def directional_volume(delta_price: float, volume_log: float) -> float:
    if delta_price > 0:
        return volume_log
    if delta_price < 0:
        return -volume_log
    return 0.0

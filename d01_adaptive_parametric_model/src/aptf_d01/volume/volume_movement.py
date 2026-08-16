from __future__ import annotations


def volume_movement_abs(volume_log: float, delta_price: float) -> float:
    return volume_log * abs(delta_price)


def volume_movement_signed(volume_log: float, delta_price: float) -> float:
    return volume_log * delta_price

from __future__ import annotations

from aptf_d01.temporal.decay import half_life_decay


def decayed_volume(volume_log: float, delta_seconds: float, volume_half_life_seconds: float) -> float:
    return volume_log * half_life_decay(delta_seconds, volume_half_life_seconds)

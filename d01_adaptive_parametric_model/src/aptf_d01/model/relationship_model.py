from __future__ import annotations


def directional_coherence(delta_price: float, directional_volume: float) -> float:
    if delta_price == 0 or directional_volume == 0:
        return 0.0
    return 1.0 if (delta_price > 0 and directional_volume > 0) or (delta_price < 0 and directional_volume < 0) else -1.0

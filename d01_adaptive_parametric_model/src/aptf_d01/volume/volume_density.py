from __future__ import annotations


def volume_density(total_volume: float, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    return total_volume / elapsed_seconds

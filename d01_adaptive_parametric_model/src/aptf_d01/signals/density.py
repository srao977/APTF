from __future__ import annotations


def signal_density(effective_mass: float, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    return effective_mass / elapsed_seconds

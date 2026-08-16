from __future__ import annotations


def signal_strength(effective_mass: float, movement_abs: float, directional_coherence: float) -> float:
    raw = 0.45 * effective_mass + 0.45 * movement_abs + 0.1 * directional_coherence
    return max(0.0, min(1.0, raw))

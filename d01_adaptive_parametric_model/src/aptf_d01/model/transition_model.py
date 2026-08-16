from __future__ import annotations


def reversal_tendency(direction_state: float, previous_direction_state: float, perturbation_magnitude: float) -> float:
    flip = -direction_state * previous_direction_state
    base = 0.2 if flip > 0 else 0.05
    return max(0.0, min(1.0, base + 0.7 * perturbation_magnitude))

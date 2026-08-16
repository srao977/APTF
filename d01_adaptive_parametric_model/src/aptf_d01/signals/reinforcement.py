from __future__ import annotations


def reinforcement_score(previous_direction: float, current_direction: float, perturbation_magnitude: float) -> float:
    aligned = previous_direction * current_direction
    base = 0.15 if aligned > 0 else -0.15
    return max(-1.0, min(1.0, base + 0.2 * perturbation_magnitude))

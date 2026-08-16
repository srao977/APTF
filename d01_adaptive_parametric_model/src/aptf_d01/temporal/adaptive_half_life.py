from __future__ import annotations

from .half_life import HalfLifeState


class AdaptiveHalfLife:
    def __init__(
        self,
        state: HalfLifeState,
        perturbation_shorten_factor: float = 0.35,
        reinforcement_lengthen_factor: float = 1.15,
    ) -> None:
        self.state = state
        self.perturbation_shorten_factor = perturbation_shorten_factor
        self.reinforcement_lengthen_factor = reinforcement_lengthen_factor

    def update(self, perturbation_magnitude: float, reinforcement: float, enabled: bool, perturbation_responsive: bool) -> float:
        current = self.state.current_seconds
        if not enabled:
            return current

        updated = current
        if perturbation_responsive and perturbation_magnitude > 0.0:
            updated = current * (1.0 - min(0.95, perturbation_magnitude) * self.perturbation_shorten_factor)
        if reinforcement > 0:
            updated = updated * (1.0 + min(reinforcement, 1.0) * (self.reinforcement_lengthen_factor - 1.0))

        self.state.current_seconds = self.state.clamp(updated)
        return self.state.current_seconds

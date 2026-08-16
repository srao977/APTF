from __future__ import annotations

from .decay import half_life_decay


class TemporalRelevanceModel:
    def __init__(self, observation_half_life_seconds: float, forward_half_life_seconds: float) -> None:
        self.observation_half_life_seconds = observation_half_life_seconds
        self.forward_half_life_seconds = forward_half_life_seconds

    def observation_weight(self, age_seconds: float) -> float:
        return half_life_decay(age_seconds, self.observation_half_life_seconds)

    def forward_decay(self, horizon_seconds: float) -> float:
        return half_life_decay(horizon_seconds, self.forward_half_life_seconds)

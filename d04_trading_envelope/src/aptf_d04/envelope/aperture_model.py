from __future__ import annotations

from abc import ABC, abstractmethod

from aptf_d04.models.enums import EnvelopeState


class ApertureModel(ABC):
    @abstractmethod
    def update(
        self,
        capturability_score: float,
        current_state: EnvelopeState,
        prior_aperture: float,
    ) -> float:
        raise NotImplementedError


class ApertureModelV0(ApertureModel):
    def __init__(self, alpha: float) -> None:
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("alpha must be in [0,1]")
        self.alpha = alpha

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def update(
        self,
        capturability_score: float,
        current_state: EnvelopeState,
        prior_aperture: float,
    ) -> float:
        target = self._clamp(capturability_score)
        smoothed = self.alpha * target + (1.0 - self.alpha) * self._clamp(prior_aperture)
        return self._clamp(smoothed)

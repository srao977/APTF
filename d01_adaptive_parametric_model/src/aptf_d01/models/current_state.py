from __future__ import annotations

from pydantic import BaseModel


class CurrentState(BaseModel):
    direction_state: float
    magnitude_state: float
    strength: float
    persistence: float
    reinforcement: float
    uncertainty: float
    reversal_tendency: float
    perturbation_state: float

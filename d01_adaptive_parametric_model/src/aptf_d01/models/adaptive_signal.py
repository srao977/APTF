from __future__ import annotations

from pydantic import BaseModel


class AdaptiveSignal(BaseModel):
    signal_id: str
    entity_id: str
    signal_type: str

    strength: float
    half_life_seconds: float
    reinforcement: float
    uncertainty: float

    effective_mass: float
    density: float

    created_at: float
    updated_at: float
    version: int

    active: bool = True

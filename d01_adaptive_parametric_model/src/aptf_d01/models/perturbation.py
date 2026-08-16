from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import PerturbationType


class Perturbation(BaseModel):
    perturbation_id: str
    entity_id: str
    timestamp: float
    magnitude: float
    direction: float
    type: PerturbationType
    confidence: float
    affected_channels: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)

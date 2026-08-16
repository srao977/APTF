from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ForwardModelOutput(BaseModel):
    entity_id: str
    model_time: float

    forward_interval_start: float
    forward_interval_end: float

    directional_support: float
    expected_magnitude: float
    expected_persistence: float

    forward_half_life: float
    expected_decay: float
    reversal_tendency: float
    uncertainty: float

    favorable_excursion_estimate: float
    adverse_excursion_estimate: float

    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)

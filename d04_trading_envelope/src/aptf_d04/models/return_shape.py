from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import Direction


class ReturnShape(BaseModel):
    model_config = ConfigDict(extra="forbid")

    return_shape_id: str
    candidate_id: str
    version: int = Field(ge=1)

    timestamp: float
    direction: Direction

    shape_quality: float = Field(ge=0.0, le=1.0)
    forward_support: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)

    expected_lifetime_seconds: float
    candidate_rr: float

    magnitude_score: float = Field(ge=0.0, le=1.0)
    persistence_score: float = Field(ge=0.0, le=1.0)
    decay_score: float = Field(ge=0.0, le=1.0)
    reversal_risk: float = Field(ge=0.0, le=1.0)

    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import EventType


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    timestamp: float
    candidate_id: str | None = None
    return_shape_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .enums import EventType


class OpportunityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    candidate_id: str
    return_shape_id: str
    timestamp: float
    reason_codes: list[str]

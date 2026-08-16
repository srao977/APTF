from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .enums import SessionState


class NormalizedObservation(BaseModel):
    entity_id: str
    event_id: str
    source_id: str
    source_sequence: int

    exchange_timestamp: float
    receive_timestamp: float
    model_available_timestamp: float

    price: float
    trade_size: float | None = None
    volume: float

    bid: float | None = None
    ask: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None

    session_state: SessionState = SessionState.OPEN

    contextual: dict[str, float] = Field(default_factory=dict)
    data_valid: bool = True
    channel_availability: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

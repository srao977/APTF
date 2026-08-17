from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EnvelopeContext(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    evaluation_time: float
    market_eligible: bool

    data_integrity: float = Field(ge=0.0, le=1.0)
    clock_event_quality: float = Field(ge=0.0, le=1.0)
    capital_available: float = Field(ge=0.0, le=1.0)
    portfolio_capacity: float = Field(ge=0.0, le=1.0)
    position_capacity: float = Field(ge=0.0, le=1.0)
    liquidity_quality: float = Field(ge=0.0, le=1.0)
    spread_quality: float = Field(ge=0.0, le=1.0)
    latency_quality: float = Field(ge=0.0, le=1.0)
    execution_feasibility: float = Field(ge=0.0, le=1.0)
    risk_capacity: float = Field(ge=0.0, le=1.0)
    broker_health: float = Field(ge=0.0, le=1.0)


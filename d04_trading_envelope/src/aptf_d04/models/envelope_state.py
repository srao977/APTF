from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import ContinuationSignal, EnvelopeState, EventType
from .opportunity import OpportunityEvent


class EnvelopeTransitionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    timestamp: float


class EnvelopeEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: float
    return_shape_id: str
    candidate_id: str
    return_shape_version: int

    previous_state: EnvelopeState
    new_state: EnvelopeState

    shape_quality: float = Field(ge=0.0, le=1.0)
    shape_component: float = Field(ge=0.0, le=1.0)
    envelope_component: float = Field(ge=0.0, le=1.0)
    lifetime_component: float = Field(ge=0.0, le=1.0)
    base_capturability_score: float = Field(ge=0.0, le=1.0)
    feasibility_gate_score: float = Field(ge=0.0, le=1.0)
    capturability_score: float = Field(ge=0.0, le=1.0)
    gate_dimension_values: dict[str, float] = Field(default_factory=dict)

    previous_aperture: float = Field(ge=0.0, le=1.0)
    aperture: float = Field(ge=0.0, le=1.0)

    position_open: bool
    entry_eligible: bool
    continuation_signal: ContinuationSignal = ContinuationSignal.NONE

    reason_codes: list[str] = Field(default_factory=list)
    events_emitted: list[EventType] = Field(default_factory=list)
    state_transition_event: EnvelopeTransitionEvent | None = None
    opportunity_event: OpportunityEvent | None = None

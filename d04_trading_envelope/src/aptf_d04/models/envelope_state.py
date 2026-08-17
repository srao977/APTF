from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import EnvelopeState, EventType, SafetyReason, SafetyState
from .opportunity import CandidateEnvelope


class EnvelopeTransitionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    event_type: EventType
    timestamp: float


class EnvelopeEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    evaluation_time: float
    entity_id: str
    return_shape_model_time: float
    source_model_version: str
    hard_eligibility: int = Field(ge=0, le=1)
    geometry_quality: float = Field(ge=0.0, le=1.0)
    structural_quality: float = Field(ge=0.0, le=1.0)
    risk_quality: float = Field(ge=0.0, le=1.0)
    base_capturability_score: float = Field(ge=0.0, le=1.0)
    feasibility_gate_score: float = Field(ge=0.0, le=1.0)
    capturability_score: float = Field(ge=0.0, le=1.0)
    previous_envelope_state: EnvelopeState
    new_envelope_state: EnvelopeState
    aperture_before: float = Field(ge=0.0, le=1.0)
    aperture_after: float = Field(ge=0.0, le=1.0)
    projection_valid: bool
    stale: bool
    safety_state: SafetyState
    safety_reason: SafetyReason | None
    candidate_envelope: CandidateEnvelope | None
    gate_dimension_values: dict[str, float]
    reason_codes: list[str] = Field(default_factory=list)
    events: list[EventType] = Field(default_factory=list)

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .current_state import CurrentState
from .volume_state import VolumeState


class DynamicModelOutput(BaseModel):
    entity_id: str
    model_instance_id: str
    model_time: float

    model_definition_version: str
    parameter_state_version: int

    observation_interval_start: float
    observation_interval_end: float

    input_channel_snapshot: dict[str, float]
    adaptive_signal_snapshot: dict[str, float]

    current_state: CurrentState

    direction_state: float
    magnitude_state: float

    strength: float
    persistence: float
    reinforcement: float
    uncertainty: float

    observation_half_life: float
    forward_half_life: float

    reversal_tendency: float

    perturbation_state: float

    volume_state: VolumeState

    parameter_summary: dict[str, Any] = Field(default_factory=dict)
    model_health: dict[str, Any] = Field(default_factory=dict)

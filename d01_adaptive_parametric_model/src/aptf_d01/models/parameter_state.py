from __future__ import annotations

from pydantic import BaseModel, Field


class ParameterState(BaseModel):
    model_definition_version: str
    parameter_state_version: int
    updated_at: float
    parameters: dict[str, list[float]] = Field(default_factory=dict)

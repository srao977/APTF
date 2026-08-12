from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ApertureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    previous_aperture: float = Field(ge=0.0, le=1.0)
    new_aperture: float = Field(ge=0.0, le=1.0)

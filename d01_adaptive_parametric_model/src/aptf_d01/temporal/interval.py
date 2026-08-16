from __future__ import annotations

from pydantic import BaseModel


class ObservationInterval(BaseModel):
    start: float
    end: float


class ForwardInterval(BaseModel):
    start: float
    end: float

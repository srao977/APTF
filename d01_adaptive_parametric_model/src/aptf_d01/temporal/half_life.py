from __future__ import annotations

from pydantic import BaseModel


class HalfLifeState(BaseModel):
    min_seconds: float
    default_seconds: float
    max_seconds: float
    current_seconds: float

    @classmethod
    def from_bounds(cls, min_seconds: float, default_seconds: float, max_seconds: float) -> "HalfLifeState":
        return cls(
            min_seconds=min_seconds,
            default_seconds=default_seconds,
            max_seconds=max_seconds,
            current_seconds=max(min(default_seconds, max_seconds), min_seconds),
        )

    def clamp(self, value: float) -> float:
        return max(self.min_seconds, min(value, self.max_seconds))

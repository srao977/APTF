from __future__ import annotations

from pydantic import BaseModel


class VolumeState(BaseModel):
    raw_volume: float
    relative_volume: float
    volume_log: float
    volume_density: float
    directional_volume: float
    volume_movement_interaction_abs: float
    volume_movement_interaction_signed: float
    volume_half_life_seconds: float

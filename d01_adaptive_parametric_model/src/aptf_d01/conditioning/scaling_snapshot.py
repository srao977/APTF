from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScalingSnapshot:
    feature_name: str
    center: float
    scale: float
    statistics_version: int
    warmup_state: bool

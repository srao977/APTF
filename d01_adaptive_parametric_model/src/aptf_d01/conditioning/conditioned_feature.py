from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConditionedFeature:
    feature_name: str
    raw_value: float
    raw_units: str
    model_value: float
    scaling_method: str
    center: float
    scale: float
    lower_bound: float
    upper_bound: float
    statistics_version: int
    model_time: float
    warmup_state: bool
    valid: bool
    pre_bound_model_value: float
    bound_hit: bool

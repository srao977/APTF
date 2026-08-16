from __future__ import annotations

from dataclasses import dataclass

from .conditioned_feature import ConditionedFeature
from .running_statistics import RunningStatistics


@dataclass
class FeatureScalerConfig:
    method: str = "RUNNING_ZSCORE"
    epsilon: float = 1e-6
    lower_bound: float = -8.0
    upper_bound: float = 8.0
    minimum_warmup_observations: int = 20


class RunningZScoreFeatureScaler:
    def __init__(self, config: FeatureScalerConfig) -> None:
        self.config = config
        self.stats = RunningStatistics()

    def reset(self) -> None:
        self.stats = RunningStatistics()

    def is_warmup(self) -> bool:
        return self.stats.count < self.config.minimum_warmup_observations

    def transform_then_update(self, feature_name: str, raw_value: float, raw_units: str, model_time: float) -> ConditionedFeature:
        # Use prior statistics for point-in-time causal transformation.
        prior_center = self.stats.mean
        prior_scale = max(self.stats.std(), self.config.epsilon)

        warmup_state = self.is_warmup()
        if warmup_state:
            pre_bound = 0.0
        else:
            pre_bound = (raw_value - prior_center) / prior_scale

        model_value = min(self.config.upper_bound, max(self.config.lower_bound, pre_bound))
        bound_hit = pre_bound != model_value

        out = ConditionedFeature(
            feature_name=feature_name,
            raw_value=raw_value,
            raw_units=raw_units,
            model_value=model_value,
            scaling_method=self.config.method,
            center=prior_center,
            scale=prior_scale,
            lower_bound=self.config.lower_bound,
            upper_bound=self.config.upper_bound,
            statistics_version=self.stats.version,
            model_time=model_time,
            warmup_state=warmup_state,
            valid=True,
            pre_bound_model_value=pre_bound,
            bound_hit=bound_hit,
        )

        # Update happens after transformation to preserve causality.
        self.stats.update(raw_value)
        return out

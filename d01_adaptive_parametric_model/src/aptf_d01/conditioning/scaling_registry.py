from __future__ import annotations

from dataclasses import dataclass

from .conditioned_feature import ConditionedFeature
from .feature_scaler import FeatureScalerConfig, RunningZScoreFeatureScaler


@dataclass
class ScalingPolicy:
    method: str
    units: str


class FeatureScalingRegistry:
    def __init__(
        self,
        policies: dict[str, ScalingPolicy],
        minimum_warmup_observations: int,
        epsilon: float,
        lower_bound: float,
        upper_bound: float,
    ) -> None:
        self.policies = policies
        self.scalers: dict[str, RunningZScoreFeatureScaler] = {}
        self._cfg = FeatureScalerConfig(
            method="RUNNING_ZSCORE",
            epsilon=epsilon,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            minimum_warmup_observations=minimum_warmup_observations,
        )

        for feature_name in policies:
            self.scalers[feature_name] = RunningZScoreFeatureScaler(self._cfg)

    def reset(self) -> None:
        for scaler in self.scalers.values():
            scaler.reset()

    def transform(self, feature_name: str, raw_value: float, model_time: float) -> ConditionedFeature:
        policy = self.policies[feature_name]
        scaler = self.scalers[feature_name]
        return scaler.transform_then_update(
            feature_name=feature_name,
            raw_value=raw_value,
            raw_units=policy.units,
            model_time=model_time,
        )

    def warmup_state(self) -> bool:
        return any(s.is_warmup() for s in self.scalers.values())

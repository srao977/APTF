from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class VolumePolicyConfig:
    policy_id: str
    state_source: str
    lower_threshold: float
    upper_threshold: float
    confirmation_observations: int
    epsilon: float


@dataclass(frozen=True)
class VolumePolicyState:
    color: str | None = None
    pending_color: str | None = None
    pending_count: int = 0


@dataclass(frozen=True)
class VolumeEmission:
    symbol: str
    timestamp: str
    engine: str
    v_raw: float
    v: float
    v1: float
    v2: float
    projected_v: float
    projected_v1: None
    projected_v2: None
    activity_state_value: float
    phase: str
    transition_state: str
    confidence_state: str
    domain_state: str
    raw_color: str
    cockpit_color: str
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason_codes"] = list(self.reason_codes)
        return payload


class VolumeEngine:
    def __init__(self, config: VolumePolicyConfig):
        if config.state_source not in {"V_N", "INTERVAL_MEAN_V_N"}:
            raise ValueError("unsupported Volume state source")
        if not 0 < config.lower_threshold < config.upper_threshold:
            raise ValueError("Volume thresholds must be positive and ordered")
        if config.confirmation_observations < 1:
            raise ValueError("confirmation_observations must be positive")
        self.config = config

    def observe(
        self,
        numerical: Mapping[str, object],
        state: VolumePolicyState,
    ) -> tuple[VolumeEmission, VolumePolicyState]:
        v_raw = float(numerical["V_RAW"])
        v = float(numerical["V_N"])
        v1 = float(numerical["V1"])
        v2 = float(numerical["V2"])
        projected_v = float(numerical["predicted_next_V_N"])
        interval_mean = float(numerical["interval_mean_vn"])
        finite = all(math.isfinite(value) for value in (v_raw, v, v1, v2, projected_v, interval_mean))
        if not finite:
            emission = self._build(
                numerical, v_raw, v, v1, v2, projected_v, math.nan,
                "INVALID", "INVALID", "INVALID", "INVALID", ("NONFINITE_VOLUME_STATE",),
            )
            return emission, VolumePolicyState(color="INVALID")

        activity = v if self.config.state_source == "V_N" else interval_mean
        if activity >= self.config.upper_threshold:
            raw_color = "GREEN"
            activity_reason = "ACTIVITY_ABOVE_BASELINE"
        elif activity <= self.config.lower_threshold:
            raw_color = "RED"
            activity_reason = "ACTIVITY_BELOW_BASELINE"
        else:
            raw_color = "AMBER"
            activity_reason = "ACTIVITY_NEAR_BASELINE"

        phase = self._phase(v1, v2)
        pending_color = None
        pending_count = 0
        color = raw_color
        transition = "STABLE"
        reasons = [activity_reason, phase]
        if state.color is not None and raw_color != state.color:
            pending_count = state.pending_count + 1 if state.pending_color == raw_color else 1
            if pending_count < self.config.confirmation_observations:
                color = "AMBER"
                pending_color = raw_color
                transition = f"PENDING_{raw_color}"
                reasons.append("STATE_CONFIRMATION_PENDING")
            else:
                transition = f"CONFIRMED_{raw_color}"
                reasons.append("STATE_CHANGE_CONFIRMED")

        confidence = "HIGH" if self.config.state_source == "INTERVAL_MEAN_V_N" else "MEDIUM"
        emission = self._build(
            numerical, v_raw, v, v1, v2, projected_v, activity,
            phase, transition, confidence, raw_color, tuple(reasons), color,
        )
        return emission, VolumePolicyState(color=color, pending_color=pending_color, pending_count=pending_count)

    def _phase(self, v1: float, v2: float) -> str:
        epsilon = self.config.epsilon
        if abs(v1) <= epsilon:
            return "ACTIVITY_STATIONARY"
        if v1 > 0:
            return "ACTIVITY_INCREASING_ACCELERATING" if v2 > epsilon else "ACTIVITY_INCREASING_DECELERATING"
        return "ACTIVITY_DECREASING_ACCELERATING" if v2 < -epsilon else "ACTIVITY_DECREASING_DECELERATING"

    def _build(
        self,
        numerical: Mapping[str, object],
        v_raw: float,
        v: float,
        v1: float,
        v2: float,
        projected_v: float,
        activity: float,
        phase: str,
        transition: str,
        confidence: str,
        raw_color: str,
        reasons: tuple[str, ...],
        color: str = "INVALID",
    ) -> VolumeEmission:
        return VolumeEmission(
            symbol="SPY", timestamp=str(numerical["timestamp"]), engine="V",
            v_raw=v_raw, v=v, v1=v1, v2=v2, projected_v=projected_v,
            projected_v1=None, projected_v2=None, activity_state_value=activity,
            phase=phase, transition_state=transition, confidence_state=confidence,
            domain_state="CAUSAL_LOCAL_VOLUME", raw_color=raw_color,
            cockpit_color=color, reason_codes=tuple(dict.fromkeys(reasons)),
        )
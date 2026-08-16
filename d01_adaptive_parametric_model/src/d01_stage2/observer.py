from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np


@dataclass(frozen=True)
class Geometry:
    requested_minutes: float
    actual_minutes: float
    overshoot_minutes: float
    displacement: float
    slope: float
    quadratic_slope: float | None
    acceleration: float | None
    path_length: float
    efficiency: float
    normalized_deviation: float
    max_signed_progress: float | None
    terminal_signed_progress: float | None
    category: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Duration:
    censor_type: str
    lower: float
    upper: float | None


def direction_claim(velocity: float, acceleration: float, level: float) -> int:
    for value in (velocity, acceleration, level):
        if value > 0:
            return 1
        if value < 0:
            return -1
    return 0


def compatibility(direction: int, displacement: float, slope: float) -> str:
    if direction == 0:
        return "AMBIGUOUS/INCONCLUSIVE"
    dy, db = direction * displacement, direction * slope
    if dy > 0 and db > 0:
        return "CONTINUATION"
    if dy >= 0 and db <= 0:
        return "WEAKENING"
    if dy < 0 and db < 0:
        return "REVERSAL"
    return "AMBIGUOUS/INCONCLUSIVE"


def observe_geometry(anchor_close: float, future_minutes: list[float], future_closes: list[float], direction: int, requested_minutes: float) -> Geometry:
    if anchor_close <= 0 or not future_minutes or len(future_minutes) != len(future_closes):
        raise ValueError("INVALID_OBSERVER_INPUT")
    x = np.asarray(future_minutes, dtype=float)
    y = np.log(np.asarray(future_closes, dtype=float) / anchor_close)
    denominator = float(np.dot(x, x))
    slope = float(np.dot(x, y) / denominator)
    quadratic_slope = acceleration = None
    if len(x) >= 2:
        design = np.column_stack((x, 0.5 * x * x))
        coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
        if rank == 2:
            quadratic_slope, acceleration = map(float, coefficients)
    increments = np.diff(np.concatenate(([0.0], y)))
    path_length = float(np.abs(increments).sum())
    endpoint = float(y[-1])
    efficiency = 0.0 if path_length == 0.0 else abs(endpoint) / path_length
    residual = y - slope * x
    deviation = 0.0 if path_length == 0.0 else float(np.sqrt(np.mean(residual * residual)) / path_length)
    signed = direction * y if direction else None
    return Geometry(
        requested_minutes=requested_minutes, actual_minutes=float(x[-1]),
        overshoot_minutes=float(x[-1] - requested_minutes), displacement=endpoint, slope=slope,
        quadratic_slope=quadratic_slope, acceleration=acceleration, path_length=path_length,
        efficiency=efficiency, normalized_deviation=deviation,
        max_signed_progress=None if signed is None else float(np.max(signed)),
        terminal_signed_progress=None if signed is None else float(signed[-1]),
        category=compatibility(direction, endpoint, slope),
    )


def validity_duration(anchor_close: float, future_minutes: list[float], future_closes: list[float], direction: int, gap_flags: list[bool] | None = None) -> Duration:
    if direction == 0:
        return Duration("INCONCLUSIVE", 0.0, None)
    gaps = gap_flags or [False] * len(future_minutes)
    last_compatible = 0.0
    for end in range(1, len(future_minutes) + 1):
        geometry = observe_geometry(anchor_close, future_minutes[:end], future_closes[:end], direction, future_minutes[end - 1])
        if geometry.category == "REVERSAL":
            if gaps[end - 1]:
                return Duration("INTERVAL", last_compatible, future_minutes[end - 1])
            return Duration("EXACT", future_minutes[end - 1], future_minutes[end - 1])
        last_compatible = future_minutes[end - 1]
    return Duration("RIGHT", last_compatible, None)


def ambiguity_index(efficiency: float | None, deviation: float | None, category: str | None) -> float | None:
    if efficiency is None or deviation is None or category is None:
        return None
    if not (math.isfinite(efficiency) and math.isfinite(deviation)):
        return None
    incidence = 1.0 if category == "AMBIGUOUS/INCONCLUSIVE" else 0.0
    return ((1.0 - efficiency) + deviation / (1.0 + deviation) + incidence) / 3.0


def transition_magnitude(displacement: float, slope: float, horizon_minutes: float) -> float:
    return math.hypot(displacement, horizon_minutes * slope)
from __future__ import annotations

from collections import deque
import math

from aptf_d01.temporal.decay import half_life_decay


class RelativeVolumeEstimator:
    def __init__(self, method: str = "half_life_weighted_mean", window: int = 20, half_life_seconds: float = 45.0) -> None:
        self.method = method
        self.window = window
        self.half_life_seconds = half_life_seconds
        self._history: deque[tuple[float, float]] = deque(maxlen=window)

    def baseline(self, now: float) -> float:
        if not self._history:
            return 1.0
        values = [v for _, v in self._history]
        if self.method == "rolling_mean":
            return max(1e-9, sum(values) / len(values))
        if self.method == "rolling_median":
            sorted_vals = sorted(values)
            mid = len(sorted_vals) // 2
            if len(sorted_vals) % 2 == 1:
                return max(1e-9, sorted_vals[mid])
            return max(1e-9, 0.5 * (sorted_vals[mid - 1] + sorted_vals[mid]))

        weights = [half_life_decay(max(0.0, now - ts), self.half_life_seconds) for ts, _ in self._history]
        total_w = sum(weights)
        if total_w <= 0:
            return max(1e-9, values[-1])
        return max(1e-9, sum(w * v for w, v in zip(weights, values)) / total_w)

    def update(self, now: float, volume: float) -> tuple[float, float]:
        base = self.baseline(now)
        rv = max(0.0, volume / base)
        self._history.append((now, volume))
        return rv, math.log1p(rv)

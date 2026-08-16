from __future__ import annotations


def uncertainty_calibration_proxy(uncertainty: list[float], absolute_error: list[float]) -> float:
    if not uncertainty:
        return 0.0
    return sum(abs(u - min(1.0, e * 20.0)) for u, e in zip(uncertainty, absolute_error)) / len(uncertainty)

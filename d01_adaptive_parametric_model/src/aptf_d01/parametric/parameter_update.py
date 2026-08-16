from __future__ import annotations

import numpy as np


def bounded_online_gradient_update(
    weights: np.ndarray,
    x: np.ndarray,
    target: float,
    prediction: float,
    learning_rate: float,
    l2_regularization: float,
    weight_clip: float,
) -> tuple[np.ndarray, float]:
    error = target - prediction
    grad = -error * x + l2_regularization * weights
    new_weights = weights - learning_rate * grad
    new_weights = np.clip(new_weights, -weight_clip, weight_clip)
    return new_weights, float(error)

from __future__ import annotations

import numpy as np


def linear_predict(weights: np.ndarray, x: np.ndarray) -> float:
    return float(weights @ x)

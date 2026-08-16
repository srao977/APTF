from __future__ import annotations


def polynomial_basis(inputs: dict[str, float], order: int, interaction_max_order: int = 1) -> dict[str, float]:
    if order not in (1, 2, 3):
        raise ValueError("order must be one of 1, 2, 3")
    if interaction_max_order not in (1, 2, 3):
        raise ValueError("interaction_max_order must be one of 1, 2, 3")

    out: dict[str, float] = {"bias": 1.0}
    for key, value in inputs.items():
        out[key] = value
        effective_order = min(order, interaction_max_order) if "_x_" in key else order
        if effective_order >= 2:
            out[f"{key}^2"] = value * value
        if effective_order >= 3:
            out[f"{key}^3"] = value * value * value
    return out

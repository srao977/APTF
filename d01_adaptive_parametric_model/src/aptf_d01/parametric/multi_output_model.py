from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .parameter_update import bounded_online_gradient_update


@dataclass
class MultiOutputConfig:
    learning_rate: float
    l2_regularization: float
    weight_clip: float
    output_overrides: dict[str, dict[str, float]] | None = None


class MultiOutputModel:
    def __init__(self, outputs: list[str], feature_names: list[str], config: MultiOutputConfig) -> None:
        self.outputs = outputs
        self.feature_names = feature_names
        self.config = config
        self._weights = {o: np.zeros(len(feature_names), dtype=float) for o in outputs}

    def _cfg_for(self, output_channel: str) -> tuple[float, float, float]:
        lr = self.config.learning_rate
        reg = self.config.l2_regularization
        clip = self.config.weight_clip
        overrides = self.config.output_overrides or {}
        if output_channel in overrides:
            ov = overrides[output_channel]
            lr = float(ov.get("learning_rate", lr))
            reg = float(ov.get("l2_regularization", reg))
            clip = float(ov.get("weight_clip", clip))
        return lr, reg, clip

    def predict(self, x: np.ndarray) -> dict[str, float]:
        return {name: float(self._weights[name] @ x) for name in self.outputs}

    def update(self, x: np.ndarray, targets: dict[str, float]) -> dict[str, dict[str, float]]:
        change_log: dict[str, dict[str, float]] = {}
        for out in self.outputs:
            old = self._weights[out].copy()
            pred = float(old @ x)
            learning_rate, l2_regularization, weight_clip = self._cfg_for(out)
            new, error = bounded_online_gradient_update(
                old,
                x,
                target=float(targets.get(out, 0.0)),
                prediction=pred,
                learning_rate=learning_rate,
                l2_regularization=l2_regularization,
                weight_clip=weight_clip,
            )
            self._weights[out] = new
            drift = float(np.abs(new - old).sum())
            change_log[out] = {
                "old_l1": float(np.abs(old).sum()),
                "new_l1": float(np.abs(new).sum()),
                "delta_l1": float(np.abs(new - old).sum()),
                "error": error,
                "drift": drift,
            }
        return change_log

    def update_detailed(self, x: np.ndarray, targets: dict[str, float]) -> dict[str, dict[str, Any]]:
        detail: dict[str, dict[str, Any]] = {}
        for out in self.outputs:
            old = self._weights[out].copy()
            pred = float(old @ x)
            target = float(targets.get(out, 0.0))
            learning_rate, l2_regularization, weight_clip = self._cfg_for(out)
            error = target - pred
            grad = -error * x + l2_regularization * old
            proposed = old - learning_rate * grad
            new = np.clip(proposed, -weight_clip, weight_clip)
            bound_hit = bool(np.any(new != proposed))
            delta = new - old
            self._weights[out] = new
            detail[out] = {
                "prediction": pred,
                "target": target,
                "error": error,
                "gradient": grad,
                "grad_abs_max": float(np.max(np.abs(grad))) if grad.size else 0.0,
                "learning_rate": learning_rate,
                "l2_regularization": l2_regularization,
                "weight_clip": weight_clip,
                "weights_pre": old,
                "weights_post": new,
                "delta": delta,
                "parameter_bound_hit": bound_hit,
                "old_l1": float(np.abs(old).sum()),
                "new_l1": float(np.abs(new).sum()),
                "delta_l1": float(np.abs(delta).sum()),
                "drift": float(np.abs(delta).sum()),
            }
        return detail

    def summarize(self) -> dict[str, float]:
        return {k: float(np.abs(v).sum()) for k, v in self._weights.items()}

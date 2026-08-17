from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from aptf_d04.models.envelope_context import EnvelopeContext
from d02.v02.models import ForwardSample, PathDirection, ReturnShape


@dataclass
class Observation:
    scenario_time: float
    return_shape: ReturnShape
    context: EnvelopeContext
    expected: dict


class SyntheticGenerator:
    def __init__(self, scenario_data: dict) -> None:
        self.scenario_data = scenario_data

    def generate(self) -> list[Observation]:
        observations: list[Observation] = []
        entity_id = self.scenario_data["entity_id"]
        shape_defaults = self.scenario_data["shape_defaults"]
        context_defaults = self.scenario_data["context_defaults"]
        for step in self.scenario_data["steps"]:
            shape_values = {**shape_defaults, **step.get("shape", {})}
            context_values = {**context_defaults, **step.get("context", {})}
            model_time = float(step["scenario_time"])
            rs = self._return_shape(entity_id, model_time, shape_values)
            ctx = EnvelopeContext(evaluation_time=model_time, **context_values)
            observations.append(
                Observation(
                    scenario_time=float(step["scenario_time"]),
                    return_shape=rs,
                    context=ctx,
                    expected=step.get("expected", {}),
                )
            )
        return observations

    @staticmethod
    def _return_shape(entity_id: str, model_time: float, values: dict) -> ReturnShape:
        current_level = float(values.get("current_level", 0.0))
        interval = float(values.get("projection_interval", 30.0))
        half_life = float(values.get("forward_half_life", 60.0))
        terminal = float(values["terminal_displacement"])
        maximum = float(values["maximum_absolute_displacement"])
        if maximum < abs(terminal):
            raise ValueError("maximum_absolute_displacement cannot be smaller than terminal displacement")
        if terminal > 0.0:
            direction = PathDirection.UPWARD
            excursion = maximum
        elif terminal < 0.0:
            direction = PathDirection.DOWNWARD
            excursion = -maximum
        else:
            direction = PathDirection.FLAT
            excursion = maximum
        strength = float(values["strength"])
        persistence = float(values["persistence"])
        uncertainty = float(values["uncertainty"])
        reversal = float(values["reversal_propensity"])
        samples = (
            ForwardSample(
                tau=interval / 2.0,
                level=current_level + excursion,
                velocity=0.0,
                uncertainty=uncertainty,
                strength=strength,
                persistence=persistence,
                reversal_propensity=reversal,
            ),
            ForwardSample(
                tau=interval,
                level=current_level + terminal,
                velocity=0.0,
                uncertainty=uncertainty,
                strength=strength,
                persistence=persistence,
                reversal_propensity=reversal,
            ),
        )
        return ReturnShape(
            model_time=model_time,
            entity_id=entity_id,
            source_model_version="0.2",
            current_level=current_level,
            projection_interval=interval,
            forward_half_life=half_life,
            forward_samples=samples,
            terminal_displacement=terminal,
            maximum_absolute_displacement=maximum,
            path_direction=direction,
            terminal_decay_factor=2.0 ** (-interval / half_life),
            strength=strength,
            coherence=float(values["coherence"]),
            persistence=persistence,
            uncertainty=uncertainty,
            reversal_propensity=reversal,
            state_support_ratio=float(values["state_support_ratio"]),
        )

    def checksum(self) -> str:
        canonical = json.dumps(self.scenario_data, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

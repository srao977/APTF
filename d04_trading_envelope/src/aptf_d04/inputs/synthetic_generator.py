from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.return_shape import ReturnShape


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
        for step in self.scenario_data["steps"]:
            rs = ReturnShape(**step["return_shape"])
            ctx = EnvelopeContext(**step["envelope_context"])
            observations.append(
                Observation(
                    scenario_time=float(step["scenario_time"]),
                    return_shape=rs,
                    context=ctx,
                    expected=step.get("expected", {}),
                )
            )
        return observations

    def checksum(self) -> str:
        canonical = json.dumps(self.scenario_data, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

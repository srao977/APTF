from __future__ import annotations

from typing import Iterable

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.models.normalized_observation import NormalizedObservation


def run_replay(model: AdaptiveParametricModel, observations: Iterable[NormalizedObservation]) -> list[tuple]:
    rows = []
    for obs in observations:
        model_time = obs.model_available_timestamp
        dmo, fmo, change = model.step(obs, model_time=model_time)
        rows.append((obs, dmo, fmo, change))
    return rows

from __future__ import annotations

from d01.v02.outputs import DMOOutput, FMOSample, FMOOutput


def make_dmo(**updates) -> DMOOutput:
    values = {
        "model_time": 100.0,
        "entity_id": "TEST:D02",
        "model_version": "0.2",
        "state_level": 1.0,
        "state_velocity": 0.1,
        "state_acceleration": 0.01,
        "state_curvature": 0.01,
        "strength": 0.8,
        "coherence": 0.7,
        "persistence": 0.6,
        "perturbation_magnitude": 0.2,
        "perturbation_class": "NONE",
        "uncertainty": 0.3,
        "reversal_propensity": 0.25,
        "state_support_ratio": 0.9,
        "observation_half_life": 120.0,
        "forward_half_life": 60.0,
        "parameter_state": {},
        "parameter_update_magnitude": {},
        "data_quality": 1.0,
        "model_health": "OK",
        "dmo_schema_version": "0.2",
        "fmo_schema_version": "0.2",
        "config_hash": "config",
        "state_hash": "state",
        "trace_id": "trace",
    }
    values.update(updates)
    return DMOOutput(**values)


def sample(tau: float, level: float) -> FMOSample:
    return FMOSample(
        tau=tau,
        level=level,
        velocity=0.1,
        uncertainty=0.3,
        strength=0.8,
        persistence=0.6,
        reversal_propensity=0.25,
    )


def make_fmo(levels=(1.1, 1.2, 1.3), **updates) -> FMOOutput:
    interval = float(len(levels) * 10)
    values = {
        "model_time": 100.0,
        "entity_id": "TEST:D02",
        "interval_length": interval,
        "samples": [sample(float((index + 1) * 10), level) for index, level in enumerate(levels)],
    }
    values.update(updates)
    return FMOOutput(**values)
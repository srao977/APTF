from __future__ import annotations

from dataclasses import dataclass

from aptf_d01.models.forward_model_output import ForwardModelOutput


@dataclass(frozen=True)
class FMOCaptureRecord:
    capture_id: str
    entity_id: str
    model_time: float
    parameter_state_version: int
    forward_interval_start: float
    forward_interval_end: float
    directional_support: float
    expected_magnitude: float
    expected_persistence: float
    uncertainty: float
    favorable_excursion_estimate: float
    adverse_excursion_estimate: float


class FMOCapture:
    def __init__(self) -> None:
        self.counter = 0

    def capture(self, fmo: ForwardModelOutput, parameter_state_version: int) -> FMOCaptureRecord:
        self.counter += 1
        return FMOCaptureRecord(
            capture_id=f"C-{self.counter:08d}",
            entity_id=fmo.entity_id,
            model_time=fmo.model_time,
            parameter_state_version=parameter_state_version,
            forward_interval_start=fmo.forward_interval_start,
            forward_interval_end=fmo.forward_interval_end,
            directional_support=fmo.directional_support,
            expected_magnitude=fmo.expected_magnitude,
            expected_persistence=fmo.expected_persistence,
            uncertainty=fmo.uncertainty,
            favorable_excursion_estimate=fmo.favorable_excursion_estimate,
            adverse_excursion_estimate=fmo.adverse_excursion_estimate,
        )

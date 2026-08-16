from __future__ import annotations

from aptf_d01.models.adaptive_signal import AdaptiveSignal
from aptf_d01.signals.density import signal_density
from aptf_d01.signals.strength import signal_strength


class AdaptiveSignalEstimator:
    def __init__(self) -> None:
        self.counter = 0

    def build(
        self,
        entity_id: str,
        timestamp: float,
        half_life_seconds: float,
        reinforcement: float,
        uncertainty: float,
        effective_mass: float,
        movement_abs: float,
        directional_coherence: float,
    ) -> AdaptiveSignal:
        self.counter += 1
        strength = signal_strength(effective_mass, movement_abs, directional_coherence)
        density = signal_density(effective_mass, max(1.0, half_life_seconds))
        return AdaptiveSignal(
            signal_id=f"S-{self.counter:08d}",
            entity_id=entity_id,
            signal_type="ADAPTIVE",
            strength=strength,
            half_life_seconds=half_life_seconds,
            reinforcement=reinforcement,
            uncertainty=uncertainty,
            effective_mass=effective_mass,
            density=density,
            created_at=timestamp,
            updated_at=timestamp,
            version=self.counter,
            active=True,
        )

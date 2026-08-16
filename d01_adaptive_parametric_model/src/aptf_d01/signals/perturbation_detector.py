from __future__ import annotations

from dataclasses import dataclass

from aptf_d01.models.enums import PerturbationType
from aptf_d01.models.perturbation import Perturbation


@dataclass
class PerturbationThresholds:
    displacement_threshold: float
    velocity_threshold: float
    acceleration_threshold: float
    rv_threshold: float
    volume_density_threshold: float
    spread_change_threshold: float


class PerturbationDetector:
    def __init__(self, thresholds: PerturbationThresholds) -> None:
        self.thresholds = thresholds
        self.counter = 0

    def detect(
        self,
        entity_id: str,
        timestamp: float,
        displacement: float,
        velocity: float,
        acceleration: float,
        relative_volume: float,
        volume_density: float,
        spread_change: float,
    ) -> Perturbation:
        reasons: list[str] = []
        if abs(displacement) >= self.thresholds.displacement_threshold:
            reasons.append("DISPLACEMENT")
        if abs(velocity) >= self.thresholds.velocity_threshold:
            reasons.append("VELOCITY")
        if abs(acceleration) >= self.thresholds.acceleration_threshold:
            reasons.append("ACCELERATION")
        if relative_volume >= self.thresholds.rv_threshold:
            reasons.append("RV")
        if volume_density >= self.thresholds.volume_density_threshold:
            reasons.append("VOLUME_DENSITY")
        if abs(spread_change) >= self.thresholds.spread_change_threshold:
            reasons.append("SPREAD")

        magnitude = min(1.0, 0.2 * len(reasons))
        direction = 0.0 if displacement == 0 else (1.0 if displacement > 0 else -1.0)
        p_type = PerturbationType.NONE
        if reasons:
            if any(r in reasons for r in ["RV", "VOLUME_DENSITY"]) and any(
                r in reasons for r in ["DISPLACEMENT", "VELOCITY", "ACCELERATION"]
            ):
                p_type = PerturbationType.COMBINED
            elif any(r in reasons for r in ["RV", "VOLUME_DENSITY"]):
                p_type = PerturbationType.VOLUME
            else:
                p_type = PerturbationType.PRICE

        self.counter += 1
        return Perturbation(
            perturbation_id=f"P-{self.counter:08d}",
            entity_id=entity_id,
            timestamp=timestamp,
            magnitude=magnitude,
            direction=direction,
            type=p_type,
            confidence=min(1.0, 0.4 + magnitude),
            affected_channels=["price", "volume"] if reasons else [],
            reason_codes=reasons,
        )

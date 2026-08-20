from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MarketObservation:
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    session: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PriceEmission:
    symbol: str
    timestamp: str
    engine: str
    p: float
    p1: float
    p2: float
    projected_p: float
    projected_p1: float
    projected_p2: float
    delta_projected_p: float
    delta_projected_p1: float
    delta_projected_p2: float
    current_direction: str
    current_acceleration: str
    projected_direction: str
    projected_acceleration: str
    trajectory_phase: str
    turning_tendency: str
    domain_state: str
    stability_state: str
    confidence_state: str
    raw_color: str
    color: str
    reason_codes: tuple[str, ...]
    rk_success: bool
    condition_number: float
    max_real_eigenvalue: float
    perturbation_amplification: float

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason_codes"] = list(self.reason_codes)
        return payload

from __future__ import annotations

from typing import Mapping

from .contracts import MarketObservation, PriceEmission
from .policy import EmissionPolicy, PolicyState


class PriceEngine:
    def __init__(self, policy: EmissionPolicy):
        self.policy = policy

    def observe(
        self,
        observation: MarketObservation,
        numerical_trajectory: Mapping[str, object],
        policy_state: PolicyState,
    ) -> tuple[PriceEmission, PolicyState]:
        if observation.symbol != "SPY":
            raise ValueError("Test014 PriceEngine accepts SPY observations only")
        if str(numerical_trajectory["timestamp"]) != observation.timestamp:
            raise ValueError("observation and trajectory timestamps differ")
        return self.policy.emit(numerical_trajectory, policy_state)
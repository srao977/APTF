from __future__ import annotations

from dataclasses import dataclass

from .emitter import AdaptiveEmitter
from .models import (
    EmitterDecision,
    ExecutionIntent,
    ImmutableEmission,
    PositionState,
    PositionTransition,
)
from .observation import Observation
from .position import apply_position_decision


@dataclass(frozen=True)
class RuntimeResult:
    emission: ImmutableEmission
    position_transition: PositionTransition | None
    execution_intent: ExecutionIntent
    position_state: PositionState


class RuntimeCore:
    version = "APTF Runtime Core V0.1"

    def __init__(self, entity_id: str, rule_fingerprint: str, code_fingerprint: str) -> None:
        self.entity_id = entity_id
        self.emitter = AdaptiveEmitter(entity_id, rule_fingerprint, code_fingerprint)
        self.position_state = PositionState.FLAT

    def process(self, observation: Observation) -> RuntimeResult:
        emission = self.emitter.process(observation)
        raw_decision = emission["position_decision"]
        if raw_decision is None:
            return RuntimeResult(
                emission=emission,
                position_transition=None,
                execution_intent=ExecutionIntent.NONE,
                position_state=self.position_state,
            )
        transition = apply_position_decision(
            self.position_state,
            EmitterDecision(raw_decision),
        )
        self.position_state = transition.state_after
        return RuntimeResult(
            emission=emission,
            position_transition=transition,
            execution_intent=transition.execution_intent,
            position_state=self.position_state,
        )

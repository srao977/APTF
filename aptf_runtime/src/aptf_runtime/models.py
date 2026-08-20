from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class EmitterDecision(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PositionState(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"


class ExecutionIntent(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"


class EmissionStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACTIONABLE = "ACTIONABLE"


@dataclass(frozen=True)
class EmitterState:
    completed_count: int = 0
    previous_decision: EmitterDecision | None = None
    legacy_internal_controller_state: str = "FLAT"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class ImmutableEmission:
    _payload: Mapping[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ImmutableEmission":
        return cls(_freeze(payload))

    def as_dict(self) -> dict[str, Any]:
        return _thaw(self._payload)

    def __getitem__(self, key: str) -> Any:
        return self._payload[key]


@dataclass(frozen=True)
class PositionTransition:
    state_before: PositionState
    emitter_decision: EmitterDecision
    state_after: PositionState
    structural_classification: str
    execution_intent: ExecutionIntent

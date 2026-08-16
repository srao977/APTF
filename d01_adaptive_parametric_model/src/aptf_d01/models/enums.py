from __future__ import annotations

from enum import Enum


class SessionState(str, Enum):
    PRE = "PRE"
    OPEN = "OPEN"
    HALT = "HALT"
    CLOSE = "CLOSE"


class PerturbationType(str, Enum):
    NONE = "NONE"
    PRICE = "PRICE"
    VOLUME = "VOLUME"
    COMBINED = "COMBINED"


class DirectionState(str, Enum):
    DOWN = "DOWN"
    FLAT = "FLAT"
    UP = "UP"

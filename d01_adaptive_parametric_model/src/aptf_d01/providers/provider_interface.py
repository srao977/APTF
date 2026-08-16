from __future__ import annotations

from typing import Protocol

from aptf_d01.models.normalized_observation import NormalizedObservation


class ProviderInterface(Protocol):
    def stream(self) -> list[NormalizedObservation]:
        ...

from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Mapping


CONTEXT_LENGTH = 15


class RollingContext:
    def __init__(self) -> None:
        self._records: deque[dict[str, Any]] = deque(maxlen=CONTEXT_LENGTH)

    def __len__(self) -> int:
        return len(self._records)

    @property
    def ready(self) -> bool:
        return len(self._records) == CONTEXT_LENGTH

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(deepcopy(record) for record in self._records)

    def append_completed(self, record: Mapping[str, Any]) -> None:
        self._records.append(deepcopy(dict(record)))

    @property
    def observation_ids(self) -> tuple[str, ...]:
        return tuple(record["observation_id"] for record in self._records)

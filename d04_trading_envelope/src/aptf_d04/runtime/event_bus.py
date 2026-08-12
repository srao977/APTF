from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from aptf_d04.models.events import Event
from aptf_d04.models.enums import EventType


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        for callback in self._subscribers.get(event.event_type, []):
            callback(event)

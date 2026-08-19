from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from .identity import new_runtime_identity


class Clock(Protocol):
    runtime_instance_id: str
    clock_domain_id: str

    def utc_now(self) -> datetime: ...

    def monotonic_ns(self) -> int: ...


class SystemClock:
    def __init__(
        self,
        *,
        runtime_instance_id: str | None = None,
        clock_domain_id: str | None = None,
    ) -> None:
        self.runtime_instance_id = runtime_instance_id or new_runtime_identity()
        self.clock_domain_id = clock_domain_id or new_runtime_identity()

    def utc_now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic_ns(self) -> int:
        return time.perf_counter_ns()


@dataclass(frozen=True)
class TimingStart:
    received_at_utc: datetime
    received_monotonic_ns: int
    runtime_instance_id: str
    clock_domain_id: str


@dataclass(frozen=True)
class TimingResult:
    received_at_utc: datetime
    emitted_at_utc: datetime
    received_monotonic_ns: int
    emitted_monotonic_ns: int
    processing_duration_ns: int
    runtime_instance_id: str
    clock_domain_id: str
    telemetry_flags: tuple[str, ...]


def require_aware_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC telemetry timestamps must be timezone-aware")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError("UTC telemetry timestamps must have zero UTC offset")


def format_utc(value: datetime) -> str:
    require_aware_utc(value)
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def begin_timing(clock: Clock) -> TimingStart:
    received_at = clock.utc_now()
    require_aware_utc(received_at)
    received_monotonic = clock.monotonic_ns()
    return TimingStart(
        received_at_utc=received_at,
        received_monotonic_ns=received_monotonic,
        runtime_instance_id=clock.runtime_instance_id,
        clock_domain_id=clock.clock_domain_id,
    )


def end_timing(clock: Clock, start: TimingStart) -> TimingResult:
    if clock.runtime_instance_id != start.runtime_instance_id:
        raise ValueError("runtime_instance_id changed within one stage measurement")
    if clock.clock_domain_id != start.clock_domain_id:
        raise ValueError("cross-clock-domain monotonic subtraction is prohibited")
    emitted_monotonic = clock.monotonic_ns()
    emitted_at = clock.utc_now()
    require_aware_utc(emitted_at)
    duration = emitted_monotonic - start.received_monotonic_ns
    if duration < 0:
        raise ValueError("monotonic processing duration cannot be negative")
    flags = ("WALL_CLOCK_INVERSION",) if emitted_at < start.received_at_utc else ()
    return TimingResult(
        received_at_utc=start.received_at_utc,
        emitted_at_utc=emitted_at,
        received_monotonic_ns=start.received_monotonic_ns,
        emitted_monotonic_ns=emitted_monotonic,
        processing_duration_ns=duration,
        runtime_instance_id=start.runtime_instance_id,
        clock_domain_id=start.clock_domain_id,
        telemetry_flags=flags,
    )

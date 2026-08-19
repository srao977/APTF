from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from .canonical_json import normalize_semantic
from .clock import format_utc, require_aware_utc


_EVENT_ID = re.compile(r"^aptf:evt:v1:sha256:[0-9a-f]{64}$")
_OBSERVATION_ID = re.compile(r"^aptf:obs:v1:sha256:[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMPONENTS = {
    "SOURCE_GATEWAY",
    "D01",
    "D02",
    "D04",
    "D03",
    "POSITION_TRANSITION_CONTROLLER",
}
_TIME_ROLES = {
    "BAR_OPEN",
    "BAR_CLOSE",
    "PROVIDER_EVENT",
    "SAMPLE",
    "INSTANTANEOUS_EVENT",
    "OTHER",
}
_FLAGS = {"WALL_CLOCK_INVERSION"}


def _require_uuid4(value: str, field_name: str) -> None:
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be canonical UUIDv4 text") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise ValueError(f"{field_name} must be canonical UUIDv4 text")


def _freeze(value: Any) -> Any:
    normalized = normalize_semantic(value)
    if isinstance(normalized, dict):
        return MappingProxyType({key: _freeze(item) for key, item in normalized.items()})
    if isinstance(normalized, list):
        return tuple(_freeze(item) for item in normalized)
    return normalized


@dataclass(frozen=True)
class ErrorInfo:
    error_type: str
    error_code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "error_type": self.error_type,
            "error_code": self.error_code,
            "message": self.message,
        }


@dataclass(frozen=True)
class TemporalEventEnvelope:
    schema_version: str
    event_id: str
    observation_id: str
    execution_id: str
    parent_event_id: str | None
    logical_output_ordinal: int
    source_stream_id: str
    sequence_number: int
    instrument_id: str
    market_event_time_utc: str
    market_event_time_role: str
    producer_component: str
    producer_version: str
    runtime_instance_id: str
    clock_domain_id: str
    received_at_utc: datetime
    emitted_at_utc: datetime
    received_monotonic_ns: int
    emitted_monotonic_ns: int
    processing_duration_ns: int
    telemetry_flags: tuple[str, ...]
    status: str
    payload_type: str
    payload_version: str
    payload_sha256: str | None
    scientific_ids: Mapping[str, str | int | float | None]
    payload: Any
    error: ErrorInfo | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "telemetry_flags", tuple(self.telemetry_flags))
        object.__setattr__(self, "scientific_ids", _freeze(self.scientific_ids))
        object.__setattr__(self, "payload", _freeze(self.payload))
        if self.schema_version != "0.2":
            raise ValueError("schema_version must be 0.2")
        if not _EVENT_ID.fullmatch(self.event_id):
            raise ValueError("invalid event_id")
        if not _OBSERVATION_ID.fullmatch(self.observation_id):
            raise ValueError("invalid observation_id")
        _require_uuid4(self.execution_id, "execution_id")
        _require_uuid4(self.runtime_instance_id, "runtime_instance_id")
        _require_uuid4(self.clock_domain_id, "clock_domain_id")
        if self.parent_event_id is not None and not _EVENT_ID.fullmatch(self.parent_event_id):
            raise ValueError("invalid parent_event_id")
        if self.producer_component == "SOURCE_GATEWAY" and self.parent_event_id is not None:
            raise ValueError("source event parent must be null")
        if self.producer_component != "SOURCE_GATEWAY" and self.parent_event_id is None:
            raise ValueError("derived event parent is required")
        if self.logical_output_ordinal < 0 or self.sequence_number < 0:
            raise ValueError("ordinals and sequence_number must be nonnegative")
        if not self.source_stream_id or not self.instrument_id:
            raise ValueError("source_stream_id and instrument_id are required")
        if not self.market_event_time_utc.endswith("Z"):
            raise ValueError("market_event_time_utc must be canonical UTC text")
        datetime.fromisoformat(self.market_event_time_utc.replace("Z", "+00:00"))
        if self.market_event_time_role not in _TIME_ROLES:
            raise ValueError("invalid market_event_time_role")
        if self.producer_component not in _COMPONENTS:
            raise ValueError("invalid producer_component")
        require_aware_utc(self.received_at_utc)
        require_aware_utc(self.emitted_at_utc)
        if self.received_monotonic_ns < 0 or self.emitted_monotonic_ns < 0:
            raise ValueError("monotonic samples must be nonnegative")
        if self.processing_duration_ns != self.emitted_monotonic_ns - self.received_monotonic_ns:
            raise ValueError("processing_duration_ns must equal same-envelope monotonic subtraction")
        if self.processing_duration_ns < 0:
            raise ValueError("processing_duration_ns must be nonnegative")
        if len(set(self.telemetry_flags)) != len(self.telemetry_flags):
            raise ValueError("telemetry_flags must be unique")
        if not set(self.telemetry_flags).issubset(_FLAGS):
            raise ValueError("unknown telemetry flag")
        expected_inversion = self.emitted_at_utc < self.received_at_utc
        if expected_inversion != ("WALL_CLOCK_INVERSION" in self.telemetry_flags):
            raise ValueError("wall-clock inversion flag does not match UTC samples")
        if self.status == "SUCCESS":
            if self.error is not None or self.payload_sha256 is None:
                raise ValueError("SUCCESS requires payload hash and null error")
            if not _SHA256.fullmatch(self.payload_sha256):
                raise ValueError("invalid payload_sha256")
        elif self.status == "ERROR":
            if self.error is None or self.payload is not None or self.payload_sha256 is not None:
                raise ValueError("ERROR requires typed error and null payload/hash")
        else:
            raise ValueError("status must be SUCCESS or ERROR")

    def validate_child_of(self, parent: "TemporalEventEnvelope") -> None:
        inherited = (
            "observation_id",
            "source_stream_id",
            "sequence_number",
            "instrument_id",
            "market_event_time_utc",
            "market_event_time_role",
        )
        for field_name in inherited:
            if getattr(self, field_name) != getattr(parent, field_name):
                raise ValueError(f"child changed inherited field: {field_name}")
        if self.parent_event_id != parent.event_id:
            raise ValueError("child parent_event_id mismatch")

    @property
    def processing_duration_us(self) -> float:
        return self.processing_duration_ns / 1_000.0

    @property
    def processing_duration_ms(self) -> float:
        return self.processing_duration_ns / 1_000_000.0

    def as_dict(self, *, distributed: bool = False) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "observation_id": self.observation_id,
            "execution_id": self.execution_id,
            "parent_event_id": self.parent_event_id,
            "logical_output_ordinal": self.logical_output_ordinal,
            "source_stream_id": self.source_stream_id,
            "sequence_number": self.sequence_number,
            "instrument_id": self.instrument_id,
            "market_event_time_utc": self.market_event_time_utc,
            "market_event_time_role": self.market_event_time_role,
            "producer_component": self.producer_component,
            "producer_version": self.producer_version,
            "runtime_instance_id": self.runtime_instance_id,
            "clock_domain_id": self.clock_domain_id,
            "received_at_utc": format_utc(self.received_at_utc),
            "emitted_at_utc": format_utc(self.emitted_at_utc),
            "received_monotonic_ns": None if distributed else self.received_monotonic_ns,
            "emitted_monotonic_ns": None if distributed else self.emitted_monotonic_ns,
            "processing_duration_ns": self.processing_duration_ns,
            "telemetry_flags": list(self.telemetry_flags),
            "status": self.status,
            "payload_type": self.payload_type,
            "payload_version": self.payload_version,
            "payload_sha256": self.payload_sha256,
            "scientific_ids": normalize_semantic(self.scientific_ids),
            "payload": normalize_semantic(self.payload),
            "error": None if self.error is None else self.error.as_dict(),
        }

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from .canonical_json import canonical_sha256, normalize_semantic
from .clock import Clock, begin_timing, end_timing
from .identity import event_id, new_execution_id, observation_id
from .temporal_envelope import ErrorInfo, TemporalEventEnvelope


T = TypeVar("T")


@dataclass(frozen=True)
class StageResult(Generic[T]):
    output: T
    envelope: TemporalEventEnvelope


class StageExecutionError(RuntimeError):
    def __init__(self, envelope: TemporalEventEnvelope, cause: BaseException) -> None:
        super().__init__(str(cause))
        self.envelope = envelope
        self.cause = cause


def _success_envelope(
    *,
    execution_id_value: str,
    parent: TemporalEventEnvelope | None,
    source_stream_id: str,
    sequence_number: int,
    instrument_id: str,
    market_event_time_utc: str,
    market_event_time_role: str,
    observation_id_value: str,
    producer_component: str,
    producer_version: str,
    payload_type: str,
    payload_version: str,
    payload: Any,
    scientific_ids: dict[str, str | int | float | None],
    timing: Any,
) -> TemporalEventEnvelope:
    normalized = normalize_semantic(payload)
    payload_hash = canonical_sha256(normalized)
    parent_id = None if parent is None else parent.event_id
    logical_id = event_id(
        observation_id_value=observation_id_value,
        parent_event_id=parent_id,
        producer_component=producer_component,
        producer_version=producer_version,
        logical_output_ordinal=0,
        status="SUCCESS",
        payload_type=payload_type,
        payload_version=payload_version,
        payload_sha256=payload_hash,
    )
    envelope = TemporalEventEnvelope(
        schema_version="0.2",
        event_id=logical_id,
        observation_id=observation_id_value,
        execution_id=execution_id_value,
        parent_event_id=parent_id,
        logical_output_ordinal=0,
        source_stream_id=source_stream_id,
        sequence_number=sequence_number,
        instrument_id=instrument_id,
        market_event_time_utc=market_event_time_utc,
        market_event_time_role=market_event_time_role,
        producer_component=producer_component,
        producer_version=producer_version,
        runtime_instance_id=timing.runtime_instance_id,
        clock_domain_id=timing.clock_domain_id,
        received_at_utc=timing.received_at_utc,
        emitted_at_utc=timing.emitted_at_utc,
        received_monotonic_ns=timing.received_monotonic_ns,
        emitted_monotonic_ns=timing.emitted_monotonic_ns,
        processing_duration_ns=timing.processing_duration_ns,
        telemetry_flags=timing.telemetry_flags,
        status="SUCCESS",
        payload_type=payload_type,
        payload_version=payload_version,
        payload_sha256=payload_hash,
        scientific_ids=scientific_ids,
        payload=normalized,
        error=None,
    )
    if parent is not None:
        envelope.validate_child_of(parent)
    return envelope


def create_source_event(
    *,
    clock: Clock,
    source_stream_id: str,
    sequence_number: int,
    instrument_id: str,
    market_event_time_utc: str,
    market_event_time_role: str,
    payload_type: str,
    payload_version: str,
    source_builder: Callable[[], T],
) -> StageResult[T]:
    execution_id_value = new_execution_id()
    start = begin_timing(clock)
    output = source_builder()
    timing = end_timing(clock, start)
    normalized = normalize_semantic(output)
    payload_hash = canonical_sha256(normalized)
    observation = observation_id(
        source_stream_id=source_stream_id,
        instrument_id=instrument_id,
        sequence_number=sequence_number,
        market_event_time_utc=market_event_time_utc,
        market_event_time_role=market_event_time_role,
        payload_type=payload_type,
        payload_version=payload_version,
        payload_sha256=payload_hash,
    )
    envelope = _success_envelope(
        execution_id_value=execution_id_value,
        parent=None,
        source_stream_id=source_stream_id,
        sequence_number=sequence_number,
        instrument_id=instrument_id,
        market_event_time_utc=market_event_time_utc,
        market_event_time_role=market_event_time_role,
        observation_id_value=observation,
        producer_component="SOURCE_GATEWAY",
        producer_version="0.2",
        payload_type=payload_type,
        payload_version=payload_version,
        payload=normalized,
        scientific_ids={},
        timing=timing,
    )
    return StageResult(output=output, envelope=envelope)


def execute_stage(
    *,
    parent: TemporalEventEnvelope,
    clock: Clock,
    producer_component: str,
    producer_version: str,
    payload_type: str,
    payload_version: str,
    call: Callable[[], T],
    payload_adapter: Callable[[T], Any] = normalize_semantic,
    scientific_id_adapter: Callable[[T], dict[str, str | int | float | None]] = lambda _: {},
    error_code: str = "COMPONENT_EXECUTION_FAILED",
) -> StageResult[T]:
    execution_id_value = new_execution_id()
    start = begin_timing(clock)
    try:
        output = call()
    except Exception as exc:
        timing = end_timing(clock, start)
        info = ErrorInfo(type(exc).__name__, error_code, str(exc)[:500])
        logical_id = event_id(
            observation_id_value=parent.observation_id,
            parent_event_id=parent.event_id,
            producer_component=producer_component,
            producer_version=producer_version,
            logical_output_ordinal=0,
            status="ERROR",
            payload_type=payload_type,
            payload_version=payload_version,
            payload_sha256=None,
            error_type=info.error_type,
            error_code=info.error_code,
        )
        envelope = TemporalEventEnvelope(
            schema_version="0.2",
            event_id=logical_id,
            observation_id=parent.observation_id,
            execution_id=execution_id_value,
            parent_event_id=parent.event_id,
            logical_output_ordinal=0,
            source_stream_id=parent.source_stream_id,
            sequence_number=parent.sequence_number,
            instrument_id=parent.instrument_id,
            market_event_time_utc=parent.market_event_time_utc,
            market_event_time_role=parent.market_event_time_role,
            producer_component=producer_component,
            producer_version=producer_version,
            runtime_instance_id=timing.runtime_instance_id,
            clock_domain_id=timing.clock_domain_id,
            received_at_utc=timing.received_at_utc,
            emitted_at_utc=timing.emitted_at_utc,
            received_monotonic_ns=timing.received_monotonic_ns,
            emitted_monotonic_ns=timing.emitted_monotonic_ns,
            processing_duration_ns=timing.processing_duration_ns,
            telemetry_flags=timing.telemetry_flags,
            status="ERROR",
            payload_type=payload_type,
            payload_version=payload_version,
            payload_sha256=None,
            scientific_ids={},
            payload=None,
            error=info,
        )
        envelope.validate_child_of(parent)
        raise StageExecutionError(envelope, exc) from exc
    timing = end_timing(clock, start)
    payload = payload_adapter(output)
    envelope = _success_envelope(
        execution_id_value=execution_id_value,
        parent=parent,
        source_stream_id=parent.source_stream_id,
        sequence_number=parent.sequence_number,
        instrument_id=parent.instrument_id,
        market_event_time_utc=parent.market_event_time_utc,
        market_event_time_role=parent.market_event_time_role,
        observation_id_value=parent.observation_id,
        producer_component=producer_component,
        producer_version=producer_version,
        payload_type=payload_type,
        payload_version=payload_version,
        payload=payload,
        scientific_ids=scientific_id_adapter(output),
        timing=timing,
    )
    return StageResult(output=output, envelope=envelope)

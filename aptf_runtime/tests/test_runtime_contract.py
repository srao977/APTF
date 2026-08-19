from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from aptf_runtime.canonical_json import canonical_json_text, canonical_sha256
from aptf_runtime.clock import begin_timing, end_timing, require_aware_utc
from aptf_runtime.identity import event_id, observation_id
from aptf_runtime.stage_wrappers import (
    StageExecutionError,
    create_source_event,
    execute_stage,
)


RUNTIME_ID = "11111111-1111-4111-8111-111111111111"
CLOCK_ID = "22222222-2222-4222-8222-222222222222"
T0 = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


class FakeClock:
    def __init__(
        self,
        utc_values: list[datetime],
        monotonic_values: list[int],
        *,
        runtime_instance_id: str = RUNTIME_ID,
        clock_domain_id: str = CLOCK_ID,
    ) -> None:
        self.runtime_instance_id = runtime_instance_id
        self.clock_domain_id = clock_domain_id
        self._utc_values = iter(utc_values)
        self._monotonic_values = iter(monotonic_values)

    def utc_now(self) -> datetime:
        return next(self._utc_values)

    def monotonic_ns(self) -> int:
        return next(self._monotonic_values)


def source_event(*, clock: FakeClock | None = None, sequence: int = 16):
    return create_source_event(
        clock=clock or FakeClock([T0, T0 + timedelta(microseconds=1)], [100, 300]),
        source_stream_id="stream-a",
        sequence_number=sequence,
        instrument_id="SPY",
        market_event_time_utc="2022-09-30T08:16:00Z",
        market_event_time_role="PROVIDER_EVENT",
        payload_type="NormalizedObservationSourceRecord",
        payload_version="v0_1",
        source_builder=lambda: {"close": 366.0, "source_row_number": 17},
    )


def test_canonical_payload_hash_is_semantic_and_rejects_nonfinite() -> None:
    left = {"b": [1, -0.0], "a": True}
    right = {"a": True, "b": [1, 0.0]}
    assert canonical_json_text(left) == '{"a":true,"b":[1,0.0]}'
    assert canonical_sha256(left) == canonical_sha256(right)
    with pytest.raises(ValueError, match="non-finite"):
        canonical_sha256({"bad": float("nan")})


def test_observation_and_logical_ids_are_deterministic_and_collision_resistant() -> None:
    identity = {
        "source_stream_id": "stream-a",
        "instrument_id": "SPY",
        "sequence_number": 16,
        "market_event_time_utc": "2022-09-30T08:16:00Z",
        "market_event_time_role": "PROVIDER_EVENT",
        "payload_type": "source",
        "payload_version": "1",
        "payload_sha256": "a" * 64,
    }
    first = observation_id(**identity)
    assert first == observation_id(**identity)
    assert first != observation_id(**{**identity, "source_stream_id": "stream-b"})
    assert first != observation_id(**{**identity, "sequence_number": 17})

    logical = {
        "observation_id_value": first,
        "parent_event_id": None,
        "producer_component": "SOURCE_GATEWAY",
        "producer_version": "0.2",
        "logical_output_ordinal": 0,
        "status": "SUCCESS",
        "payload_type": "source",
        "payload_version": "1",
        "payload_sha256": "a" * 64,
    }
    assert event_id(**logical) == event_id(**logical)
    assert event_id(**logical) != event_id(**{**logical, "logical_output_ordinal": 1})


def test_schema_local_and_distributed_profiles_and_deep_immutability() -> None:
    result = source_event()
    schema_path = Path(__file__).parents[1] / "schemas" / "temporal_event_envelope_v0_2.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(result.envelope.as_dict())
    validator.validate(result.envelope.as_dict(distributed=True))

    with pytest.raises(FrozenInstanceError):
        result.envelope.market_event_time_utc = "2022-09-30T08:17:00Z"
    with pytest.raises(TypeError):
        result.envelope.payload["close"] = 0.0
    with pytest.raises(ValueError, match="canonical UUIDv4"):
        replace(result.envelope, execution_id="11111111-1111-1111-8111-111111111111")


def test_parent_lineage_inherits_event_time_observation_stream_and_sequence() -> None:
    source = source_event()
    child = execute_stage(
        parent=source.envelope,
        clock=FakeClock([T0, T0 + timedelta(microseconds=1)], [500, 900]),
        producer_component="D01",
        producer_version="0.2",
        payload_type="D01OutputPair",
        payload_version="0.2.0",
        call=lambda: {"result": 1},
    )
    assert child.envelope.parent_event_id == source.envelope.event_id
    for field_name in (
        "observation_id",
        "source_stream_id",
        "sequence_number",
        "instrument_id",
        "market_event_time_utc",
        "market_event_time_role",
    ):
        assert getattr(child.envelope, field_name) == getattr(source.envelope, field_name)
    assert child.envelope.processing_duration_ns == 400


def test_same_domain_duration_timezone_and_cross_domain_rules() -> None:
    clock = FakeClock([T0, T0 + timedelta(microseconds=1)], [10, 25])
    start = begin_timing(clock)
    result = end_timing(clock, start)
    assert result.processing_duration_ns == 15

    require_aware_utc(T0)
    with pytest.raises(ValueError, match="timezone-aware"):
        require_aware_utc(datetime(2026, 8, 18, 12, 0))

    changed = FakeClock([T0, T0 + timedelta(microseconds=1)], [10, 25])
    changed_start = begin_timing(changed)
    changed.clock_domain_id = "33333333-3333-4333-8333-333333333333"
    with pytest.raises(ValueError, match="cross-clock-domain"):
        end_timing(changed, changed_start)


def test_wall_clock_inversion_is_telemetry_only_and_retry_ids_are_separate() -> None:
    inverted = source_event(clock=FakeClock([T0, T0 - timedelta(seconds=1)], [100, 140]))
    normal = source_event(clock=FakeClock([T0, T0 + timedelta(seconds=1)], [200, 240]))
    assert inverted.envelope.status == "SUCCESS"
    assert inverted.envelope.telemetry_flags == ("WALL_CLOCK_INVERSION",)
    assert inverted.envelope.processing_duration_ns == 40
    assert inverted.envelope.payload_sha256 == normal.envelope.payload_sha256
    assert inverted.envelope.observation_id == normal.envelope.observation_id
    assert inverted.envelope.event_id == normal.envelope.event_id
    assert inverted.envelope.execution_id != normal.envelope.execution_id
    assert UUID(inverted.envelope.execution_id).version == 4


def test_error_envelope_has_no_fabricated_payload_and_retains_cause() -> None:
    source = source_event()

    def fail() -> object:
        raise ValueError("sensitive local detail")

    with pytest.raises(StageExecutionError) as raised:
        execute_stage(
            parent=source.envelope,
            clock=FakeClock([T0, T0 + timedelta(microseconds=1)], [500, 550]),
            producer_component="D01",
            producer_version="0.2",
            payload_type="D01OutputPair",
            payload_version="0.2.0",
            call=fail,
            error_code="D01_FAILED",
        )
    envelope = raised.value.envelope
    assert isinstance(raised.value.cause, ValueError)
    assert envelope.status == "ERROR"
    assert envelope.payload is None
    assert envelope.payload_sha256 is None
    assert envelope.scientific_ids == {}
    assert envelope.error is not None
    assert envelope.error.error_type == "ValueError"
    assert envelope.error.error_code == "D01_FAILED"

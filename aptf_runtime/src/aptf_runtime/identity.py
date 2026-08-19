from __future__ import annotations

from uuid import uuid4

from .canonical_json import canonical_sha256


OBSERVATION_ID_PREFIX = "aptf:obs:v1:sha256:"
EVENT_ID_PREFIX = "aptf:evt:v1:sha256:"


def new_execution_id() -> str:
    return str(uuid4())


def new_runtime_identity() -> str:
    return str(uuid4())


def observation_id(
    *,
    source_stream_id: str,
    instrument_id: str,
    sequence_number: int,
    market_event_time_utc: str,
    market_event_time_role: str,
    payload_type: str,
    payload_version: str,
    payload_sha256: str,
) -> str:
    preimage = [
        "APTF_OBSERVATION_IDENTITY",
        "v1",
        source_stream_id,
        instrument_id,
        sequence_number,
        market_event_time_utc,
        market_event_time_role,
        payload_type,
        payload_version,
        payload_sha256,
    ]
    return OBSERVATION_ID_PREFIX + canonical_sha256(preimage)


def event_id(
    *,
    observation_id_value: str,
    parent_event_id: str | None,
    producer_component: str,
    producer_version: str,
    logical_output_ordinal: int,
    status: str,
    payload_type: str,
    payload_version: str,
    payload_sha256: str | None,
    error_type: str | None = None,
    error_code: str | None = None,
) -> str:
    preimage = [
        "APTF_LOGICAL_EVENT_IDENTITY",
        "v1",
        observation_id_value,
        parent_event_id,
        producer_component,
        producer_version,
        logical_output_ordinal,
        status,
        payload_type,
        payload_version,
        payload_sha256,
        error_type,
        error_code,
    ]
    return EVENT_ID_PREFIX + canonical_sha256(preimage)

from __future__ import annotations

from uuid import UUID

from aptf_runtime.single_observation_pipeline import (
    SOURCE_STREAM_ID,
    TARGET_TIMESTAMP,
    run_single_observation_proof,
)


def test_real_single_observation_lineage_payload_non_drift_and_terminal_plan() -> None:
    proof = run_single_observation_proof()
    events = proof["events"]

    assert proof["target_count"] == 1
    assert proof["setup_rows"] == 16
    assert proof["last_source_timestamp_read"] == TARGET_TIMESTAMP
    assert proof["target_source_row"]["source_provider"] == "FirstRateData"
    assert proof["target_source_row"]["source_row_number"] == 17
    assert proof["sequence_mapping"]["aptf_sequence_number"] == 16
    assert len(events) == 6
    assert [event["stage"] for event in events] == ["E0", "E1", "E2", "E3", "E4", "E5"]
    assert [event["payload_type"] for event in events] == [
        "NormalizedObservationSourceRecord",
        "D01OutputPair",
        "ReturnShape",
        "EnvelopeEvaluation",
        "DecisionRecord",
        "PositionTransitionPlan",
    ]

    observation_ids = {event["observation_id"] for event in events}
    event_ids = {event["event_id"] for event in events}
    execution_ids = {event["execution_id"] for event in events}
    clock_domains = {event["clock_domain_id"] for event in events}
    assert len(observation_ids) == 1
    assert len(event_ids) == 6
    assert len(execution_ids) == 6
    assert len(clock_domains) == 1
    assert all(UUID(value).version == 4 for value in execution_ids)

    assert events[0]["parent_event_id"] is None
    for parent, child in zip(events, events[1:]):
        assert child["parent_event_id"] == parent["event_id"]
    for event in events:
        assert event["source_stream_id"] == SOURCE_STREAM_ID
        assert event["sequence_number"] == 16
        assert event["market_event_time_utc"] == TARGET_TIMESTAMP
        assert event["status"] == "SUCCESS"
        assert event["processing_duration_ns"] >= 0
        assert event["processing_duration_us"] == event["processing_duration_ns"] / 1_000
        assert event["processing_duration_ms"] == event["processing_duration_ns"] / 1_000_000

    assert all(
        result["field_equivalent"] and result["hash_equivalent"]
        for result in proof["payload_non_drift"].values()
    )
    assert proof["state_non_drift"]["field_equivalent"]
    assert proof["state_non_drift"]["hash_equivalent"]
    assert proof["terminal_payload_type"] == "PositionTransitionPlan"
    assert proof["terminal_verbs"] == ["NO_ACTION"]

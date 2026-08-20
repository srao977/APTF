from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aptf_runtime.context import CONTEXT_LENGTH, RollingContext
from aptf_runtime.models import EmitterDecision, ExecutionIntent, ImmutableEmission, PositionState
from aptf_runtime.observation import Observation
from aptf_runtime.position import apply_position_decision


def source_row(index: int = 1) -> dict[str, str]:
    return {
        "entity_id": "SPY",
        "event_timestamp_local": "2022-09-30T04:00:00-04:00",
        "event_timestamp_utc": "2022-09-30T08:00:00Z",
        "timezone": "America/New_York",
        "open": "365.0",
        "high": "366.0",
        "low": "364.0",
        "close": "365.5",
        "volume": "1000.0",
        "session_type": "PRE_MARKET",
        "source_provider": "FirstRateData",
        "source_dataset": "SPY_1min_firstratedata",
        "source_row_number": str(index),
        "data_valid": "true",
        "quality_flags": "",
    }


def test_observation_validation_stops_before_math_and_preserves_source() -> None:
    row = source_row()
    observation = Observation.from_source_row(2, row)
    normalized = observation.to_d01()
    assert observation.close == row["close"]
    assert normalized.sequence_id == 0
    assert normalized.price == 365.5
    assert normalized.source_quality == 1.0

    invalid = source_row()
    invalid["data_valid"] = "false"
    with pytest.raises(ValueError, match="failed data validation"):
        Observation.from_source_row(2, invalid)
    missing = source_row()
    del missing["volume"]
    with pytest.raises(ValueError, match="missing required"):
        Observation.from_source_row(2, missing)


def test_rolling_context_is_continuous_and_defensive() -> None:
    context = RollingContext()
    records = []
    for index in range(45):
        record = {"observation_id": f"O{index + 1}", "C": float(index)}
        records.append(record)
        context.append_completed(record)
        if index + 1 >= CONTEXT_LENGTH:
            assert len(context) == CONTEXT_LENGTH
    assert context.observation_ids == tuple(f"O{index}" for index in range(31, 46))
    snapshot = context.snapshot()
    snapshot[0]["C"] = -1.0
    assert context.snapshot()[0]["C"] == 30.0


@pytest.mark.parametrize(
    ("before", "decision", "after", "intent", "classification"),
    [
        (PositionState.FLAT, EmitterDecision.BUY, PositionState.LONG, ExecutionIntent.BUY, "EPISODE_OPEN"),
        (PositionState.FLAT, EmitterDecision.HOLD, PositionState.FLAT, ExecutionIntent.NONE, "FLAT_HOLD"),
        (PositionState.FLAT, EmitterDecision.SELL, PositionState.FLAT, ExecutionIntent.NONE, "UNMATCHED_SELL_WHILE_FLAT"),
        (PositionState.LONG, EmitterDecision.BUY, PositionState.LONG, ExecutionIntent.NONE, "REPEATED_BUY_WHILE_LONG"),
        (PositionState.LONG, EmitterDecision.HOLD, PositionState.LONG, ExecutionIntent.NONE, "EPISODE_HOLD"),
        (PositionState.LONG, EmitterDecision.SELL, PositionState.FLAT, ExecutionIntent.SELL, "EPISODE_CLOSE"),
    ],
)
def test_position_operator_truth_table(before, decision, after, intent, classification) -> None:
    transition = apply_position_decision(before, decision)
    assert transition.state_after is after
    assert transition.execution_intent is intent
    assert transition.structural_classification == classification


def test_emission_is_deeply_immutable_and_returns_defensive_copy() -> None:
    emission = ImmutableEmission.from_dict({"decision": "BUY", "nested": {"values": [1, 2]}})
    with pytest.raises(TypeError):
        emission._payload["decision"] = "SELL"
    copy = emission.as_dict()
    copy["nested"]["values"].append(3)
    assert emission.as_dict()["nested"]["values"] == [1, 2]
    with pytest.raises(FrozenInstanceError):
        emission._payload = {}
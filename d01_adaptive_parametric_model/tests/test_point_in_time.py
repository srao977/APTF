import pytest

from aptf_d01.runtime.experiment_runner import _point_in_time_assert
from aptf_d01.models.normalized_observation import NormalizedObservation
from aptf_d01.models.enums import SessionState


def _obs() -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="TEST_ENTITY",
        event_id="E1",
        source_id="synthetic",
        source_sequence=1,
        exchange_timestamp=1.0,
        receive_timestamp=1.1,
        model_available_timestamp=1.2,
        price=100.0,
        trade_size=10.0,
        volume=1000.0,
        bid=99.99,
        ask=100.01,
        bid_size=500.0,
        ask_size=500.0,
        session_state=SessionState.OPEN,
    )


def test_future_observation_rejected() -> None:
    with pytest.raises(ValueError):
        _point_in_time_assert(_obs(), model_time=1.0)

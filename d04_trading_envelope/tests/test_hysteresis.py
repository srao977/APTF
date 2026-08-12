import pytest

from aptf_d04.envelope.hysteresis import HysteresisConfig, HysteresisController
from aptf_d04.models.enums import EnvelopeState


def test_threshold_validation() -> None:
    with pytest.raises(ValueError):
        HysteresisConfig(
            open_threshold=0.5,
            close_threshold=0.6,
            open_persistence_observations=3,
            close_persistence_observations=2,
        ).validate()


def test_open_persistence_behavior() -> None:
    h = HysteresisController(
        HysteresisConfig(0.75, 0.55, 3, 2)
    )
    state = EnvelopeState.CLOSED
    for score in [0.76, 0.78, 0.79]:
        state, _ = h.next_state(state, score)
    assert state == EnvelopeState.OPEN


def test_close_persistence_behavior() -> None:
    h = HysteresisController(HysteresisConfig(0.75, 0.55, 3, 2))
    state = EnvelopeState.OPEN
    for score in [0.54, 0.53]:
        state, _ = h.next_state(state, score)
    assert state == EnvelopeState.CLOSED


def test_closing_recovery_to_open() -> None:
    h = HysteresisController(HysteresisConfig(0.75, 0.55, 3, 2))
    state = EnvelopeState.OPEN
    state, _ = h.next_state(state, 0.50)
    assert state == EnvelopeState.CLOSING
    state, _ = h.next_state(state, 0.70)
    assert state == EnvelopeState.OPEN

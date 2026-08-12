from __future__ import annotations

from aptf_d04.models.enums import ContinuationSignal, EnvelopeState


def map_transition_event(previous: EnvelopeState, new: EnvelopeState) -> str | None:
    if previous == EnvelopeState.CLOSED and new == EnvelopeState.OPENING:
        return "ENVELOPE_OPENING"
    if previous == EnvelopeState.OPENING and new == EnvelopeState.OPEN:
        return "ENVELOPE_OPENED"
    if previous == EnvelopeState.OPEN and new == EnvelopeState.CLOSING:
        return "ENVELOPE_CLOSING"
    if previous == EnvelopeState.CLOSING and new == EnvelopeState.CLOSED:
        return "ENVELOPE_CLOSED"
    return None


def continuation_signal_for_state(
    position_open: bool,
    previous_state: EnvelopeState,
    new_state: EnvelopeState,
) -> ContinuationSignal:
    if not position_open:
        return ContinuationSignal.NONE
    if new_state == EnvelopeState.OPEN:
        return ContinuationSignal.HOLD_ELIGIBLE
    if new_state == EnvelopeState.CLOSING:
        return ContinuationSignal.REDUCE_CANDIDATE
    if previous_state in (EnvelopeState.OPEN, EnvelopeState.CLOSING) and new_state == EnvelopeState.CLOSED:
        return ContinuationSignal.EXIT_CANDIDATE
    return ContinuationSignal.NONE

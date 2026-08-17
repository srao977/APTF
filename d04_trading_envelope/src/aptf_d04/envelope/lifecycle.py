from __future__ import annotations

from aptf_d04.models.enums import EnvelopeState


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

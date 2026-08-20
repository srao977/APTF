from __future__ import annotations

from .models import EmitterDecision, ExecutionIntent, PositionState, PositionTransition


_TRANSITIONS = {
    (PositionState.FLAT, EmitterDecision.BUY): (
        PositionState.LONG,
        "EPISODE_OPEN",
        ExecutionIntent.BUY,
    ),
    (PositionState.FLAT, EmitterDecision.HOLD): (
        PositionState.FLAT,
        "FLAT_HOLD",
        ExecutionIntent.NONE,
    ),
    (PositionState.FLAT, EmitterDecision.SELL): (
        PositionState.FLAT,
        "UNMATCHED_SELL_WHILE_FLAT",
        ExecutionIntent.NONE,
    ),
    (PositionState.LONG, EmitterDecision.BUY): (
        PositionState.LONG,
        "REPEATED_BUY_WHILE_LONG",
        ExecutionIntent.NONE,
    ),
    (PositionState.LONG, EmitterDecision.HOLD): (
        PositionState.LONG,
        "EPISODE_HOLD",
        ExecutionIntent.NONE,
    ),
    (PositionState.LONG, EmitterDecision.SELL): (
        PositionState.FLAT,
        "EPISODE_CLOSE",
        ExecutionIntent.SELL,
    ),
}


def apply_position_decision(
    current_state: PositionState,
    emitter_decision: EmitterDecision,
) -> PositionTransition:
    state_after, classification, intent = _TRANSITIONS[(current_state, emitter_decision)]
    return PositionTransition(
        state_before=current_state,
        emitter_decision=emitter_decision,
        state_after=state_after,
        structural_classification=classification,
        execution_intent=intent,
    )

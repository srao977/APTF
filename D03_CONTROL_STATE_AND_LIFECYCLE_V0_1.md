# D03 Control State and Lifecycle v0.1

## Status

**PROPOSED DESIGN; NOT FROZEN; NO IMPLEMENTATION.**

## State ownership

D03 is stateless over explicit input. It owns the decision result, not hidden position memory.

- Actual position and position lineage are factual state owned by the position/control ledger.
- Pending target and pending decision identity are factual state owned by the execution controller.
- D04 owns envelope/candidate lifecycle.
- D03 computes desired position and transition intent for the current input pair.
- A future adapter/controller owns concrete execution and reports resulting state back through DecisionContext.

## Position and target states

Actual and desired position states are `FLAT|LONG|SHORT`. Pending target is `NONE|FLAT|LONG|SHORT`. Partial fills, quantities, prices, order types, and broker statuses are normalized outside D03 into current actual state, pending target, availability, and validity.

## Initialization

Default clean initialization:

```text
actual_position_state = FLAT
position_candidate_id = null
position_source_return_shape_model_time = null
pending_target_state = NONE
pending_decision_id = null
control_state_valid = true
```

A restart with an existing position must begin only after authoritative reconciliation supplies actual state and candidate/source lineage. D03 must not infer position from prior D04 envelope state.

Schema or semantic validation failure, including `control_state_valid=false`, yields no committed decision. BLOCKED is not an invalid-input substitute.

## Event-driven evaluation

D03 reevaluates on:

- each new D04Evaluation;
- actual-position change;
- pending-target/decision change;
- execution availability change;
- system/trading enable change;
- emergency-flatten change;
- control-validity change.

No 15-minute scheduler, bar completion, or replay-specific cadence exists.

## D04 lifecycle mapping

| Current D04 fact | Unconstrained D03 target |
|---|---|
| CLOSED | FLAT |
| OPENING | FLAT |
| OPEN with no QUALIFIED candidate | FLAT |
| OPEN with QUALIFIED UPWARD candidate | LONG |
| OPEN with QUALIFIED DOWNWARD candidate | SHORT |
| OPEN with QUALIFIED FLAT candidate | FLAT |
| CLOSING | FLAT |
| stale/projection invalid/safety closed | FLAT |

OPENING never authorizes preparatory exposure. CLOSING is a factual loss of open qualification and therefore targets FLAT; D03 does not wait for D04 CLOSED when position control is required.

## Candidate continuity and supersession

D03 uses only the candidate represented by the current D04 evaluation.

- Same-direction replacement: desired directional state remains unchanged; candidate lineage updates to the new candidate and transition is normally NO_CHANGE.
- Opposite-direction replacement: desired state changes to the opposite target; transition is REVERSE when authorized.
- Replacement with absent/invalid/non-directional candidate: desired FLAT.
- `SHAPE_SUPERSEDED` alone is not a failure and does not force FLAT if the same evaluation contains a valid replacement candidate.

Direction comes exclusively from immutable `D04 candidate.path_direction`; there is no direct D02 input.

## Closure, staleness, and invalidation

D04 factual closure does not itself submit EXIT. D03 maps non-OPEN/safety facts to desired FLAT. If actual is LONG/SHORT, this derives CLOSE; if actual is FLAT, NO_CHANGE. Candidate invalidation is preserved as reason/lineage. Stale aperture and D04 hysteresis reset remain D04 facts and are not recomputed.

## Recovery

When D04 later returns to OPEN with a new qualified directional candidate, D03 evaluates the current actual/pending context anew. No old target, candidate, or blocked action is restored. If execution was unavailable, availability restoration triggers reevaluation; the old decision is never blindly queued.

When disabled control is re-enabled, the next D03 evaluation uses only the then-current D04 evaluation and DecisionContext. It does not replay missed candidates, restore targets observed while disabled, or automatically execute a stale deferred action.

## Control overrides

Priority is invalid context, emergency flatten, system disable, trading disable, then D04 target rules. Approved behavior:

- emergency flatten establishes desired FLAT even if other controls are disabled;
- unavailable execution records BLOCKED and cannot authorize action;
- system/trading disabled preserve actual state, emit NO_CHANGE, authorize no transition, and accumulate no deferred target;
- invalid control state blocks all action.

Disabled preservation continues even if D04 becomes CLOSING, CLOSED, stale, safety-closed, or invalidates its candidate. Only explicit emergency flatten establishes FLAT while disabled. This is suspension of control transitions, not an assertion that the position remains desirable.

BLOCKED applies only after a valid desired target and actionable transition are known and execution is unavailable. It creates no deferred transition. Candidate lineage is current D04 candidate only for ordinary QUALIFIED UPWARD/DOWNWARD/FLAT target rules; all override, safety, non-OPEN, absent, and invalidated target rules emit null lineage.

## Transition protection

No second D03 hysteresis or debounce is introduced. D04 already protects envelope qualification. D03 idempotency, actual/pending comparison, and deterministic input identity prevent duplicate transition commitments. Engineering event coalescing may not alter ordered semantic outputs.

## Reset

D03 has no internal reset. Reset means the external control ledger has reconciled to an explicit state and emits a new DecisionContext. Clearing candidate lineage is valid only when actual position becomes FLAT. Clearing a pending target requires an execution-controller event.

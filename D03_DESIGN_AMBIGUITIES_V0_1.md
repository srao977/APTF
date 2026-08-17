# D03 Design Ambiguities v0.1

## Status

**ZERO OPEN ISSUES. D03 DESIGN FREEZE-READY FOR HUMAN REVIEW; NOT FROZEN.**

No historical outcomes, P&L, replay, or reserve evidence was used to resolve these issues.

## A1. Directional authority - RESOLVED

**Human decision:** D04 CandidateEnvelope carries immutable `path_direction` propagated verbatim from its source D02 ReturnShape.

```text
D02 ReturnShape.path_direction
  -> D04 candidate.path_direction
  -> D03
```

Exact domain: `UPWARD|DOWNWARD|FLAT` from `d02.v02.models.PathDirection`.

D03 mapping:

- UPWARD -> desired LONG;
- DOWNWARD -> desired SHORT;
- FLAT -> desired FLAT and no directional trade.

D03 has zero direct D02 inputs and performs no directional inference. D04 does not recompute or reinterpret direction. Resolution is implemented and frozen under D04 v0.2.1 executable/interface authority.

## A2. Disabled-control policy - RESOLVED

**Human decision:** with `emergency_flatten=false`, either `system_enabled=false` or `trading_enabled=false` preserves the current actual position/control state and emits NO_CHANGE.

- LONG remains desired LONG.
- SHORT remains desired SHORT.
- FLAT remains desired FLAT.
- D04 candidate/state changes cannot retarget while disabled.
- D04 CLOSING, CLOSED, stale, safety closure, or invalidation does not flatten while disabled.
- No deferred/pending target is accumulated from D04 changes.
- Re-enable evaluates only the current D04 evaluation and current DecisionContext.

Disabled means control transitions are suspended; it is not a market opinion.

`emergency_flatten=true` has higher precedence, establishes desired FLAT, and derives CLOSE from LONG/SHORT or NO_CHANGE from FLAT. Execution availability still controls whether the transition can be authorized now.

## Previously resolved design questions

- Primary paradigm: desired state plus derived transition intent.
- MAINTAIN: no separate command; NO_CHANGE plus explicit desired state.
- Reversal: desired opposite state; execution sequencing downstream.
- Statefulness: stateless over explicit DecisionContext.
- Position sizing: outside first-pass D03.
- Second hysteresis: none.
- Commitment: immutable, deterministic, pre-outcome, including NO_CHANGE/BLOCKED.
- Execution unavailable: BLOCKED/unauthorized, never queued; reevaluate current facts when availability changes.

## Counts

- decision policy issues open: 0;
- control-state issues open: 0;
- reversal issues open: 0;
- context issues open: 0;
- commitment issues open: 0;
- ownership/interface issues open: 0.

D03 design is freeze-ready, subject to human review. This document does not freeze or implement D03.

## Final committed-output blockers - RESOLVED BY HUMAN REVIEW

1. Primary reason: resolved target/control rule reason; transition/overlay reasons are supporting.
2. Decision rule ID: `TARGET:<id>|TRANSITION:<id-or-NONE>|OVERLAYS:<ordered-ids-or-NONE>`.
3. Supporting reasons: ordered target detail, transition reason, overlay reasons; duplicate-free; primary excluded.
4. Invalid input: rejected before policy/commitment; no D03Decision and no BLOCKED record.
5. Safety reason: machine R30 primary `D04_SAFETY_CLOSED`; exact D04 safety reason is supporting.
6. T00: pending target exists AND desired differs from pending target; intent RETARGET. Execution unavailability is overlay A00.
7. Candidate lineage: null for emergency/disabled/noncandidate targets; current D04 lineage for ordinary QUALIFIED UPWARD/DOWNWARD/FLAT.

Current open issue count after all reconciliations: 0.

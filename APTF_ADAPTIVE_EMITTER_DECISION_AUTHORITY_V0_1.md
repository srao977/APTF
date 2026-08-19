# APTF Adaptive Emitter Decision Authority V0.1

Status: PRODUCTION CANDIDATE / PRE-RESERVE  
Normative validated rule authority: `APTF_TEST_006A_EMITTER_DECISION_AUTHORITY_V0_1.md` SHA-256 `c4c5bbf36ab97b3e7fc4628dfe11708947f996bcd79901a9d19b6a0f2049e9e2`.

## Inputs And Context

Current D02 `path_direction` is canonical sign authority. Current H/Q_G/Q_S/Q_R/C retain existing formulas. Prior context is exactly 15 completed records. Adaptive values are prior-15 median/min/max/range C, prior C, delta C, UP/DOWN/FLAT counts, direction balance, and actual source delta-t.

## Terminal Rules

- BUY iff H=1, current direction UPWARD, current C >= prior-15 median C, and prior up_count >= down_count. Set internal Position State LONG.
- SELL iff H=1, current direction DOWNWARD, current C >= prior-15 median C, and prior down_count >= up_count. Set internal Position State SHORT.
- HOLD otherwise; affirmatively preserve current internal Position State. HOLD is not error, unknown, FLAT, or NO_ACTION.
- Invalid input has execution status INVALID and emits no Position Decision.

Current D02 direction controls sign; directional count and relative C must agree. Count ties permit current direction. Reversal propensity is emitted context but does not trigger case-by-case overrides. Historical C=0.75 is not consulted.

Initial experimental Position State is FLAT and not broker-sourced. Feedback sets prior decision and internal state from n+1 only. Decision vocabulary, equations, conflict resolution, context length, adaptation, and feedback are frozen.

## Emission Contract

Every actionable immutable emission includes IDs, source/time/context provenance, state before/after, complete DMO/FMO/ReturnShape, H/Q_G/Q_S/Q_R/C, adaptive properties, Position State, terminal decision, rule path, feedback declaration, source/rule/code fingerprints, and component/direct nanosecond timing.
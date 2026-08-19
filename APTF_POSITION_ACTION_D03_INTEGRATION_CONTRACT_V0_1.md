# APTF Position Action / D03 Integration Contract v0.1

## Frozen authority

D03 implementation freeze: `D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json`, SHA256 `6A93291FFE555A3FFF1239A9A4F88C0A1546B6C46A02B60586614B60A3C91AD6`.

## Consumed D03 fields

The controller consumes the complete committed record for validation/hash and uses these semantic fields directly: `decision_id`, `decision_time`, `entity_id`, `prior_position_state`, `desired_position_state`, `transition_intent`, and `action_authorized`. It does not consume D01, D02, D04, candidate direction, reasons, benchmark data, or market data to alter the mapping.

## Intent overlay

| D03 condition | Plan behavior |
|---|---|
| actionable intent and authorized | READY with base matrix verbs |
| aligned NO_CHANGE | NON_EXECUTABLE_NO_CHANGE with HOLD/NO_ACTION |
| same target already pending (T10) | PENDING_ALREADY with no new verbs |
| BLOCKED | BLOCKED; retain required base verbs for audit; executable=false |
| invalid/malformed or state mismatch | reject; no plan |

`action_authorized` is a hard gate. The controller cannot turn BLOCKED or NO_CHANGE into executable intent. BLOCKED creates no queue. Disabled control is not flattening; D03 preserves actual state. Emergency flatten is not re-decided; its committed FLAT target maps normally. Candidate lineage is carried only inside the immutable source record/hash and does not affect action selection.

## Consistency rules

For no-pending ordinary pairs, D03 intent must match the matrix: aligned -> NO_CHANGE, FLAT to directional -> OPEN, directional to FLAT -> CLOSE, opposite directional -> REVERSE. RETARGET is allowed only as D03's authorized pending-conflict result. Same-target pending is detected by transition rule ID/reason and emits no duplicate verbs.

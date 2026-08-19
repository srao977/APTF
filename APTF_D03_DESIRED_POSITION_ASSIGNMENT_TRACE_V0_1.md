# APTF D03 Desired-Position Assignment Trace V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Authority and implementation

- Frozen implementation: `D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json` v0.1.
- Runtime module: `d03.v01`.
- Target resolver: `_resolve_target_rule(context, evaluation)`.
- Committed assignment: `evaluate_decision` constructs `DecisionRecord(desired_position_state=desired)`.
- Legal domain: `PositionState.FLAT`, `PositionState.LONG`, `PositionState.SHORT`.
- D03 configuration file: NONE. Policy/rule versions and tables are code/design constants.

There is one committed assignment location. Its value comes from 12 named target rules, evaluated in order, plus a defensive R34 fallback.

## Every target assignment path

| Priority | Desired | Assignment branch | Exact condition | Inputs used | Primary reason |
|---:|---|---|---|---|---|
| 0 | FLAT | R10 | `emergency_flatten` | D03 context | `EMERGENCY_FLATTEN` |
| 1 | actual state | R20 | `not system_enabled` | D03 actual position/control | `SYSTEM_DISABLED` |
| 2 | actual state | R21 | `not trading_enabled` | D03 actual position/control | `TRADING_DISABLED` |
| 3 | FLAT | R30 | safety closed OR stale OR projection invalid | D04 evaluation | `D04_SAFETY_CLOSED` |
| 4 | FLAT | R31 | envelope state CLOSED | D04 evaluation | `ENVELOPE_CLOSED` |
| 5 | FLAT | R32 | envelope state OPENING | D04 evaluation | `ENVELOPE_NOT_QUALIFIED` |
| 6 | FLAT | R33 | envelope state CLOSING | D04 evaluation | `ENVELOPE_CLOSING` |
| 7 | FLAT | R34 | OPEN and candidate absent | D04 evaluation | `NO_VALID_CANDIDATE` |
| 8 | FLAT | R35 | OPEN and candidate status not QUALIFIED | D04 candidate | `CANDIDATE_INVALIDATED` |
| 9 | FLAT | R36 | OPEN, QUALIFIED, direction FLAT | D04 candidate direction | `CANDIDATE_NON_DIRECTIONAL` |
| 10 | LONG | R40 | OPEN, QUALIFIED, direction UPWARD | D04 candidate direction | `CANDIDATE_QUALIFIED` |
| 11 | SHORT | R41 | OPEN, QUALIFIED, direction DOWNWARD | D04 candidate direction | `CANDIDATE_QUALIFIED` |
| fallback | FLAT | R34 fallback | No prior branch returns | D04 evaluation | `NO_VALID_CANDIDATE` |

R20/R21 return one of all three legal states depending on actual position. Thus LONG has both R40 and disabled-preservation paths; SHORT has both R41 and disabled-preservation paths; FLAT has the ordinary D04 paths plus overrides/preservation.

## Assignment versus later stages

After desired position is fixed:

1. `_transition_intent` compares desired with pending target or actual state.
2. `_overlay_rule` may change transition intent to BLOCKED when execution is unavailable.
3. Neither pending state nor `execution_available` changes `desired_position_state`.

`control_state_valid=false` does not assign FLAT; it rejects input and emits no DecisionRecord.

## Minimal current frozen input for a committed target

Schema-valid D03 requires the complete `D03Input`:

- complete 23-field D04 `EnvelopeEvaluation`;
- all 12 `DecisionContext` fields.

The target resolver itself reads only:

- `emergency_flatten`, `system_enabled`, `trading_enabled`, `actual_position_state`;
- D04 `safety_state`, `stale`, `projection_valid`, `safety_reason`, `new_envelope_state`;
- candidate existence, `status`, `path_direction`, plus candidate ID/source time for lineage.

Other required fields support validity, identity, commitment, transition, pending handling, authorization, or fingerprints.

# APTF D03 DecisionContext Field Matrix V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

Runtime type: `d03.v01.DecisionContext`. All fields are required; extras and non-finite floats are forbidden.

| Field | Type/domain | Source | Used in desired target? | Other use | Can change LONG/SHORT/FLAT? | Can veto direction? | Can force FLAT? | Can delay/block transition? |
|---|---|---|---|---|---|---|---|---|
| `context_time` | finite float | causal control snapshot | NO | D04 time validation, decision time/ID | NO | NO | NO | NO |
| `entity_id` | nonempty str | control/position authority | NO | D04 entity match, identity | NO | validation can reject | NO | NO |
| `actual_position_state` | FLAT/LONG/SHORT | external actual-position ledger | YES only under R20/R21 disabled preservation | prior state and transition matrix | YES when disabled; NO in enabled D04 target rules | YES under disabled control by replacing candidate target with actual | YES if disabled and actual FLAT | Determines OPEN/CLOSE/REVERSE/NO_CHANGE after target |
| `position_candidate_id` | str/null constrained by actual state | position lineage authority | NO | semantic validation/fingerprint | NO | validation can reject | NO | NO |
| `position_source_return_shape_model_time` | finite float/null constrained by actual | position lineage authority | NO | semantic validation/fingerprint | NO | validation can reject | NO | NO |
| `pending_target_state` | NONE/FLAT/LONG/SHORT | pending-transition ledger | NO | T00 RETARGET / T10 NO_CHANGE | NO | NO | NO | YES |
| `pending_decision_id` | str/null consistent with pending target | pending-transition ledger | NO | validation/fingerprint | NO | validation can reject | NO | YES via pending consistency/lineage |
| `execution_available` | bool | execution/control authority | NO | A00 converts actionable intent to BLOCKED | NO | NO | NO | YES, blocks without changing desired |
| `system_enabled` | bool | system control | YES, R20 | preserve actual and NO_CHANGE | YES | YES | YES if actual FLAT | YES; disabled means no new transition |
| `trading_enabled` | bool | trading control | YES, R21 | preserve actual and NO_CHANGE | YES | YES | YES if actual FLAT | YES; disabled means no new transition |
| `emergency_flatten` | bool | emergency control | YES, highest priority R10 | transition derived toward FLAT | YES | YES | YES | Transition can still be execution-blocked |
| `control_state_valid` | bool | control authority | Boundary only | false rejects before commitment | No desired value produced | Rejects evaluation | Does not assign FLAT | Prevents any transition record |

## Actual-position result

Identical D04 input can produce different desired states solely from actual position **only when `system_enabled=false` or `trading_enabled=false`**:

- actual FLAT -> desired FLAT;
- actual LONG -> desired LONG;
- actual SHORT -> desired SHORT.

With emergency false and both controls enabled, actual position does not change the target; it changes only transition intent.

## Pending/execution result

Pending state and execution availability do not change LONG, SHORT, or FLAT target selection. They operate after the target:

- pending differs -> RETARGET;
- pending matches -> NO_CHANGE / already pending;
- execution unavailable -> BLOCKED for actionable transitions.

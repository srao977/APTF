# APTF D03 Desired-Position Truth Table V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

This is a STATIC CODE TRACE. No contexts or market objects were fabricated or executed.

## Target truth table

Rows are first-match precedence.

| D03 control | D04 safety/state | Candidate | D02 direction carried | Actual | Desired | Notes |
|---|---|---|---|---|---|---|
| invalid control/schema | any | any | any | any | NO RECORD | boundary rejection |
| emergency flatten | any | any | any | any | FLAT | R10 |
| system disabled | ignored | ignored | ignored | FLAT/LONG/SHORT | actual | R20 |
| trading disabled | ignored | ignored | ignored | FLAT/LONG/SHORT | actual | R21 |
| enabled | safety/stale/invalid projection | any | any | any | FLAT | R30 |
| enabled | CLOSED | any | any | any | FLAT | R31 |
| enabled | OPENING | any | any | any | FLAT | R32 |
| enabled | CLOSING | any | any | any | FLAT | R33 |
| enabled | OPEN | absent | unavailable | any | FLAT | R34 |
| enabled | OPEN | INVALIDATED | preserved but unusable | any | FLAT | R35 |
| enabled | OPEN | QUALIFIED | FLAT | any | FLAT | R36 |
| enabled | OPEN | QUALIFIED | UPWARD | any | LONG | R40 |
| enabled | OPEN | QUALIFIED | DOWNWARD | any | SHORT | R41 |

## Actual-position cross product for ordinary candidates

| Candidate | Actual FLAT | Actual LONG | Actual SHORT |
|---|---|---|---|
| QUALIFIED UPWARD | desired LONG / OPEN | desired LONG / NO_CHANGE | desired LONG / REVERSE |
| QUALIFIED DOWNWARD | desired SHORT / OPEN | desired SHORT / REVERSE | desired SHORT / NO_CHANGE |
| QUALIFIED FLAT | desired FLAT / NO_CHANGE | desired FLAT / CLOSE | desired FLAT / CLOSE |
| no candidate / non-OPEN | desired FLAT / NO_CHANGE | desired FLAT / CLOSE | desired FLAT / CLOSE |

Desired is invariant across actual state in this enabled table; only transition changes.

## Pending and execution cross product

For any already-resolved desired target:

| Pending/control | Desired changes? | Transition result |
|---|---|---|
| no pending | NO | matrix NO_CHANGE/OPEN/CLOSE/REVERSE |
| pending target equals desired | NO | NO_CHANGE / already pending |
| pending target differs | NO | RETARGET |
| execution unavailable + actionable intent | NO | BLOCKED |
| execution unavailable + NO_CHANGE | NO | remains NO_CHANGE |

## Disabled-control cross product

For identical D04 input:

| Actual | System/trading disabled desired |
|---|---|
| FLAT | FLAT |
| LONG | LONG |
| SHORT | SHORT |

This is why the full policy cannot be reduced solely to D02 sign plus D04 permission.

## Persistence relationship

Starting CLOSED with valid $C\ge0.75$:

- first consecutive qualifying evaluation -> OPENING -> D03 FLAT;
- second -> OPENING -> D03 FLAT;
- third -> OPEN -> candidate created from the current shape direction -> D03 LONG for UPWARD or SHORT for DOWNWARD.

Hysteresis counts capturability qualification only; it does not inspect direction sign. If the sequence breaks before the third observation, counters reset and no candidate reaches D03.

# APTF Six Action Verb Responsibility Matrix V0.1

Status: DIAGNOSTIC / DESIGN REVIEW ONLY. NOT FROZEN AUTHORITY.

## Frozen position language

The frozen position-state domain is:

- `FLAT`: no directional exposure in the entity.
- `LONG`: positive directional exposure.
- `SHORT`: negative directional exposure.

These are states, not commands. `LONG` does not mean `BUY`; `SHORT` does not mean `SELL_SHORT`.

Authority: [APTF_CANONICAL_EXECUTION_VERB_ONTOLOGY_V0_1.md](APTF_CANONICAL_EXECUTION_VERB_ONTOLOGY_V0_1.md), frozen by [APTF_POSITION_ACTION_DESIGN_V0_1_FREEZE.json](APTF_POSITION_ACTION_DESIGN_V0_1_FREEZE.json).

## Exact six primitive verbs

| Verb | Exact frozen meaning | Valid current-position precondition | Desired-position condition | Result after successful execution | Semantic category |
|---|---|---|---|---|---|
| `BUY` | Establish LONG exposure | FLAT | LONG | LONG | Primitive execution instruction for an opening transition |
| `SELL` | Close existing LONG exposure | LONG | FLAT, or first leg of LONG to SHORT | FLAT after this primitive | Primitive execution instruction for a closing transition |
| `SELL_SHORT` | Establish SHORT exposure | FLAT | SHORT | SHORT | Primitive execution instruction for an opening transition |
| `BUY_TO_COVER` | Close existing SHORT exposure | SHORT | FLAT, or first leg of SHORT to LONG | FLAT after this primitive | Primitive execution instruction for a closing transition |
| `HOLD` | Preserve already-open directional exposure | LONG or SHORT | Same directional state | Unchanged | Non-executable transition communication; not a broker order |
| `NO_ACTION` | Preserve absence of directional exposure | FLAT | FLAT | FLAT | Non-executable transition communication; not a broker order |

Reversal is not a seventh verb. It is an ordered pair of primitives.

## Complete frozen transition algebra

| Current position | Desired position | Transition class | Ordered action verb(s) | Successful resulting position | Executable only when |
|---|---|---|---|---|---|
| FLAT | FLAT | `NO_CHANGE_FLAT` | `NO_ACTION` | FLAT | Never submitted; aligned state |
| FLAT | LONG | `OPEN_LONG` | `BUY` | LONG | plan `READY` and `action_authorized=true` |
| FLAT | SHORT | `OPEN_SHORT` | `SELL_SHORT` | SHORT | plan `READY` and `action_authorized=true` |
| LONG | FLAT | `CLOSE_LONG` | `SELL` | FLAT | plan `READY` and `action_authorized=true` |
| LONG | LONG | `HOLD_LONG` | `HOLD` | LONG | Never submitted; aligned state |
| LONG | SHORT | `REVERSE_LONG_TO_SHORT` | `SELL`, then `SELL_SHORT` | SHORT | plan `READY` and `action_authorized=true` |
| SHORT | FLAT | `CLOSE_SHORT` | `BUY_TO_COVER` | FLAT | plan `READY` and `action_authorized=true` |
| SHORT | LONG | `REVERSE_SHORT_TO_LONG` | `BUY_TO_COVER`, then `BUY` | LONG | plan `READY` and `action_authorized=true` |
| SHORT | SHORT | `HOLD_SHORT` | `HOLD` | SHORT | Never submitted; aligned state |

Authority: [APTF_POSITION_TRANSITION_MATRIX_V0_1.md](APTF_POSITION_TRANSITION_MATRIX_V0_1.md) and [position_transition_controller.py](position_transition_controller/position_transition_controller.py).

## Responsibility matrix

| Question | Frozen owner | Inputs | Output | Explicit exclusions |
|---|---|---|---|---|
| What direction does the analytical model indicate? | D02 | D01 DMO/FMO | `ReturnShape.path_direction` | No position or verb |
| What position does APTF desire? | D03 | D04 factual evaluation plus DecisionContext | `desired_position_state` | No broker command |
| What transition is required? | D03 describes intent; Position Transition Controller validates and derives the concrete state-pair class | actual/prior position plus desired position | `transition_intent`, then `transition_class` | No market interpretation |
| Which primitive verb sequence represents the transition? | Position Transition Controller | actual position, desired position, committed D03 authorization | `ordered_execution_verbs` | No D04 fields, broker health, capital, price, quantity, or routing |
| May that sequence be submitted? | D04 qualifies capturability before desire; D03 applies `execution_available`; controller preserves D03 authorization | D04 context, D03 control context, committed record | D04 candidate/no candidate; D03 `action_authorized`; plan status | Controller cannot override a block |

## Direct dependency result

The Position Transition Controller:

- consumes a committed D03 record, its hash, and authoritative actual-position snapshot;
- does not consume D04 context or `path_direction` directly;
- does not read capital availability, broker health, liquidity, spread, latency, or risk capacity;
- selects verb identity only from `(actual_position, desired_position)`;
- retains required base verbs for a D03 `BLOCKED` record, but marks the plan non-executable.

Therefore D04 properties do not directly select a primitive verb. They can indirectly change the eventual verb by changing D04 candidate qualification and therefore D03 desired position.

## Static implementation non-conformance finding

The frozen matrix and six primitive verbs are implemented exactly, but the controller's surrounding validation does not fully implement its frozen design:

1. The frozen `A_PENDING` vector supplies D03 `transition_intent=NO_CHANGE` for current FLAT, desired LONG and requires `PENDING_ALREADY` with no verbs. The implementation's `NO_CHANGE` branch rejects this changing base pair and returns no plan. Its separate `transition_intent == "PENDING_ALREADY"` branch is unreachable because the validator does not admit that intent and D03 never emits it.
2. The design requires OPEN/CLOSE/REVERSE to agree with the base transition class. The implementation does not check that agreement. The test helper uses `OPEN` for every non-aligned pair, including CLOSE and REVERSE pairs, and the controller still emits READY base verbs.
3. The design requires entity/identity/hash reconciliation. The implementation validates only a subset and does not cryptographically compare the supplied D03 hash or require actual-position entity/identity.

These defects do not change the authoritative six-verb algebra documented above. They mean the current implementation is not a complete validator of the frozen semantic contract. No repair was made.

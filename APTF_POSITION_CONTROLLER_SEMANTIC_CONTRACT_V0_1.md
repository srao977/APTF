# APTF Position Controller Semantic Contract V0.1

Status: CURRENT SEMANTIC CLARIFICATION AUTHORITY
Date: 2026-08-18
Scope: external analytical terminology only

## Authority Relationship

This contract clarifies the externally meaningful terminology of the frozen Position Transition Controller. It does not replace or modify the Position Action Design V0.1 freeze, D03 freeze, Position Controller implementation freeze, Temporal Event Envelope V0.2 freeze, schemas, fields, transition mathematics, or action verbs.

Where a frozen predecessor uses `ActualPosition`, `actual_position`, `actual_position_state`, `actual_position_snapshot`, `actual_position_before`, or `actual_position_after`, those names remain valid legacy internal implementation/schema names. Under the current APTF analytical contract they mean internal transition/control or replay state unless a separately defined external execution authority is explicitly identified. No such broker authority exists in the current implementation.

## Canonical Analytical Chain

```text
MarketObservation(t)
  -> D01 -> D02 -> D04 -> D03
  -> Position Transition Controller
  -> Position Controller Decision(t)
```

The externally meaningful terminal analytical result consists of:

- `D03 POSITION`: the D03 position-state result for observation t;
- `POSITION CONTROLLER DECISION`: the semantic action or ordered action sequence produced for observation t.

The complete timestamped terminal event remains the E5 Temporal Event Envelope carrying the unchanged `PositionTransitionPlan` payload.

## Required Definitions

### Position Controller Internal State

Internal state supplied to the Position Controller to determine the transition represented by the current D03 position. It may be maintained by a replay/control harness and is not inherently broker-sourced. Frozen legacy fields that name this value "actual" do not establish external execution truth.

### D03 Position

The position-state result supplied by D03 for observation t under the existing frozen D03 contract. The implementation field `desired_position_state` is retained unchanged. Externally, its terminal analytical label is `D03 POSITION`.

### Position Controller Decision

The semantic action produced by the Position Transition Controller for causal observation t. It is represented internally by the unchanged complete `PositionTransitionPlan`, particularly `ordered_execution_verbs`, transition class, authorization, and plan status. The six verbs remain BUY, SELL, SELL_SHORT, BUY_TO_COVER, HOLD, and NO_ACTION.

### Broker Position

Outside the scope of the current APTF analytical contract. No broker fields, broker timestamps, broker reconciliation, fill confirmation, or external execution state are defined here.

## Frozen Internal Mapping

| External term | Frozen internal representation | Rule |
|---|---|---|
| D03 POSITION | `DecisionRecord.desired_position_state` / controller `desired_position` | retain field; change only external label |
| Position Controller internal state | `DecisionContext.actual_position_state`, controller `actual_position_snapshot`, `source_position`, `ActualPositionState`, replay ledger `actual_position_*` | legacy internal names retained; never imply broker truth |
| Position Controller Decision | complete `PositionTransitionPlan`; externally emphasize ordered semantic verb(s) | payload and verbs unchanged |
| Market event time | envelope `market_event_time_utc=t` | unchanged |

D03 `prior_position_state` remains the committed internal transition-state snapshot copied from its legacy context field. D03 mathematics and disabled-control behavior are unchanged.

## Authoritative Transition Interpretation

Mechanically verified against frozen `TRANSITION_MATRIX` and `APTF_POSITION_TRANSITION_MATRIX_V0_1.md`:

| Controller State | D03 Position | Position Controller Decision | Frozen transition class |
|---|---|---|---|
| FLAT | FLAT | NO_ACTION | NO_CHANGE_FLAT |
| FLAT | LONG | BUY | OPEN_LONG |
| FLAT | SHORT | SELL_SHORT | OPEN_SHORT |
| LONG | FLAT | SELL | CLOSE_LONG |
| LONG | LONG | HOLD | HOLD_LONG |
| LONG | SHORT | SELL -> SELL_SHORT | REVERSE_LONG_TO_SHORT |
| SHORT | FLAT | BUY_TO_COVER | CLOSE_SHORT |
| SHORT | LONG | BUY_TO_COVER -> BUY | REVERSE_SHORT_TO_LONG |
| SHORT | SHORT | HOLD | HOLD_SHORT |

This table changes only column terminology. All nine state pairs, classes, ordering, authorization overlays, and six verbs are unchanged. A complete plan may be non-executable; the semantic verb list does not override `action_authorized` or `plan_status`.

## Temporal Semantics

`PositionControllerDecision(t)` is the E5 analytical event associated with the same immutable `market_event_time_utc`, `observation_id`, parent lineage, and runtime telemetry as the frozen V0.2 envelope. It retains `event_id`, `execution_id`, `parent_event_id`, `received_at_utc`, `emitted_at_utc`, and `processing_duration_ns`. Model/control time does not replace envelope telemetry.

## Future Report Contract

Future single-observation reports must use:

```text
MARKET EVENT TIME:
<t>

D03 POSITION:
<LONG | SHORT | FLAT>

POSITION CONTROLLER DECISION:
<verb or ordered verb sequence>
```

Optional diagnostic state must be labeled:

```text
INTERNAL CONTROLLER STATE BEFORE DECISION:
<FLAT | LONG | SHORT>
```

The heading `ACTUAL POSITION` is prohibited in future analytical reports unless a future explicit broker-sourced contract introduces and proves that concept.

## Implementation Decision

No code, schema, runtime wrapper, mathematical, action-verb, or temporal change is required. Existing user-facing replay CSV headings already expose `APTF_desired_position` and `APTF_position_action`, not `ACTUAL POSITION`. Frozen internal identifiers are retained to preserve authority and compatibility.

## Broker Boundary

Broker/execution position is outside the current APTF analytical Position Controller contract. This contract does not design or anticipate its interface beyond that boundary statement.

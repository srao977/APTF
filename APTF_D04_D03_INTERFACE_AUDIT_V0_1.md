# APTF D04-D03 Interface Audit V0.1

Diagnostic only. No implementation authority.

## Boundary contract

- D04 producer: `aptf_d04.models.envelope_state.EnvelopeEvaluation` (23 fields).
- D03 consumer: `d03.v01.D03Input`.
- D03 input consists of `d04_evaluation: EnvelopeEvaluation` plus `decision_context: DecisionContext`.
- Adapter: the replay constructs `DecisionContext`; D04 evaluation is passed directly.

## Complete D03 input schema

`D03Input` fields:

1. `d04_evaluation: EnvelopeEvaluation`
2. `decision_context: DecisionContext`

`DecisionContext` requires 12 fields: `context_time`, `entity_id`, `actual_position_state`, `position_candidate_id`, `position_source_return_shape_model_time`, `pending_target_state`, `pending_decision_id`, `execution_available`, `system_enabled`, `trading_enabled`, `emergency_flatten`, and `control_state_valid`.

## Zero-mock trace result

D04 did not execute, so no `EnvelopeEvaluation` exists. The diagnostic also forbids initializing `actual_position_state`; D03 requires it and permits only `FLAT`, `LONG`, or `SHORT`. Therefore no valid complete D03 input exists for either target event.

| Required item | Row A | Row B | Provenance |
|---|---|---|---|
| D04 evaluation | NOT AVAILABLE | NOT AVAILABLE | D04 stopped for missing real context |
| actual_position_state | NOT SUPPLIED | NOT SUPPLIED | Explicitly prohibited by diagnostic |
| candidate identity/state/path_direction | NOT AVAILABLE | NOT AVAILABLE | Requires real D04 evaluation |
| pending state | NOT SUPPLIED | NOT SUPPLIED | No real pending-order source |
| execution/control flags | NOT SUPPLIED | NOT SUPPLIED | No real control-state source |

D03 was **not invoked**. No DecisionRecord, desired position, action authorization, transition intent, reason, lineage, or rule identity was fabricated.

## Prior replay behavior, not zero-mock evidence

The existing replay injects `actual_position=LONG`, a synthetic candidate ID `D04C|SPY|0.0|0.0`, candidate source time `0.0`, pending state, and execution/control booleans. Its generated CSV reports `FLAT` at both target timestamps. Those records are excluded from this trace because they do not satisfy the requested zero-mock gate.

Frozen D03 code maps envelope states `CLOSED`, `OPENING`, and `CLOSING` to desired `FLAT`; an `OPEN` qualified `UPWARD` candidate maps to `LONG`, and a qualified `DOWNWARD` candidate maps to `SHORT`. This code rule does not establish which rule fired for these targets because their valid D04/D03 inputs were unavailable.

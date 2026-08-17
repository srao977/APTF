# D03 Final Design Inventory v0.1

## Review status

Final-review inventory completed. No D03 implementation or freeze exists.

## Governing D03 design artifacts reviewed

| # | Artifact | Governing subject |
|---:|---|---|
| 1 | `D03_D04_INPUT_INVENTORY_V0_1.md` | Exact D04 23-field and candidate 6-field input inventory |
| 2 | `D03_DECISION_CONTROL_ARCHITECTURE_TRACE_V0_1.md` | System role, chain, boundaries, hierarchy |
| 3 | `D03_INPUT_CONTRACT_V0_1.md` | D03Input and 12-field DecisionContext |
| 4 | `D03_INPUT_SCHEMA_V0_1.json` | Machine-readable input authority |
| 5 | `D03_DECISION_CONTROL_CONTRACT_V0_1.md` | Desired-state and transition semantics |
| 6 | `D03_DECISION_SCHEMA_V0_1.json` | Machine-readable 21-field output |
| 7 | `D03_DETERMINISTIC_DECISION_TABLE_V0_1.md` | Human-readable target/transition rules |
| 8 | `D03_DETERMINISTIC_DECISION_TABLE_V0_1.json` | Machine-readable 13 target and 7 transition rules |
| 9 | `D03_CONTROL_STATE_AND_LIFECYCLE_V0_1.md` | Statelessness, lifecycle, overrides, re-enable |
| 10 | `D03_REPLAY_DECISION_COMMITMENT_V0_1.md` | Identity, canonicalization, durable commitment |
| 11 | `D03_D04_INTERFACE_CONSISTENCY_REVIEW_V0_1.md` | D04/D03 boundary review |
| 12 | `D03_DESIGN_AMBIGUITIES_V0_1.md` | Previously resolved policy ledger |

Repository search found no additional pre-review D03 governing artifact.

## Current frozen authority links

- D01 architecture freeze: `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235`.
- D02 design freeze: `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`.
- D02 implementation freeze: `C8029C4B9608547BBF7960F05E4F8613480C4FB2BF8594D94482516B954F7E72`.
- D04 current implementation freeze: `F72A86B3085BD11D8626F06F1FE3FAEDDE60570365488176011239382A46F1AF`.
- D04 current implementation manifest: `910845BF7ABF902EF8F02D1BFC98FF4EB2EFCC0847E2EEB8384859EAA207BCED`.

## Exact contract inventory

- D04Evaluation: 23 top-level fields.
- CandidateEnvelope: 6 fields, including immutable `path_direction`.
- DecisionContext: 12 required fields, no optional fields and no defaults; each evaluation treats it as an immutable causal snapshot supplied by its named owner.
- D03Decision: 21 required committed fields.
- Direct D01 inputs: 0.
- Direct D02 inputs: 0.
- Future/outcome/P&L inputs: 0.

## DecisionContext classification

| Fields | Classification | Mutable inside D03 | Default | Decision influence |
|---|---|---:|---|---|
| `context_time`, `entity_id`, `control_state_valid` | operational validation/control | No | None | timing, join, fail-closed gate |
| `actual_position_state`, `position_candidate_id`, `position_source_return_shape_model_time` | current position/control state | No | None | target comparison and lineage |
| `pending_target_state`, `pending_decision_id` | current execution-control state | No | None | duplicate/retarget transition overlay |
| `execution_available` | execution availability | No | None | authorization/BLOCKED overlay |
| `system_enabled`, `trading_enabled`, `emergency_flatten` | safety/operator control | No | None | override precedence |

All are required and causal at `context_time`. None is a market predictor or future outcome.

## Review-artifact status

The final-review artifacts and validator are evidence only. The seven committed-output gaps were reconciled in the unfrozen governing design and mechanically closed. This inventory is eligible for inclusion in the design manifest after final review verification.

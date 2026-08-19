# D03 Design-to-Implementation Traceability v0.1

Canonical authority: `D03_DETERMINISTIC_DECISION_TABLE_V0_1.json`.

| Rule | Frozen behavior | Implementation | Tests | Status |
|---|---|---|---|---|
| V00 | reject invalid input, no record | model validators; `evaluate_decision` | exhaustive invalid classes | PASS |
| R10 | emergency flatten | `_resolve_target_rule` | emergency precedence; exhaustive | PASS |
| R20 | system-disabled preservation | `_resolve_target_rule`; `evaluate_decision` forced transition | disabled matrix; exhaustive | PASS |
| R21 | trading-disabled preservation | `_resolve_target_rule`; `evaluate_decision` forced transition | disabled matrix; exhaustive | PASS |
| R30 | D04 safety closure | `_resolve_target_rule` | exhaustive | PASS |
| R31 | closed envelope | `_resolve_target_rule` | exhaustive | PASS |
| R32 | opening envelope | `_resolve_target_rule` | exhaustive | PASS |
| R33 | closing envelope | `_resolve_target_rule` | exhaustive | PASS |
| R34 | absent candidate | `_resolve_target_rule` | exhaustive | PASS |
| R35 | invalidated candidate | `_resolve_target_rule` | exhaustive | PASS |
| R36 | qualified FLAT candidate | `_resolve_target_rule` | qualified-FLAT lineage; exhaustive | PASS |
| R40 | qualified UPWARD candidate | `_resolve_target_rule` | directional mapping; exhaustive | PASS |
| R41 | qualified DOWNWARD candidate | `_resolve_target_rule` | directional mapping; exhaustive | PASS |
| T00 | pending target conflict | `_transition_intent` | T00 boundaries; exhaustive | PASS |
| T10 | same target pending | `_transition_intent` | T00 boundaries; exhaustive | PASS |
| T20 | already aligned | `_transition_intent` | 3x3 matrix; exhaustive | PASS |
| T21 | open required | `_transition_intent` | 3x3 matrix; exhaustive | PASS |
| T22 | close required | `_transition_intent` | 3x3 matrix; exhaustive | PASS |
| T23 | opposed position | `_transition_intent` | 3x3 matrix; exhaustive | PASS |
| A00 | execution unavailable | `_overlay_rule` | BLOCKED test; exhaustive | PASS |

Cross-cutting frozen contracts are mapped as follows:

| Contract | Implementation | Tests | Status |
|---|---|---|---|
| 12-field DecisionContext | `DecisionContext` | schema-name/count; invalid classes | PASS |
| 21-field immutable output | `DecisionRecord` | complete-field oracle; immutability | PASS |
| deterministic reason ordering | `evaluate_decision` | complete-field oracle | PASS |
| deterministic rule identity | `evaluate_decision` | complete-field oracle | PASS |
| candidate lineage | `_resolve_target_rule` | lineage and supersession tests; exhaustive | PASS |
| deterministic decision identity | fingerprint/identity helpers | repeatability and fresh-process digest | PASS |
| stateless re-enable | pure public entry point | re-enable candidate A/B test | PASS |
| feed/replay equivalence | transport absent from runtime | all 7,680 classes under both labels | PASS |

Frozen rules mapped: 20/20. Unmapped rules: 0. Untested frozen rules: 0.

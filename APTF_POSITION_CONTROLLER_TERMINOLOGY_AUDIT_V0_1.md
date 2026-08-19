# APTF Position Controller Terminology Audit V0.1

Status: COMPLETE
Date: 2026-08-18

## Method And Totals

A case-insensitive mechanical scan covered Python, Markdown, JSON, YAML, and TOML source/document artifacts. Large generated output ledgers were excluded from line enumeration but their schemas/hand-off documentation were included. Result: **261 matches on 236 lines across 57 files**.

Classification:

- **A - LEGACY INTERNAL FIELD NAME:** frozen code/schema/test/ledger identifier retained for compatibility.
- **B - EXTERNAL SEMANTIC TERMINOLOGY:** prose that presents internal state as externally authoritative "Actual Position"; clarified by the new semantic contract.
- **C - BROKER-SOURCED VALUE:** **zero occurrences found**.
- **D - OTHER:** historical quotation, prohibition, audit finding, generic comparison, or explicit statement that the value is not broker sourced.

No existing occurrence was edited. Frozen authorities and historical evidence remain byte-identical.

## File-By-File Occurrence Inventory

`A/B` means the artifact contains both literal legacy identifiers and prose semantic interpretation. "Addendum" means the existing frozen/current artifact is preserved and this semantic contract governs external interpretation.

| Artifact | Lines / matches | Class | Artifact disposition |
|---|---:|---|---|
| APTF_CAUSAL_PIPELINE_EVENT_CADENCE_AUDIT_V0_1.md | 1 / 2 | B | Historical diagnostic; preserve |
| APTF_CAUSAL_PIPELINE_INTEGRATION_PATH_AUDIT_V0_1.md | 1 / 1 | B | Historical diagnostic; preserve |
| APTF_D03_DECISION_CONTEXT_FIELD_MATRIX_V0_1.md | 4 / 5 | A/B | Historical D03 diagnostic; preserve |
| APTF_D03_DESIRED_POSITION_ASSIGNMENT_TRACE_V0_1.md | 4 / 4 | B | Historical D03 evidence; preserve |
| APTF_D03_DESIRED_POSITION_BOUNDARY_DECISION_POINT_V0_1.md | 3 / 3 | B | Historical decision point; preserve |
| APTF_D03_DESIRED_POSITION_TRUTH_TABLE_V0_1.md | 1 / 1 | B | Historical truth-table heading; preserve |
| APTF_D03_LONG_SHORT_FLAT_CAUSAL_TRACE_V0_1.md | 4 / 4 | B | Historical causal evidence; preserve |
| APTF_D04_CAPTURABILITY_DIAGNOSTIC_DECISION_POINT_V0_1.md | 1 / 1 | D | Explicit non-change scope; unaffected |
| APTF_D04_D03_INTERFACE_AUDIT_V0_1.md | 4 / 4 | A/B | Historical interface audit; preserve |
| APTF_D04_D03_POSITION_CONTROLLER_SEMANTIC_AUDIT_V0_1.md | 3 / 3 | B | Historical semantic audit; preserve |
| APTF_D04_D03_RESPONSIBILITY_CLASSIFICATION_V0_1.md | 2 / 2 | B | Historical responsibility audit; preserve |
| APTF_D04_FIXED_CONTEXT_CONTRACT_AUDIT_V0_1.md | 2 / 2 | A/B | Historical blocked experiment; preserve |
| APTF_D04_FIXED_CONTEXT_VALUES_V0_1.json | 1 / 2 | A/B | Historical evidence; preserve |
| APTF_DIRECTION_DESIRE_EXECUTION_SEPARATION_AUDIT_V0_1.md | 2 / 2 | B | Historical audit; preserve |
| APTF_FIXED_CONTEXT_EXPERIMENT_DECISION_POINT_V0_1.md | 2 / 3 | A/B | Historical decision point; preserve |
| APTF_PHASE_2_REAL_INTEGRATION_DELIVERABLES_INVENTORY.md | 2 / 2 | A | Legacy ledger fields; preserve |
| APTF_PHASE_2_REAL_INTEGRATION_HANDOFF.md | 1 / 2 | A | Legacy ledger field inventory; preserve |
| APTF_POSITION_ACTION_CAUSALITY_AND_NON_DRIFT_REVIEW_V0_1.md | 1 / 1 | B | Frozen design evidence; addendum governs external meaning |
| APTF_POSITION_ACTION_DESIGN_V0_1_MANIFEST.json | 1 / 1 | B | Frozen manifest; preserve |
| APTF_POSITION_CONTROLLER_SINGLE_INPUT_TEMPORAL_CONTRACT_V0_1.md | 1 / 1 | B | Historical diagnostic, not frozen authority; preserve |
| APTF_POSITION_EXECUTION_STATE_AUTHORITY_V0_1.md | 4 / 5 | B | Frozen current authority; semantic addendum required, original preserved |
| APTF_POSITION_TRANSITION_CONTROLLER_DESIGN_V0_1.md | 5 / 5 | B | Frozen current authority; semantic addendum required, original preserved |
| APTF_POSITION_TRANSITION_PLAN_SCHEMA_V0_1.json | 3 / 4 | A | Frozen schema identifiers; retain unchanged |
| APTF_POSITION_TRANSITION_VECTORS_V0_1.json | 1 / 1 | A | Frozen invalid-input label; retain unchanged |
| APTF_REAL_INTEGRATION_FREEZE_MANIFEST_V0_2.json | 3 / 3 | A | Frozen harness/ledger interface identifiers; retain |
| APTF_REAL_PIPELINE_CAUSALITY_DETERMINISM_AUDIT_V0_2.md | 14 / 16 | A/B | Historical integration evidence; preserve |
| APTF_REAL_PIPELINE_ZERO_MOCK_AUDIT_V0_2.md | 7 / 8 | A/B | Historical integration evidence; preserve |
| aptf_runtime/src/aptf_runtime/single_observation_pipeline.py | 5 / 5 | A | Frozen internal constant/context field; retain |
| APTF_SIX_ACTION_VERB_RESPONSIBILITY_MATRIX_V0_1.md | 4 / 4 | B | Historical/frozen design evidence; addendum governs terminology |
| APTF_TEST_001_ROW_10_COMPONENT_TRACE_V0_1.json | 4 / 4 | A | Historical machine evidence; do not modify |
| APTF_TEST_001_ROW_10_DECISION_CAUSAL_TRACE_V0_1.md | 3 / 3 | A/B/D | Historical evidence explicitly says not broker sourced; do not modify |
| APTF_TEST_001_ROW_10_INPUT_V0_1.json | 1 / 1 | A | Historical D03 field; do not modify |
| APTF_TEST_001_ROW_10_MATHEMATICAL_TRACE_V0_1.md | 3 / 3 | A/B | Historical evidence; do not modify |
| APTF_TEST_001_ROW_10_RESULT_V0_1.md | 2 / 2 | B/D | Historical evidence explicitly says not broker sourced; do not modify |
| APTF_TEST_001_ROW_10_SINGLE_OBSERVATION_PLAN_V0_1.md | 2 / 2 | A/B/D | Historical evidence explicitly says not broker data; do not modify |
| APTF_TWO_ROW_DIRECTION_PROPAGATION_TRACE_V0_1.json | 1 / 1 | A | Historical captured field; preserve |
| D03_CONTROL_STATE_AND_LIFECYCLE_V0_1.md | 4 / 4 | B | Frozen/current D03 design; external meaning clarified, original preserved |
| d03_decision_control/src/d03/v01/__init__.py | 12 / 12 | A | Frozen D03 implementation field; retain |
| d03_decision_control/tests/test_d03_decision_control.py | 13 / 14 | A | Frozen tests/fixtures; retain |
| d03_decision_control/tests/test_exhaustive_conformance.py | 2 / 2 | A | Frozen test payload fields; retain |
| D03_DECISION_CONTROL_ARCHITECTURE_TRACE_V0_1.md | 3 / 4 | A/B | Frozen D03 design evidence; clarify externally, preserve |
| D03_DECISION_CONTROL_DESIGN_V0_1_MANIFEST.json | 1 / 1 | B | Frozen manifest wording; preserve |
| D03_DECISION_SCHEMA_V0_1.json | 1 / 2 | A/B | Frozen source-field name plus semantic prose; retain schema, clarify externally |
| D03_DESIGN_AMBIGUITIES_V0_1.md | 1 / 1 | B | Frozen design resolution; preserve |
| D03_DETERMINISTIC_DECISION_TABLE_V0_1.json | 1 / 1 | A | Frozen policy expression; retain |
| D03_FINAL_DESIGN_INVENTORY_V0_1.md | 1 / 1 | A/B | Frozen field inventory; preserve |
| D03_INPUT_CONTRACT_V0_1.md | 2 / 2 | A/B | Frozen contract; legacy field retained, external meaning clarified |
| D03_INPUT_SCHEMA_V0_1.json | 3 / 3 | A/B | Frozen schema field/constraints; retain unchanged |
| D03_REPLAY_DECISION_COMMITMENT_V0_1.md | 1 / 1 | B | Frozen replay commitment; preserve |
| design_validation/validate_d03_design_v01.py | 6 / 6 | A | Frozen design validator identifiers; retain |
| diagnostics/aptf_test_001_row_10.py | 9 / 11 | A | Test 001 isolated historical harness; preserve |
| position_transition_controller/APTF_POSITION_TRANSITION_CONTROLLER_IMPLEMENTATION_TRACE_V0_1.md | 10 / 11 | A/B | Frozen implementation trace; original preserved, addendum governs terminology |
| position_transition_controller/causal_replay_harness.py | 11 / 13 | A/B | Frozen legacy harness identifiers/comments; retain |
| position_transition_controller/main_real_integration_v0_2.py | 1 / 1 | A | Frozen constructor argument; retain |
| position_transition_controller/position_transition_controller.py | 22 / 23 | A/B | Frozen implementation names/docstrings; retain; no math/code change |
| position_transition_controller/real_causal_replay_harness_v0_2.py | 17 / 23 | A/B | Frozen integration state/ledger names; retain; not broker sourced |
| position_transition_controller/test_controller.py | 12 / 12 | A | Frozen tests/variables; retain |

Totals above account for all 57 enumerated files, 236 matching lines, and 261 matches.

## Temporal Artifact Review

The frozen Temporal Event Envelope V0.2 design, schema, implementation documentation, clock design, identity implementation, wrappers, and proof contain no "actual position" semantic field or prose claim. They are **UNAFFECTED**. A new additive temporal addendum records that E5 is externally interpreted as `POSITION CONTROLLER DECISION` and that unchanged payload state fields are internal.

The frozen runtime's `single_observation_pipeline.py` contains five legacy internal occurrences (`ACTUAL_POSITION_SNAPSHOT`, `actual_position_state`, and uses). They are category A and remain byte-identical. No user-facing `ACTUAL POSITION` heading exists in the current replay CSV generator.

## Required Classification Conclusions

### A - Legacy Internal Field Names

Includes all snake-case code/schema/test/ledger identifiers and class names in the inventory: `actual_position_state`, `actual_position_snapshot`, `actual_position_before`, `actual_position_after`, `actual_position`, and `ActualPositionState`. These remain unchanged.

### B - Misleading External Semantics

The frozen Position Controller design/state authority and related D03 prose call the snapshot authoritative `ActualPosition`, "confirmed established exposure," or "realized" position. Those claims are not supported by a broker source in the current analytical implementation. They remain historical/frozen text but are superseded for external interpretation by `Position Controller internal state`.

### C - Broker-Sourced Values

**NONE.** No current analytical code reads a broker/account position, fill, reconciliation result, or broker timestamp. Broker adapters are design consumers only and are not implemented.

### D - Other

Includes explicit prohibitions, quoted test headings, generic references in historical audits, and Test 001 statements that correctly identify harness replay state as not broker sourced.

## Artifact Disposition Summary

### Current Authority - Addendum Required

- frozen Position Action Design V0.1 family, especially controller design, state authority, D03 integration, transition schema/matrix;
- frozen D03 contract family where legacy state terminology appears;
- Temporal Event Envelope V0.2 external E5 interpretation.

These originals are not edited. The new semantic contract and temporal addendum provide the current clarification.

### Historical Evidence - Do Not Modify

- all Test 001 artifacts and diagnostic harness;
- Phase 2 integration handoff/inventory;
- real-pipeline audits and historical replay harness evidence;
- earlier D03/D04 diagnostic audits and decision points;
- frozen implementation traces, tests, vectors, and validators.

### Unaffected

- D01, D02, D04 mathematics and documentation not containing the term;
- Temporal Event Envelope schema, clock, identity, and wrapper implementation;
- six-verb ontology and nine transition rows mathematically.

## Implementation Review

No runtime implementation or presentation change is required. All occurrences in frozen source are internal names. Existing user-facing CSV output uses `APTF_desired_position` and `APTF_position_action`. Future narrative reports are governed by the semantic contract and must use `D03 POSITION`, `POSITION CONTROLLER DECISION`, and optional `INTERNAL CONTROLLER STATE BEFORE DECISION`.

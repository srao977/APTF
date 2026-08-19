# D03 Decision Control Implementation Trace v0.1

## Authority and inventory

The implementation authority is `D03_DECISION_CONTROL_DESIGN_V0_1_FREEZE.json`, whose manifest SHA256 is `1BDE7D10D7687B2B02A569591BE203C2D35614EB24C432599219377194231BEF`. All 21 design-manifest entries and all referenced upstream authorities were verified before conformance work.

Runtime inventory:

| Surface | File | Symbol |
|---|---|---|
| Package metadata | `d03_decision_control/pyproject.toml` | project configuration |
| Package root | `d03_decision_control/src/d03/__init__.py` | package namespace |
| Input models | `d03_decision_control/src/d03/v01/__init__.py` | `D03Input`, `DecisionContext` |
| Output model | same | `DecisionRecord` |
| Validation boundary | same | model validators, `InvalidD03InputError` |
| Target precedence | same | `_resolve_target_rule` |
| Transition and T00 | same | `_transition_intent` |
| Execution overlay | same | `_overlay_rule` |
| Reasons and rule ID | same | `evaluate_decision` |
| Candidate lineage | same | `_resolve_target_rule` |
| Fingerprints and identity | same | `_canonical_json`, `_sha256_hex`, `_exact_float_string` |
| Public entry point | same | `evaluate_decision` |
| Focused tests | `d03_decision_control/tests/test_d03_decision_control.py` | 34 collected cases |
| Exhaustive oracle tests | `d03_decision_control/tests/test_exhaustive_conformance.py` | 6 collected cases |
| Fresh-process checker | `d03_decision_control/tests/fresh_process_digest.py` | 7,680-record digest |

## Contract realization

D03 consumes the authoritative 23-field `aptf_d04.models.envelope_state.EnvelopeEvaluation` and an explicit 12-field `DecisionContext`. The nullable D04 candidate has six fields. `DecisionRecord` has the frozen 21 fields and is immutable. The runtime imports D04 but has no D01 or D02 import.

Direction is read only from `candidate_envelope.path_direction`: `UPWARD -> LONG`, `DOWNWARD -> SHORT`, and `FLAT -> FLAT`.

## Evaluation path

1. Pydantic schema validation and D03 semantic validation reject invalid input before commitment.
2. `R10` emergency flatten has highest target precedence.
3. `R20`/`R21` disabled preservation force `NO_CHANGE` and `TRANSITION:NONE`.
4. `R30` through `R41` resolve current D04 safety, lifecycle, candidate status, and candidate direction.
5. `T00` through `T23` derive transition intent. T00 requires pending target non-NONE AND desired different from pending.
6. `A00` converts an actionable transition to `BLOCKED` only when execution is unavailable.
7. `evaluate_decision` creates the complete immutable record with deterministic fingerprints and identity.

## Conformance

The frozen validator was loaded as the independent oracle. All 7,680 frozen valid classes matched across all 21 fields, all 11 invalid classes rejected before commitment, and repeated evaluations produced no nondeterminism. D03 40/40, D04 79/79, D02 26/26, and D01 v0.2 50/50 passed.

## Verdict

PASS - implementation complete and freeze-ready.

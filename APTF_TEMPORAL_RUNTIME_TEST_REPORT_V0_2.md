# APTF Temporal Runtime Test Report V0.2

Status: PASS
Date: 2026-08-18
Runtime: Python 3.13.7

## New Runtime Tests

Command: `PYTHONPATH=aptf_runtime/src python -m pytest aptf_runtime/tests -q`

Result: **8 passed**.

Covered: Draft 2020-12 envelope schema in local and distributed profiles; deep immutability; canonical UUIDv4 enforcement; immutable event time; observation-ID determinism and source-identity collision resistance; logical-event determinism; execution uniqueness; parent lineage and inheritance; sequence semantics; aware UTC enforcement; same-domain nanosecond subtraction; cross-domain rejection; wall-clock inversion; ERROR envelope; canonical payload hashing; retry identity separation; payload/state non-drift; complete terminal plan; real single-observation E0-E5 lineage.

## Existing Regression Tests

All suites ran unchanged using existing Python and local source paths:

| Area | Test Selection | Result |
|---|---|---|
| D01 | `d01_adaptive_parametric_model/tests` | PASS |
| D02 | `d02_return_shape/tests` | PASS |
| D04 | `d04_trading_envelope/tests` | PASS |
| D03 | `d03_decision_control/tests` | PASS |
| Position Controller | `test_controller.py`, `test_small_real_integration_v0_2.py` | PASS |

The controller suite emitted six pre-existing `PytestReturnNotNoneWarning` warnings because legacy tests return lists; all six selected tests passed. Initial D04/D03 collection commands omitted transitive local source paths; corrected commands supplied the unchanged D02/D04 paths and passed. No test or frozen source was changed.

## Additional Validation

- New package compile/import: PASS
- VS Code diagnostics for `aptf_runtime`: none
- Package schema JSON parse: PASS
- Package schema hash equals frozen schema hash `954b4262a1a1931556045504f19b3bd1c21c85ec49fa996dde40b5f43047e64b`: PASS
- Single real target proof: PASS
- Protected hashes: 30/30 PASS

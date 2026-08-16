# D01 v0.1.2 Structural Basis Changelog

## Scope
Structural dependency resolution precheck only.
No predictive replay.
No D01 adaptive math changes.

## Added
- Structural basis utilities in src/aptf_d01/features/structural_independence.py.
- Structural precheck runner in scripts/run_structural_dependency_resolution_pass.py.
- Structural unit tests in tests/test_v012_structural_independence.py.

## Behavior
- Uses Phase 1 only for basis discovery.
- Freezes retained basis and validates rank/conditioning on Phase 2 and Phase 3.
- Writes structural artifacts under output/historical_exp001b_precheck/structural_dependency_pass.
- Stops after structural decision; does not run EXP001B replay.

## Determinism
- Deterministic feature ordering is applied before rank selection.
- Basis hash is emitted per experiment manifest.

## Validation Gates
- Full-rank required across frozen basis matrices.
- Severe ill-conditioning and singular matrices are blocking states.
- Any non-finite basis value is a blocking state.

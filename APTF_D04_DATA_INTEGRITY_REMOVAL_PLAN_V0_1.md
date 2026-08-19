# APTF D04 Data-Integrity Removal + Test 004R Plan V0.1

Status: AUTHORIZED NARROW CORRECTION
Date: 2026-08-18

## Architectural Finding

Observation quality is an upstream admission responsibility. The current D04 executable incorrectly receives `data_integrity`, uses it in H and safety, makes it the sole active G determinant, emits G in capturability/evaluation payloads, and multiplies C by G.

Mechanical pre-change proof:

```text
C = H * Q_G * Q_S * Q_R * G
G = min(active known configured dimensions)
active G = {data_integrity: 1.0}
additional producer-backed G determinants = none
```

The equation-change stop condition is not triggered.

## Phase A

1. Remove `data_integrity` from `EnvelopeContext`, production construction, provenance, and all D04 callers.
2. Remove the integrity threshold from D04 configuration, model construction, H, safety, reasons, and diagnostics.
3. Remove executable feasibility-gate configuration and active-gate construction.
4. Remove `feasibility_gate_score` and `gate_dimension_values` from current capturability and envelope results.
5. Set current executable capturability to `C = H * Q_G * Q_S * Q_R` without a neutral/default G representation.
6. Preserve Q_G, Q_S, Q_R, remaining H logic, aperture, thresholds, hysteresis, lifecycle, D03, controller, and temporal behavior.
7. Keep future gate concepts only as future/non-executable design discussion with no current producer or numeric assignment.

## Phase B

Run one continuing Test 004R pipeline over exactly physical rows 10-14 using the original Test 004 input authority and pre-row-10 state semantics. Stop before row 15. Compare source, D01, D02, Q_G, Q_S, Q_R, H, C, D04 semantics, D03 semantics, and controller semantics against immutable Test 004 evidence. Treat only provenance/content identities as expected changes.

## Validation

- Focused D04 equation/unit tests immediately after the first code edit.
- Complete D04 tests after fixture/schema updates.
- Static absence scan for executable `data_integrity`, G construction, neutral replacement multipliers, and emitted G fields.
- Exact five-cycle equation reconstruction and historical C comparison with zero tolerance.
- Temporal structure validation without runtime-duration equality.
- Post-test protected hash audit.

Historical Test 004 and Test 004A artifacts are immutable and excluded from correction edits.

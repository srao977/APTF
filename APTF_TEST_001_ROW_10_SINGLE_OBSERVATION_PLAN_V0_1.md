# APTF Test 001 Row 10 Single-Observation Plan V0.1

Status: EXECUTED READ-ONLY TEST EVIDENCE
Date: 2026-08-18

## Scope

Inspect exactly one real target: physical CSV row 10 of `data/market/normalized/SPY_1min_normalized_v0_1.csv`, where physical row 1 is the header. Consume earlier rows only to establish frozen causal state. Do not read physical row 11 or later, tune parameters, alter frozen code/configuration/freezes, evaluate future prices, or perform Azure work.

## Preconditions

1. Mechanically stream physical rows 1-10 only and confirm target identity.
2. Verify D01, D02, D04, D03, Position Controller, and Temporal Runtime V0.2 bindings before execution.
3. Stop on ambiguity or hash mismatch.

Pre-test result: 30/30 protected inventory hashes and 20/20 Temporal Runtime freeze references matched. Temporal implementation freeze SHA256: `4e23eae07adc848614f71842c97c49271a1d22db6624d3d85e427a92ff02296a`.

## Causal Procedure

1. Instantiate the unchanged `RealCausalReplayHarness` with its default explicit pre-row-1 LONG replay initial condition.
2. Process data indices 0-7 only as warm-up through the real D01, D02, D04, D03, and controller; carry actual position using the harness's existing semantic-success advancement.
3. Do not publish warm-up payloads as target results.
4. Select data index 8 (physical row 10) as the sole target.
5. Wrap target execution E0-E5 with frozen Temporal Runtime V0.2.
6. Capture exact target inputs, outputs, contracts, current-position provenance, and telemetry.
7. Assert last data index read is 8, target count is 1, parent lineage is complete, market time and observation identity are preserved, and all durations are nonnegative.
8. Re-hash all protected authorities after artifact creation.

## Existing Integration Inputs

The test does not invent a position. The frozen integration starts with `ActualPositionState(state="LONG", version=0, identity="INITIAL")`, describes it as an explicit `REPLAY_INITIAL_CONDITION`, and carries it forward after authorized semantic plans. This is harness-maintained replay state, not broker data.

The integration also constructs D04 with `critical_data_integrity_threshold=0.0`; package `default.yaml` contains `0.2`. Test 001 uses the existing harness construction unchanged. Target data integrity is `1.0`, so neither threshold would trigger the target safety check. This statement is provenance, not a counterfactual test.

## Artifacts

The seven requested files are test evidence only and establish no new component authority. The isolated harness is `diagnostics/aptf_test_001_row_10.py`; it calls frozen components and does not duplicate their mathematics.

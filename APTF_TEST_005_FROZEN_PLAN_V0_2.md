# APTF Test 005 Frozen D04 100-Minute Empirical Plan V0.2

Run ID: `TEST005_FROZEN_D04_V0_2_RUN_001`  
Freeze ID: `D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1`  
Freeze manifest SHA-256: `a437cdb63bc7fe4aecdeece8ebd01082a62753774ad9ff7d93ee900eee3e4b79`  
Source data SHA-256: `73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`  
Execution timestamp: `2026-08-18T21:54:17.859037Z`  
Status: PRE-EXECUTION

## Authority Gate

Before market processing, mechanically verify all five freeze artifacts, the exact freeze ID/status/readiness, 17/17 frozen authority hashes, 8/8 Test 004R evidence hashes, Test 004R PASS/60, the four-factor source equation, removed-term absence, thresholds `0.75/0.55`, and persistence `3/2`. Record the result in `APTF_TEST_005_FROZEN_PREEXECUTION_AUTHORITY_V0_2.json`. A failure permits zero pipeline observations.

## Source And Initialization

Use only `data/market/normalized/SPY_1min_normalized_v0_1.csv`. Physical row 1 is the header. Replay physical rows 2-14 as unmeasured real-data warm-up in a new process. Prove the resulting D01/D04/controller state equals Test 004R after physical row 14 and record its canonical fingerprint. Measure exactly physical rows 15-114. Never request row 115.

## Execution

Use one synchronous process and continuous recursive state. Every measured observation completes E0 Source, D01, D02, D04, D03, and Position Controller before the next row is requested. Capture full source, D01 DMO/FMO, D02 ReturnShape, four D04 factors/C/state/counters, D03, controller, E0-E5 lineage, stage nanoseconds, and direct lifecycle nanoseconds. Reconstruct C exactly from four factors. Continue through all 100 rows regardless of semantic outcome.

## Analysis

Use population standard deviation and linear-interpolated percentiles at rank `(n-1)*p`. Preserve all individual records. Derive distributions, bands, proximity counts/runs, top/bottom observations, actual joint maximum, factor distributions/maxima/tie-aware lowest factors, C differences/runs, state/decision counts, source variation, large perturbations, and Pearson associations. Source/C association is descriptive and non-causal; factor/C association is structurally related by the product equation. No backward solving, tuning, counterfactual combinations, or threshold recommendation is authorized.

## Immutability

After cycle 100, recompute source, 17 frozen authority, 8 Test 004R evidence, five freeze artifact, and historical Test 004/004A inventory identities. Pipeline authority and test code are immutable after the pre-execution record is written.
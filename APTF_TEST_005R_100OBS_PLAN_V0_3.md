# APTF Test 005R 100-Observation Empirical D04 Plan V0.3

Run ID: `TEST005R_FROZEN_D04_100OBS_V0_3_RUN_001`  
Freeze ID: `D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1`  
Freeze manifest SHA-256: `a437cdb63bc7fe4aecdeece8ebd01082a62753774ad9ff7d93ee900eee3e4b79`  
Source SHA-256: `73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`  
Execution timestamp: `2026-08-18T22:08:15.120144Z`  
Status: PRE-EXECUTION

## Corrected Observation Contract

One measured observation is one literal source row. Process physical rows 15-114 in order. Preserve each source timestamp and calculate adjacent `delta_t_seconds`; positive intervals other than 60 seconds are source evidence, not failures. Do not interpolate, duplicate, skip, or search forward. Warm physical rows 2-14 in a new process and prove row-15 state identity against Test 004R.

## Frozen Authority

Require 17/17 frozen D04 hashes, 8/8 Test 004R hashes, the four-factor equation, removed-term absence, and thresholds/persistence `0.75/0.55`, `3/2` before execution. Use one synchronous stateful pipeline and complete E0-E5 for every measured row. No code or authority changes are permitted after the pre-execution record is written.

## Evidence

Persist exactly 100 records with source OHLCV/timestamps/delta-t, D01 DMO/FMO, D02 ReturnShape, D04 factors/C/state/counters, D03, controller, continuity, E0-E5 lineage, component nanoseconds, and direct nanoseconds. Reconstruct C exactly for every observation. Derive all requested distributions, runs, state/decision counts, source-time structure, source variation, associations, and post-execution identities without rerunning the pipeline.

Previous Test 005 V0.1/V0.2 evidence remains isolated and immutable. No threshold recommendation, backward solving, synthetic state, or causal claim is authorized.
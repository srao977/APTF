# APTF Test 005 100-Minute Empirical D04 Capturability Plan V0.1

Status: PRE-EXECUTION AUTHORIZED
Date: 2026-08-18

## Frozen Authority

Current D04 is mechanically verified as `C = H * Q_G * Q_S * Q_R`. Current executable source contains no `data_integrity`, G multiplier, feasibility-gate result, active-gate construction, arbitrary context input, or neutral multiplier. Authoritative configuration is open/close `0.75/0.55` with opening/closing persistence `3/2`.

## Source And State

Use `data/market/normalized/SPY_1min_normalized_v0_1.csv` without modification. Replay data observations 1-13 (physical rows 2-14) as unmeasured warm-up. Prove the resulting D01/D04/controller state equals Test 004R state after physical row 14. Then measure exactly 100 consecutive observations at physical rows 15-114. Do not request row 115.

## Execution

Use one synchronous Python process and one continuing D01/D04/controller state. Each measured observation executes E0 Source, D01, D02, D04, D03, and Position Controller before the next observation is read. Capture source OHLCV, complete D01 DMO/FMO, D02 ReturnShape, D04 evaluation and persistence counters, D03 decision, controller plan, state continuity, E0-E5 lineage, stage nanoseconds, and direct lifecycle nanoseconds.

For every cycle independently reconstruct `C = H * Q_G * Q_S * Q_R` with required exact error `0.0`. Emit a concise checkpoint every ten observations and immediate first-event notices without terminating early.

## Analysis

Derive distributions with population standard deviation. Percentiles use linear interpolation at rank `(n-1)*p`, equivalent to NumPy's default linear convention. Preserve all 100 ordered records. Calculate threshold bands/counts/runs, top/bottom observations, factor distributions/maxima/bottlenecks, D04/D03/controller counts, C differences/runs, source variation, Pearson descriptive associations, large-movement records, and temporal reconciliation. Associations are descriptive, not causal proof; factor/C association is structurally related by the product equation.

## Non-Drift

Hash source, D01, D02, D04, D03, Position Controller, temporal authority, D04 configuration, and all Test 004/004A/004R artifacts before and after. No authority or code changes are permitted after execution begins.
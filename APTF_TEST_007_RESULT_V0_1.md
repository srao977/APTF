# APTF Test 007 Long-Only Position Episode Reconstruction Result V0.1

Status: **PASS**  
Acceptance: **120/120 PASS**

Test 007 consumed only the immutable Test 006B observation-position CSV. Emitter executions, decision recalculations, reserve reruns, and decision modifications were all zero. No P&L, return, execution price, capital, shares, slippage, commission, spread, compounding, or future-outcome judgment was introduced.

## Source Authority

- Source: `APTF_TEST_006B_OBSERVATIONS_WITH_EMITTED_POSITION_V0_1.csv`
- SHA-256: `f4c4bcf3e03e37f99ff04444035915d8f28cc24dec6d16a22e32089ad83dbfd4`
- Rows: 101,221
- Columns: 39 = 22 original source + 17 Test 006B emitter fields
- Timestamp range: `2023-03-30T08:00:00Z` to `2023-09-29T23:48:00Z`
- Decisions: INITIALIZING 15, BUY 14,249, SELL 9,779, HOLD 77,178

The Test 007 observation map preserves all 39 fields row-by-row with zero source, decision, order, added-row, or lost-row discrepancies.

## Long-Only Episodes

- Total episodes: **2,051**
- COMPLETE: **2,051**
- OPEN_AT_END: **0**
- Overlapping: **0**
- Direct BUY→SELL: **0**
- Episodes containing HOLD: **2,051**
- Episodes containing repeated BUY: **1,665**

Every episode opened only on FLAT+BUY and closed only on LONG+SELL. IDs are deterministic `EP000001` through `EP002051`.

## Decision Decomposition

| Immutable decision | Structural use | Count |
|---|---|---:|
| BUY | EPISODE_OPEN | 2,051 |
| BUY | REPEATED_BUY_WHILE_LONG | 12,198 |
| SELL | EPISODE_CLOSE | 2,051 |
| SELL | UNMATCHED_SELL_WHILE_FLAT | 7,728 |
| HOLD | EPISODE_HOLD / maintain LONG | 39,787 |
| HOLD | FLAT_HOLD / remain FLAT | 37,391 |

Reconciliations:

- BUY: `2,051 + 12,198 = 14,249`
- SELL: `2,051 + 7,728 = 9,779`
- HOLD: `39,787 + 37,391 = 77,178`

## Episode Length And Time

Complete episode observation length:

- Minimum: 3
- Maximum: 193
- Mean: 27.346172598732327
- Median: 21

Actual elapsed source seconds:

- Minimum: 120
- Maximum: 296,340
- Mean: 3,782.106289614822
- Median: 1,380

No row count was substituted for elapsed time.

## HOLD And Repeated BUY Structure

HOLD counts per complete episode:

- Minimum: 1
- Maximum: 141
- Mean: 19.398829839102877
- Median: 15
- Zero-HOLD episodes: 0
- One-HOLD episodes: 69
- More-than-one-HOLD episodes: 1,982

Repeated BUY counts per complete episode ranged from 0 to 52, mean 5.947342759629449, median 4.

## Position Occupancy

Among 101,206 actionable observations:

- Ending LONG: 54,036 (`53.392091377981544%`)
- Ending FLAT: 47,170 (`46.607908622018456%`)

Source-time occupancy, assigning each interval to the preceding reconstructed state without market-calendar assumptions:

- LONG: 7,757,100 seconds
- FLAT: 8,110,980 seconds

This is structural state occupancy, not capital utilization.

## Structural Exceptions

- UNMATCHED_SELL_WHILE_FLAT: 7,728
- REPEATED_BUY_WHILE_LONG: 12,198
- FLAT_HOLD: 37,391
- OPEN_AT_END: 0
- Overlaps: 0

All exceptions are preserved in separate CSV audits and never forced into episodes.

## Primary Outputs

- `APTF_TEST_007_POSITION_EPISODES_V0_1.csv`: one row per episode, 2,051 rows.
- `APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv`: all 101,221 observations with structural fields appended.

Boundary OHLCV and H/Q_G/Q_S/Q_R/C are preserved. No execution-price interpretation is assigned.

## Test 008 Readiness

1. Emissions form coherent long-only episodes: **YES**, with explicit exceptions preserved.
2. BUYs opening LONG: **2,051**.
3. BUYs while already LONG: **12,198**.
4. SELLs closing LONG: **2,051**.
5. SELLs while FLAT: **7,728**.
6. HOLDs maintaining LONG: **39,787**.
7. HOLDs maintaining FLAT: **37,391**.
8. Complete episodes: **2,051**.
9. Episodes with HOLD: **2,051**.
10. Direct BUY→SELL episodes: **0**.
11. Episode open at end: **NO**.
12. Overlapping episodes: **0**.
13. Typical observation duration: median **21** observations.
14. Typical source-time duration: median **1,380 seconds / 23 minutes**.
15. Intended pattern is present, but the raw stream also contains many repeated BUYs and unmatched SELLs that the long-only state machine handles explicitly.
16. Episode records are sufficient for Test 008 without rerunning or modifying the Emitter: **YES**.
17. Test 008 is structurally ready to define an independent execution-price rule and fixed 100-share quantity: **YES, subject to human approval**.

## Integrity

Test 006B, Test 006A, Test 005R, frozen Adaptive Emitter, and historical D04 remained unchanged. Source CSV pre/post hashes match. No historical artifact was overwritten.

Next action: **STOP**. Do not calculate P&L or select execution prices in Test 007.
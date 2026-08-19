# APTF Test 005R 100-Observation Empirical Result V0.3

Run ID: `TEST005R_FROZEN_D04_100OBS_V0_3_RUN_001`  
Freeze ID: `D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1`  
Status: **PASS — RESULT C**  
Acceptance: **120/120 PASS**

## Source Time

Exactly 100 literal source observations, physical rows 15-114, were processed in order. Row 115 was not processed. Timestamps were strictly increasing and preserved. The actual source-time span was `7320.0` seconds. Of 99 adjacent measured pairs, `87` were 60 seconds and `12` were greater than 60 seconds; gaps did not invalidate the test.

## Capturability

- Range: `0.02642361014377076` to `0.5577135990257739`
- Mean: `0.27565420628366016`
- Median: `0.2733545607540699`
- Population standard deviation: `0.1104955540352167`
- P90/P95/P99: `0.4244788696399675` / `0.45139780658240114` / `0.5134883909218735`
- Maximum reconstruction error: `0.0` across 100/100 observations
- Counts C >= 0.55 / 0.70 / 0.75: `1` / `0` / `0`

Maximum actual C was `0.5577135990257739` at cycle `13`, physical row `27`, timestamp `2022-09-30T08:25:00Z`, with shortfall `0.1922864009742261` and simultaneous factors H/Q_G/Q_S/Q_R = `1` / `1.0` / `0.813182899101121` / `0.6858402945293873`.

## Semantics

- D04: CLOSED-only; counts `{'CLOSED': 100}`; transitions `0`.
- D03: FLAT-only; counts `{'FLAT': 100}`.
- Position Controller: NO_ACTION-only; decision counts `{'NO_ACTION': 100}`.

## Scientific Findings

1. C range was `0.02642361014377076` to `0.5577135990257739`.
2. C reached 0.55: `YES`.
3. C reached 0.70: `NO`.
4. C reached 0.75: `NO`.
5. Maximum C was `0.5577135990257739`, shortfall `0.1922864009742261`.
6. High-value persistence is recorded in the threshold-run artifact; longest >=0.55 run was `1` observations.
7. D04 opening observed: `NO`.
8. D04 OPEN observed: `NO`.
9. D03 non-FLAT observed: `NO`.
10. Controller non-NO_ACTION observed: `NO`.
11. BUY/SELL/HOLD counts: `0` / `0` / `0`.
12. Lowest-factor counts including ties: `{'Q_S': 36, 'Q_R': 64}`; ties `{}`.
13. Volume range: `100.0` to `12590.0`.
14. Close range: `364.94` to `366.71`.
15. Large perturbation comparisons and non-causal associations are recorded in the source-variation artifact.
16. Source timestamp gaps: `12`.
17. Actual source-time span: `7320.0` seconds.
18. Gap/non-gap C comparison is recorded as descriptive, non-causal evidence.
19. This observed sequence **SUPPORTS** the hypothesis that 0.75 lies substantially above the normal observed operating range over this source sequence. This is not a mathematical impossibility claim and no replacement threshold is recommended.

## Non-Drift

Frozen authority 17/17, Test 004R 8/8, freeze artifacts 5/5, source, prior tests, and test code remained unchanged. No architecture, threshold, persistence, or timestamp handling changed during the run.

Next action: **STOP**. Do not process row 115 or start another test.

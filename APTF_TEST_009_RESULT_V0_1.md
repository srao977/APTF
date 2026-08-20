# APTF Test 009 Causal First- and Second-Derivative Price-Cycle Analysis V0.1

Status: **PASS**  
Acceptance: **73/73 PASS**  
Empirical result: **MIXED, DIAGNOSTICALLY INFORMATIVE**

PASS means the analysis was causal, complete, immutable, and reconciled. It does not mean derivative alignment was economically favorable.

## Authority and causality

- Price field: source `close`, the frozen numeric mapping to completed-observation D01 `price`.
- Timestamp: actual `event_timestamp_utc`; gaps preserved.
- Runtime Core: 22/22 frozen files unchanged.
- Test 006B/007/008 authorities: 55/55 unchanged.
- Reserve Emitter reruns: 0.
- Source rows: 101,221.
- Initialization: 15 rows used as causal context only and excluded from scoring/cycles/alignment.
- Actionable rows: 101,206.
- Future observations used for primary D1/D2: 0.
- Centered derivatives/smoothing: none.

The repository authorizes `close` as the D01 numeric price state. It does not independently establish that source timestamps have an exchange `BAR_CLOSE` clock role; Test 009 uses them only for strict causal ordering and actual elapsed time.

## Derivative method

For each trailing window, actual UTC elapsed minutes are centered on the current observation, and a causal quadratic is fitted:

$$
P(\tau)=a\tau^2+b\tau+c,\qquad D1=b,\qquad D2=2a.
$$

Units are SPY price/minute and SPY price/minute². Independent recomputation matched six distributed 15-row fits exactly.

The empirical D1 distribution over 101,206 actionable rows was:

- Minimum: `-0.7229019973988144`
- Maximum: `0.7327113768594344`
- Mean: `0.00008823140647619507`
- Median: `0.00034069247038814865`
- Population standard deviation: `0.058297861123349934`

Absolute-D1 sensitivity thresholds:

- Q05: `0.0017320854030486998`
- Q10 primary: `0.0035332071428566536`
- Q15: `0.005440976485674653`

Q10 was fixed before alignment and P&L joins.

## Window study

| Window | Valid | D1 crossings | D2 sign changes | Single-row D1 reversal runs | Reversal-run rate | Median D1 persistence |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 101,206 | 62,435 | 67,931 | 37,289 | 59.7245% | 1 |
| 5 | 101,206 | 37,925 | 41,743 | 8,830 | 23.2828% | 2 |
| 8 | 101,206 | 24,141 | 26,422 | 3,329 | 13.7892% | 4 |
| 15 | 101,206 | 13,212 | 14,394 | 1,148 | 8.6884% | 7 |

Primary window: **15 observations**. All windows had equal fit coverage and zero numerical failures; window 15 had the lowest reversal/noise metrics and highest persistence. P&L and Emitter labels were not used.

## Crossings and cycles

- Upper D1 crossings: 6,606.
- Lower D1 crossings: 6,606.
- Upward derivative cycles: 6,605.
- Downward derivative cycles: 6,606.
- Mechanical crossing validation: 13,212/13,212.
- Turning trajectory rows: 409,536.
- Pre-BUY/pre-SELL trajectory rows: 65,632.

## Emitter alignment

All 2,051 immutable BUY transitions and 2,051 immutable SELL transitions were analyzed without changing an episode boundary, decision, or Position State.

BUY alignment:

- Preceded by the `D1<0,D2>0` run leading into the associated lower crossing: **1,185/2,051 (57.776694295465624%)**.
- Offset from preceding lower crossing: mean +6.779 observations / +867.411 seconds; median **+6 observations / +420 seconds**.
- Therefore BUY generally followed the detected lower crossing rather than preceding it.

SELL alignment:

- Entered `D1>0,D2<0` before SELL within the immutable episode: **1,260/2,051 (61.43344709897611%)**.
- Before nearest upper crossing: 954 (46.51389566065334%).
- At upper crossing: 249 (12.140419307654803%).
- After upper crossing: 848 (41.34568503169186%).
- Offset: mean +0.345 observations / -9.274 seconds; median **0 observations / 0 seconds**.
- SELLs cluster around upper crossings, with a modest plurality before them.

The signed mean seconds can differ in sign from mean observation offset because actual source gaps are preserved and a few large gaps dominate elapsed-time means.

## Does D2 lead D1?

**MIXED. D2 provides measurable precursor information, but not consistently enough to stand alone.**

Upper turns (`D1>0,D2<0` before upper crossing):

| Minimum contiguous run | Qualified | Coverage | Mean lead observations | Median | Mean seconds | Median seconds |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3,176 | 48.0775% | 1.7481 | 1 | 317.3804 | 60 |
| 2 | 1,266 | 19.1644% | 2.8768 | 2 | 272.7488 | 180 |
| 3 | 521 | 7.8868% | 4.1305 | 4 | 341.4587 | 240 |

Lower turns (`D1<0,D2>0` before lower crossing):

| Minimum contiguous run | Qualified | Coverage | Mean lead observations | Median | Mean seconds | Median seconds |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3,064 | 46.3821% | 1.6599 | 1 | 166.8799 | 60 |
| 2 | 1,156 | 17.4992% | 2.7491 | 2 | 189.7059 | 120 |
| 3 | 443 | 6.7060% | 3.9549 | 3 | 265.7336 | 240 |

The one-row signal appears before roughly half of turns; sustained two- and three-row signals are much less frequent. This is genuine incremental timing information relative to D1 sign, but its coverage is mixed.

## Test 008 descriptive timing

P&L was joined only after derivative selection and classification were fixed.

- WIN trades: BUY offset median +6; SELL offset mean -0.642, median -1.
- LOSS trades: BUY offset median +6; SELL offset mean +1.307, median 0.
- Losing trades more often sold after the local upper crossing and entered `FALLING_STRENGTHENING` at SELL; winning trades more often sold before the crossing and had greater `RISING_WEAKENING`/`UPPER_TURNING_REGION` representation.
- BUY timing was much less differentiated: wins and losses both had median +6 from the preceding lower crossing.

These are associations, not causal or optimized trading rules.

## Frozen internal values

- H was 1.0 in every derivative state and therefore did not distinguish states.
- Q_G means stayed near 0.98 and varied little.
- Q_S, Q_R, and C changed systematically by derivative state.
- `RISING_WEAKENING` had mean Q_S `0.6448555384`, Q_R `0.5251835556`, and C `0.3347889116`, versus `RISING_STRENGTHENING` C `0.2943235787`.
- `FALLING_WEAKENING` had mean Q_S `0.3780001807` and C `0.1776101370`, versus `FALLING_STRENGTHENING` Q_S `0.4909360774` and C `0.2422563150`.

The strongest descriptive candidates for later curve analysis are normalized price, D1, D2, Q_S, and C; Q_R is secondary. H and Q_G show little useful state variation here.

## Curve-fit readiness

Upper and lower trajectories each contain 6,606 crossings and nearly complete -15...+15 coverage. Median normalized-price paths show coherent opposite pre-crossing arcs, with median IQR around `0.0005`. This is sufficient to justify a separate **exploratory** curve-shape experiment using normalized price, D1, D2, Q_S, and C.

No curve family was selected, no curve was fitted into Runtime Core, and no diagnostic output was fed back into the Emitter.

## Direct answers

1. Derivative price field? **Source close.**
2. Every primary derivative causal? **Yes; current and prior rows only.**
3. Most mathematically stable window? **15 observations.**
4. Upper D1 crossings? **6,606.**
5. Lower D1 crossings? **6,606.**
6. BUYs preceded by weakening decline? **1,185/2,051, 57.776694295465624%.**
7. SELLs preceded by weakening rise? **1,260/2,051, 61.43344709897611%.**
8. D2 upper-turn lead? **At >=1 row: mean 1.748 observations/317.380 seconds; median 1/60. At >=2: mean 2.877/272.749; median 2/180. At >=3: mean 4.131/341.459; median 4/240.**
9. D2 lower-turn lead? **At >=1 row: mean 1.660 observations/166.880 seconds; median 1/60. At >=2: mean 2.749/189.706; median 2/120. At >=3: mean 3.955/265.734; median 3/240.**
10. SELL relative to upper crossing? **Around it: median 0; 46.51% before, 12.14% at, 41.35% after.**
11. BUY relative to lower crossing? **Generally after it: median +6 observations/+420 seconds.**
12. Losing-episode timing pattern? **Yes descriptively: later SELL timing and more FALLING_STRENGTHENING exits.**
13. Profitable-episode timing pattern? **Yes descriptively: SELL median one observation before crossing and more rise-weakening/upper-turn exits.**
14. Systematic H/Q trajectories? **H no; Q_G little; Q_S, Q_R, and C yes descriptively.**
15. D2 useful beyond D1 sign? **Mixed: measurable lead for many turns, limited sustained coverage.**
16. Stable enough for later curve fitting? **Yes for an exploratory, non-production experiment.**
17. Most suitable variables? **Normalized price, D1, D2, Q_S, C; Q_R secondary.**
18. Curve fitted into Runtime Core V0.1? **NO.**
19. Runtime Core V0.1 modified? **NO.**
20. Test 009 used to retune Emitter? **NO.**

## Evidence identities

- Final hash inventory: `APTF_TEST_009_ARTIFACT_HASHES_V0_1.json`.
- Derivative observations: `193a8ab789af3a79ac3b0e0f111a910f2ea5f20614223f6478a1145674051260`.
- Crossings: `2300c5bff99efc028b706d21bf63619dfa6a293750552b84f1eed3464b26a1a9`.
- Episode alignment: `feaa183a587cbcc75a389eba144dda819bfde3c2aa7ecdebd1641d936ca45baf`.
- Turning trajectories: `d6610d7010ed51609cf32b058080b3b5537d626e83e8f71670203455bf2fb957`.
- Emitter transition trajectories: `caa7a4fefe3fe2f937ac19b2fd7e63f553f7d7a065455361cfa8c4fe9e90649d`.
- D2 precursor analysis: `f6b3a06d31c49e4fb4b00642e19d5b6e6a6d41cf39338937a48e371732d9762f`.
- Summary: `f665c7fd25e6f37a03c75a22d73b3a8fd968c1fedb9642f0c56af9a53b85accf`.

Next action: **STOP FOR HUMAN REVIEW. Do not modify Runtime Core V0.1. Do not begin Test 010.**
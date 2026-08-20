# APTF Test 009V Causal Price + Volume Multivariate Trajectory Analysis V0.1

Status: **PASS**  
Acceptance: **120/120 PASS**  
Empirical result: **VOLUME IS NONREDUNDANT, BUT TURNING-SEPARATION VALUE IS MIXED**

PASS means the multivariate evidence is causal, complete, immutable, and disciplined. It does not authorize a trading rule, local dynamics model, or trajectory propagator.

## Authority and immutability

- Runtime Core V0.1: 22/22 unchanged.
- Full Test 009 envelope: 18/18 unchanged.
- Test 007/008 authorities: 35/35 unchanged.
- Frozen Test 009 price window: 15.
- Frozen Test 009 upper/lower crossings: 6,606/6,606; moved by Volume: 0.
- Frozen price geometry/state mismatches: 0 across 101,221×16 fields and 409,536 trajectory rows.
- Reserve Emitter reruns: 0.
- Runtime/Emitter/Position changes: none.

## Raw Volume

- Field: source `volume`, aligned on the same immutable row/timestamp as `close`.
- Valid/missing/zero: 101,221 / 0 / 0.
- Minimum/median/mean: 100 / 35,592 / 73,723.95652088005.
- Q90/Q95/Q99/maximum: 181,955 / 253,716 / 519,004.60000000085 / 4,822,591.
- Max/median: 135.4965×; Q99/median: 14.5821×; Q95/median: 7.1285×; Q90/median: 5.1122×.
- All extremes preserved; no clipping, winsorization, deletion, interpolation, or imputation.

Time-of-day structure is material: regular-session minute medians span 57,066 to 2,006,567, and regular-session median Volume is 101,624.5 versus 1,244 premarket and 1,400 after-hours. Extended-session minute semantics are coarse, so time-of-day normalization was evaluated descriptively but not selected as a candidate.

## Frozen Volume mathematics

Nine predictor-only candidates were evaluated: rolling median ratio, rolling mean ratio, and log rolling-median relative, each at 15/30/60 rows.

Primary V_N:

$$
V_N(t)=V_{RAW}(t)/\operatorname{median}(V_{RAW,t-14:t}).
$$

- Method/aperture: `ROLLING_MEDIAN_RATIO_15`.
- Future observations: 0.
- P&L/BUY/SELL/crossings used for selection: no.
- V_N≥2/5/10: 18,284 / 6,085 / 2,814 observations.
- Regimes: actionable V_N Q25/Q75/Q95 boundaries, labeled LOW/NORMAL/ELEVATED/EXTREME.

V1/V2 use a causal trailing quadratic on actual elapsed minutes. The predeclared coverage-first rule selected window 3:

- Valid: 101,205.
- V1 crossings: 70,036.
- V2 sign changes: 71,754.
- Single-row V1 reversal runs: 46,573 (66.4977%).
- Median V1 persistence: 1.

This is a serious noise limitation. Window 15 was much more stable (19.0783% reversal-run rate; median persistence 5) but had 12 fewer valid actionable fits. The rule was not changed after observing this result.

## Turning evidence

At both upper and lower crossings, median V_N was 1.0. Median V1/V2 were 0.2224/0.1776 upper and 0.1740/0.1579 lower.

| Evidence | Upper | Lower |
|---|---:|---:|
| Elevated within prior 3 | 2,598 (39.3279%) | 2,586 (39.1462%) |
| Extreme within prior 3 | 667 (10.0969%) | 661 (10.0061%) |
| Elevated within prior 15 | 5,934 (89.8274%) | 5,929 (89.7517%) |
| Extreme within prior 15 | 2,270 (34.3627%) | 2,265 (34.2870%) |

The valid ±3 non-turning baseline contains 28,768 rows. Its per-row elevated/extreme frequencies were 23.7868%/5.6834%, versus 19.6646%/4.9971% for upper precursor rows and 19.8868%/4.8950% for lower precursor rows. Volume extremes were not more concentrated in precursor rows.

Volume-regime stratification did not reduce frozen normalized-price trajectory dispersion: median IQR increased by 3.2531% upper and 4.6050% lower. Upper/lower price shapes remain repeatable, but the full Volume-augmented shape is highly dispersed.

## Trajectory separation

Upper precursor `P1>0,P2<0`:

- Immediate: 3,176; delayed 2-6: 3,105; return to strengthening: 1,562; other: 180.
- Median V_N: 0.966 immediate, 1.000 delayed, 1.000 return.
- Elevated/extreme frequency: 19.99%, 21.06%, 25.16%.

Lower precursor `P1<0,P2>0`:

- Immediate: 3,064; delayed: 2,740; return to strengthening: 1,399; other: 99.
- Median V_N: 0.962 immediate, 1.000 delayed, 1.024 return.
- Elevated/extreme frequency: 20.23%, 22.12%, 28.23%.

Return paths show somewhat higher Volume, but immediate/delayed medians are close and V1/V2 dispersion is large. Separation is **MIXED/WEAK**, not a trading signal.

## Relationships and P&L labels

Absolute Pearson/Spearman correlations between P1/P2 and V_N/V1/V2 were all below 0.019. Linear R² of Volume components from P1/P2 was:

- V_N: 0.0002800807.
- V1: 0.0000012756.
- V2: 0.0000004633.

This establishes representational nonredundancy, not independence or predictive utility. Joint-state output preserves 98 combinations, including states with one observation.

WIN/LOSS episode medians were close: BUY V_N 1.0/1.0118 and SELL V_N 1.0/1.0, with large dispersion. No material profitable-versus-losing Volume trajectory separation was established. P&L was descriptive only and never selected mathematics.

## Test 010 recommendation

Primary minimal candidate:

```text
X_010(t) = [P, P1, P2, V_N]
```

- STRONG: P, P1, P2.
- CONDITIONAL: V_N, Q_S, Q_R, C.
- WEAK: V1, V2, H, Q_G.

V_N is causal, interpretable, and nonredundant, but weakly turn-discriminative. V1/V2 should remain sensitivity-only until a chronologically validated test authorizes a more stable Volume derivative specification. Test 010 readiness is **CONDITIONAL**.

## Direct answers

1. Source Volume located? **Yes, `volume`.**
2. Price/Volume observation alignment? **Yes, 101,221/101,221.**
3. Raw min/median/Q90/Q95/Q99/max? **100 / 35,592 / 181,955 / 253,716 / 519,004.60000000085 / 4,822,591.**
4. Max/Q99/Q95/Q90 divided by median? **135.4965× / 14.5821× / 7.1285× / 5.1122×.**
5. Large Volume variation present? **Yes, over two orders of magnitude max/median.**
6. Selected normalization? **15-row causal rolling-median ratio.**
7. Why? **Maximum coverage/zero failure, then best fixed-15 reversal stability among full-coverage candidates.**
8. Baseline aperture? **15 observations.**
9. Volume derivative aperture? **3 observations under the frozen coverage-first rule.**
10. Future normalization observations? **NO.**
11. Future V1/V2 observations? **NO.**
12. Test 009 P1/P2 changed? **NO.**
13. Price crossings moved? **NO, 0.**
14. V_N different near upper turns versus baseline? **Modestly lower relative Volume/frequency; not stronger concentration.**
15. V_N different near lower turns? **Same mixed pattern: modestly lower than baseline.**
16. V1 additional upper information? **Weak/mixed; small group differences, high noise.**
17. V1 additional lower information? **Weak/mixed.**
18. V2 upper precursor information? **Weak/mixed.**
19. V2 lower precursor information? **Weak/mixed.**
20. Upper immediate versus non-crossing separation? **Mixed; return paths had higher Volume, immediate/delayed were close.**
21. Lower separation? **Mixed; return paths had higher Volume, immediate/delayed were close.**
22. Elevated/extreme Volume more concentrated around turns? **No, precursor-row frequencies were lower than baseline.**
23. Information beyond P1/P2? **Yes representationally; transition discrimination remains weak/mixed.**
24. Profitable versus losing Volume trajectories materially different? **No clear material separation.**
25. V_N/V1/V2 suitability? **V_N conditional; V1/V2 weak/sensitivity-only.**
26. Internal candidates? **Q_S/Q_R/C conditional; H/Q_G weak.**
27. Repeatable upper multivariate shape? **Price shape yes; Volume augmentation mixed/high-dispersion.**
28. Repeatable lower multivariate shape? **Same.**
29. More informative than price alone? **Mixed: nonredundant state information, no improved turning dispersion.**
30. Exact recommended state? **[P, P1, P2, V_N].**
31. F(X,t) fitted? **NO.**
32. Runge-Kutta used? **NO.**
33. Runtime Core modified? **NO.**
34. Emitter modified/retuned? **NO.**
35. Sufficient for Test 010? **CONDITIONAL: enough to test a minimal causal state, but Volume derivatives require stability sensitivity and chronological validation before inclusion.**

## Discipline

No conclusion of “high Volume = BUY/SELL” or “P2 sign = BUY/SELL” is authorized. No classifier, curve family, PCA, trading rule, local dynamics F, or Runge-Kutta method was created.

Next action: **STOP FOR HUMAN REVIEW. Do not begin Test 010. Do not implement Runge-Kutta.**
# APTF Test 009V Causal Volume Normalization Method V0.1

## Source preservation

`V_RAW` is the source `volume` on the same immutable row/timestamp as Test 009 price. Missing is not zero. Exact zero is retained. No extreme value is clipped, winsorized, removed, or replaced without source-invalid authority.

## Predeclared candidates

For each baseline aperture $w\in\{15,30,60\}$, require a complete trailing window ending at current observation t and a strictly positive baseline:

1. `ROLLING_MEDIAN_RATIO_w`:
$$V_N(t)=V_{RAW}(t)/\operatorname{median}(V_{RAW,t-w+1:t}).$$

2. `ROLLING_MEAN_RATIO_w`:
$$V_N(t)=V_{RAW}(t)/\operatorname{mean}(V_{RAW,t-w+1:t}).$$

3. `LOG_ROLLING_MEDIAN_RELATIVE_w`, valid only when current Volume is positive:
$$V_N(t)=\log(V_{RAW}(t)/\operatorname{median}(V_{RAW,t-w+1:t})).$$

All use current/past observations only. No full-dataset baseline, centered window, future value, interpolation, or outcome label participates.

## Time-of-day study

Raw Volume is summarized by authoritative `session_type` and `minute_of_session`. Because PREMARKET/AFTERHOURS coordinates are coarse, causal time-of-day relative Volume is not a primary candidate in V0.1. The comparison reports regular-session between-minute median dispersion and all-session group coverage only.

## Predictor-only selection

For every candidate, calculate actionable valid coverage, numerical failures, finite distribution/IQR, raw-to-normalized Spearman rank preservation, fixed 15-row causal quadratic V1 reversal-run rate, V2 sign-change rate, median V1 persistence, and regular-session minute residual dispersion.

Rank lexicographically by:

1. maximum actionable valid count;
2. minimum numerical failures;
3. minimum single-observation V1 reversal-run percentage;
4. minimum V2 sign-change rate;
5. maximum median V1 persistence;
6. minimum regular-session minute residual dispersion;
7. maximum raw-volume rank preservation;
8. candidate name as deterministic final tie-break.

No crossing, Emitter, episode, or P&L file is opened before selection is persisted.

## Volume regimes

After V_N is frozen, calculate actionable valid Q25/Q75/Q95:

- LOW: V_N <= Q25.
- NORMAL: Q25 < V_N <= Q75.
- ELEVATED: Q75 < V_N <= Q95.
- EXTREME: V_N > Q95.
- UNAVAILABLE: no valid causal V_N.

Exact zero remains in its quantile-derived regime and is separately counted. For ratio-based primary V_N, counts at V_N>=2, >=5, and >=10 are also reported. For log-relative primary V_N, equivalent relative ratios use exp(V_N).

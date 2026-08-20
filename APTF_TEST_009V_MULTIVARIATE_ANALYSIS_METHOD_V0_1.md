# APTF Test 009V Multivariate Analysis Method V0.1

## Frozen channels

P, P1, P2, price states, crossing IDs/locations, normalized price, decisions, Position States, and episode boundaries are copied from Test 009 unchanged. V_N is `ROLLING_MEDIAN_RATIO_15`; V1/V2 are the selected causal 3-row quadratic derivatives. Volume cannot move a price crossing.

## Prior intervals

`prior_k` means the k source observations immediately before the crossing or signal, excluding the current crossing/signal row. Declared k values are 1, 3, 5, 8, and 15. At-crossing values are reported separately.

## Volume proximity

Regimes use frozen V_N Q25/Q75/Q95. For each crossing, elevated/extreme-at-crossing and occurrence in prior 1/3/5/15 are separate fields. Nearest preceding elevated/extreme searches strictly before the crossing and preserves actual elapsed seconds.

## Non-turning baseline

The baseline is actionable rows with valid V_N/V1/V2 outside +/-3 observations of every frozen upper/lower crossing. Radius selection used only frozen crossing density: baseline counts were 64,684 at +/-1, 28,769 at +/-3, 11,576 at +/-5, and 142 at +/-15. +/-3 was fixed before Volume alignment as the widest candidate retaining a substantial baseline.

Upper/lower precursor-region distributions use unique rows from crossing-15 through crossing, inclusive, for the corresponding frozen crossing type. Overlap is preserved between upper/lower sets if frozen crossing geometry warrants it.

## Trajectory-separation labels

For every causal price precursor row:

- upper precursor: P1>0 and P2<0;
- lower precursor: P1<0 and P2>0.

The next relevant frozen crossing supplies a retrospective label:

- IMMEDIATE: 1 observation to crossing;
- DELAYED: 2 through 6 observations;
- RETURN_TO_STRENGTHENING: no relevant crossing within 6 and corresponding strengthening price state appears within 6;
- OTHER_NO_NEAR_CROSSING: neither.

V_N/V1/V2 at the precursor row are current/past-only. Future crossing/time labels are retrospective outputs only.

## Relationships

Calculate pairwise Pearson and Spearman correlations for P, P1, P2, V_N, V1, V2 using pairwise valid actionable observations. Also regress each of V_N/V1/V2 descriptively on `[1,P1,P2]` and report in-sample linear R². Low correlation or R² is not treated alone as independence; baseline/turning distributions, separation groups, and regime-stratified trajectory dispersion are considered jointly.

## Trajectory dispersion

For each crossing type and relative coordinate, preserve Test 009 normalized-price IQR. Compare it with the count-weighted within-volume-regime normalized-price IQR. Report the median across relative coordinates. Lower stratified dispersion is descriptive evidence that Volume partitions price trajectories; it is not a predictive model.

## Prohibitions

No classifier, optimization, P&L-driven selection, trading rule, curve family, PCA, F(X,t), ODE model, or Runge-Kutta method is permitted.
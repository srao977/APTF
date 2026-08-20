# APTF Test 009V Plan V0.1

## Purpose

Extend frozen Test 009 price evidence with a separate causal normalized-volume channel and determine whether Volume adds descriptive trajectory information. This is state discovery, not a trading-rule, classifier, P&L, Runtime, Emitter, local-dynamics, or Runge-Kutta experiment.

## Frozen inputs

- Runtime Core V0.1: 22 files.
- Test 009: all 18 current authority/evidence files pre-hashed before analysis.
- Test 009 price field, P1/P2, 15-row price aperture, near-zero criterion, derivative state, 6,606 upper and 6,606 lower crossing IDs/locations, turning geometry, and episode alignment.
- Test 007 episodes and Test 008 P&L, opened only after Volume mathematics is frozen.

## Ordered procedure

1. Audit raw source `volume` aligned row-for-row with frozen Test 009 `close`, UTC timestamp, and observation identity.
2. Preserve missing and exact-zero observations; never clip, winsorize, impute, interpolate, or forward-fill.
3. Evaluate only the nine predeclared rolling candidates and windows in the normalization method document. Evaluate time-of-day structure descriptively, not as a candidate because extended-session minute semantics are coarse.
4. Select and persist one primary V_N using predictor-only mathematical criteria before opening crossings, decisions, episodes, or P&L.
5. Evaluate causal quadratic V1/V2 windows 3/5/8/15 and freeze one by the predeclared stability rule.
6. Construct X_OBS=[P,P1,P2,V_N,V1,V2] per observation while copying every frozen price/state/internal label exactly.
7. Only after Volume mathematics is frozen, open frozen crossing IDs and produce crossing features, -15...+15 trajectories, precursor/time-to-crossing labels, non-turning baseline comparisons, joint frequencies, and episode/P&L descriptive joins.
8. Recommend an interpretable causal state vector for Test 010 without fitting F(X,t), a classifier, a curve family, PCA, or Runge-Kutta.
9. Recompute all frozen hashes and stop for human review.

## Retrospective labels

For precursor observations, labels use the next relevant frozen crossing:

- IMMEDIATE: crossing in 1 observation.
- DELAYED: crossing in 2 through 6 observations.
- RETURN_TO_STRENGTHENING: no relevant crossing in 1 through 6 and the corresponding strengthening price state appears in that horizon.
- OTHER_NO_NEAR_CROSSING: neither condition.

These labels never enter V_N/V1/V2 calculation.

The non-turning baseline is actionable valid rows outside +/-3 observations of every frozen crossing. This radius was fixed from frozen crossing-density feasibility before Volume alignment: +/-15 left only 142 baseline rows, while +/-3 preserves 28,769. It is retrospective descriptive evidence and never a causal input.

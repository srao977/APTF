# APTF Test 009V Test 010 State-Vector Recommendation V0.1

Status: **CONDITIONAL RECOMMENDATION ONLY**

| Variable | Recommendation | Evidence | Concern / requirement |
|---|---|---|---|
| P | STRONG CANDIDATE | Authoritative observed price and repeatable frozen turning geometry | Preserve source-close and actual-time authority |
| P1 | STRONG CANDIDATE | Causal direction state and exact frozen crossing authority | Keep Test 009 15-row estimator unchanged |
| P2 | STRONG CANDIDATE | Measurable precursor information in Test 009 | Mixed coverage; do not convert sign directly to trading action |
| V_N | CONDITIONAL CANDIDATE | Causal, interpretable participation ratio; P1/P2 linear R² only 0.000280; broad independent variation | Weak turn concentration and no price-IQR reduction; retain 15-row rolling-median authority |
| V1 | WEAK CANDIDATE | Ordered causal Volume evolution and small group differences | Selected 3-row estimator has 66.50% single-row reversal runs and median persistence 1 |
| V2 | WEAK CANDIDATE | Causal Volume curvature available observation-by-observation | Same short-window noise; no strong turn separation |
| H | WEAK CANDIDATE | Preserved frozen field | Constant 1.0 across the reserve; no state information |
| Q_G | WEAK CANDIDATE | Preserved frozen geometry field | Little variation and near-zero Volume relationship |
| Q_S | CONDITIONAL CANDIDATE | Test 009 showed systematic price-state variation | Derived/internal and weak Volume relationship; possible redundancy |
| Q_R | CONDITIONAL CANDIDATE | Test 009 price-state variation and modest rank relation to Volume | Derived/internal; evaluate redundancy chronologically |
| C | CONDITIONAL CANDIDATE | Frozen emitted mathematical property with price-state variation | Composite derived value; avoid circular state specification |

## Recommended Test 010 state

Primary minimal candidate:

```text
X_010(t) = [P, P1, P2, V_N]
```

Sensitivity-only expanded diagnostic candidate:

```text
X_010_EXPANDED(t) = [P, P1, P2, V_N, V1, V2]
```

V1 and V2 should not enter the primary state until Test 010 demonstrates chronological out-of-sample stability or authorizes a more stable causal Volume derivative aperture. Q_S, Q_R, and C may be evaluated as conditional covariates, not silently included as independent physical dimensions. H and Q_G should not enter the initial state vector on this evidence.

## Why conditional

Volume is nonredundant with P1/P2 in linear/rank representation, but it does not concentrate around frozen turns, does not reduce price-trajectory dispersion under regime stratification, and its selected maximum-coverage derivatives are noisy. Test 010 may proceed only as a local-dynamics identification experiment with chronological validation, explicit regularization/conditioning, and no trading-rule feedback.

Local dynamics F(X,t) created: **NO**  
Runge-Kutta used: **NO**
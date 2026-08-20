# APTF Test 010 -> Test 011 RK Interface V0.1

Status: **CONDITIONAL PRICE-ENGINE RK READINESS; VOLUME OBSERVER ONLY**

## Price Engine

State:

$$X_P=[P,P1,P2].$$

Units:

- P: SPY source-close price units.
- P1: price units/minute.
- P2: price units/minute².
- J_P/F_P: price units/minute³.
- independent variable: elapsed UTC minutes.

Dynamics:

$$F_P(X_P,t)=[P1,P2,J_P(X_P,t)].$$

`J_P` is evaluated from the locally fitted `PRICE_AFFINE_TIME_W15` model. Every Price emission supplies:

- model identifier and lookback;
- standardized-feature coefficient vector;
- state means/scales;
- centered local-time mean/scale and endpoint origin;
- condition number and error estimate.

At an intermediate RK stage with trial state `[P*,P1*,P2*]` and local time offset `tau*`, Test 011 may standardize the trial state using the frozen emission scaling and evaluate the affine coefficient vector. It must not refit inside a solver step.

Model fitting: causal trailing 15 completed J_P observations, SVD least squares, no regularization, exact-rank requirement, condition limit `1e8`.

Valid local horizon: **at most 1 elapsed minute and only inside `INTRASESSION_CONTINUOUS`** before mandatory comparison/re-estimation. This is not a multi-minute authorization.

Stability evidence:

- 101,191 one-step forecasts; unstable/singular fits 0.
- P2 MAE 0.002125690083990186; RMSE 0.011399229350711077.
- P2 evolution sign accuracy 0.6953978120583847.
- Curvature-state sign accuracy 0.8798608571908569.
- Median/p95 condition 18.8344/39.4396.

## Session and gap rule

Do not integrate through `SESSION_TRANSITION`, `OVERNIGHT_GAP`, `WEEKEND_OR_HOLIDAY_GAP`, or an unobserved source gap. Preserve the last state as evidence, wait for the next real observation, admit the observed state, and re-estimate local dynamics before any new projection.

Overnight and weekend one-step extrapolation produced catastrophic level errors, confirming the prohibition. Session close resets no state and forces no color.

## Volume Engine

Primary state/update interface:

```text
X_V = {
  V_N,
  IntervalState_15,
  Observer(V1,V2,sign,persistence)
}
```

Units:

- V_RAW: provider-reported Volume units.
- V_N: dimensionless 15-row rolling-median ratio.
- interval statistics: raw Volume or dimensionless V_N as named.
- V1: V_N/minute; V2: V_N/minute².

Evolution:

```text
G_V: discrete observation-to-observation update
primary one-step estimate: V_N_hat(n+1) = V_N(n)
interval condition descriptor: trailing 15-observation Volume state
V1/V2: observer events, not integrated primary coordinates
```

Volume ODE/RK readiness: **NO for V0.1**. Point persistence provides maximum causal coverage; interval-15 median has lower MAE but 13 fewer forecasts; pointwise derivative Taylor is numerically unusable. Test 011 may consume Volume as an independently updated observer/control input at real observations, not propagate it via RK.

## Control contract

Control receives separate `PriceEngineEmission` and `VolumeEngineEmission` references. No scalar Price/Volume mixture is permitted. Control may report both persistent, both transitioning, Price-only transition, Volume-only transition, or inconclusive. It emits no BUY/HOLD/SELL.

## Test 011 candidates

- Required candidate: RK45.
- Required candidate: DOP853.
- Optional deterministic reference if separately authorized: RK4.

No solver was executed in Test 010. Test 011 must compare one-minute Price projections only, use solver tolerances/step limits declared before outcomes, preserve local F_P parameters during each propagation, and re-estimate after every real observation.

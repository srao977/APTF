# APTF Test 011 RK45 Numerical and Causal Method V0.1

## Solver and units

Use `scipy.integrate.solve_ivp(method="RK45")`. Solver time is elapsed **minutes**, matching frozen Test 010 F_P units.

$$X_P=[P,P1,P2],\qquad \dot X_P=[P1,P2,J_P].$$

For each emission, with frozen coefficient vector beta and scaling metadata:

$$J_P(X,\tau)=\beta_0+\beta_P z(P)+\beta_{P1}z(P1)+\beta_{P2}z(P2)+\beta_\tau z(\tau).$$

Feature order is frozen as `[intercept,P,P1,P2,t_local]` by Test 010 method/code. `tau=0` is the real observation endpoint. Parameters/scaling remain unchanged throughout one solve and expire after that projection.

## Tolerance study

Predeclared tolerance IDs:

- TOL_A: rtol 1e-6.
- TOL_B: rtol 1e-8.
- TOL_C: rtol 1e-10 (tightest reference).

For each emission and tolerance r, derive vector atol without outcomes:

$$atol=[r\sigma_P,\min(r\sigma_{P1},0.1\epsilon),r\sigma_{P2}],$$

where state scales come from the frozen local emission and frozen Test 009 epsilon is `0.0035332071428566536` price/minute. Every component tolerance is recorded per projection.

The sensitivity sample is 1,024 deterministic evenly spaced eligible emissions from the full chronological eligible index set, including both endpoints. For A versus B and B versus C, calculate terminal absolute and local-scale-normalized state differences, derivative-state disagreement, and projected-crossing disagreement.

Select the loosest tolerance whose comparison to the next tighter tolerance has:

- maximum component normalized difference <= 0.1;
- derivative-state disagreement = 0;
- crossing disagreement = 0;
- solver failures = 0.

P&L and trading labels are unavailable to selection.

## Events

Two nonterminal causal events evaluate P1 within `[0,1]`:

- upper event: P1=0, direction -1;
- lower event: P1=0, direction +1.

Event detection never extends the integration span. Actual Test 009 crossing labels are revealed only after the projection is persisted.

## Derivative state

Use frozen Test 009 epsilon and exact state labels:

- `RISING_STRENGTHENING`, `RISING_WEAKENING`, `UPPER_TURNING_REGION`;
- `FALLING_STRENGTHENING`, `FALLING_WEAKENING`, `LOWER_TURNING_REGION`;
- `D2_ZERO`, `UNAVAILABLE`.

Crossing detection uses P1 sign/event zero, not the epsilon band.

## Numerical failure

Preserve solver failure, nonfinite state, malformed F_P, or numerical explosion. Do not clip or fabricate. A safety envelope is scale-relative: terminal component deviation from initial state above `1e6` local state scales is `NUMERICALLY_UNSTABLE`.

## Perturbation sensitivity

Use 256 evenly spaced eligible emissions. Perturb one component at a time by:

$$\delta=10^{-6}[\sigma_P,\min(\sigma_{P1},0.25\epsilon/10^{-6}),\sigma_{P2}].$$

Freeze the same F_P and primary tolerance, integrate each perturbed state one minute, and report Euclidean initial/final difference and amplification. No outcome selects perturbations.

## Adaptive-loop causality

The projection phase reads only O_n and its frozen Test 010 emission and writes a projection core. Scoring then reads O_(n+1), appends actual/error fields, and records reveal-after-persist. The prior F_P is never reused for a second minute.
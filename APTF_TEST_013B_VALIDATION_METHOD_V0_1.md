# APTF Test 013B Frozen Validation Method V0.1

## Source and state

Use QQQ source `close` as $P$. Interpret naive FirstRate timestamps as `America/New_York` local market time and derive UTC only for elapsed-time arithmetic. Construct $P1$ and $P2$ with the exact frozen Test009 15-row causal quadratic OLS evaluated at the current endpoint. The first 14 rows and any rank-invalid states are initialization, never scored.

## Time and targets

Classify local sessions as PREMARKET `[04:00,09:30)`, REGULAR `[09:30,16:00)`, and AFTERHOURS `[16:00,20:00)`. A training target or projection is eligible only when adjacent timestamps are exactly one minute apart, have the same local date, and have the same session type.

For an eligible pair ending at observation $k+1$, use $J_{P,k}=(P2_{k+1}-P2_k)/1$. At projection origin $n$, every training target must satisfy $k+1\le n$.

## Models

F0_W15 is the Test010/Test011 centered/scaled affine-time local least-squares method, fitted from QQQ causal history with 15 valid contiguous $J_P$ targets. F4 is the exact Test012 centered/scaled affine ridge implementation: design `[1,zP,zP1,zP2]`, population means/scales from QQQ causal history, unpenalized intercept, ridge matrix `diag(0,1,1,1)`, and lambda 1. Primary F4 window is 30; W15/W60 are sensitivity only.

No SPY coefficient, center, scale, or fitted state is transferred.

## Propagation

Use `scipy.integrate.solve_ivp(method="RK45")`, `rtol=1e-6`, and Test011 vector `atol=[rtol*sigma_P,min(rtol*sigma_P1,0.1*epsilon),rtol*sigma_P2]`. Propagate exactly one contiguous minute from the real current QQQ state. Persist the projection core before reading the next real state; never substitute a projected state for observation truth.

## Covers and diagnostics

Primary cover is the exact F0_W15/F4_L1_W30 intersection. Sensitivity cover is the exact F4 W15/W30/W60 intersection. The primary test remains executable if sensitivity is blocked, but W30 remains primary.

Report all endpoint, Q90/Q95/Q99/Q99.5/Q99.9/max, sign/state, transition confusion, perturbation, local-domain, Jacobian, coefficient, condition, and SPY-relative metrics predeclared by Test013B. Raw cross-instrument comparisons are scale-dependent; no new normalization is introduced.

Classification uses the complete scorecard: externally validated only for broad material relative stabilization; conditional when substantial stabilization coexists with material concerns; failed when the SPY pattern does not reproduce; blocked only for structural invalidity.

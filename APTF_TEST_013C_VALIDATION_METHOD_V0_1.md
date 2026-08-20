# APTF Test 013C Frozen Validation Method V0.1

Use DIA source `close` as $P$. Interpret naive FirstRate timestamps as `America/New_York` local time. Construct $P1/P2$ with the frozen Test009 15-row causal quadratic OLS endpoint method; exclude the first 14 initialization rows from scoring.

Session and contiguous-time rules, corrected $J_P$, F0_W15, F4 centered/scaled ridge lambda 1, W30 primary, W15/W60 sensitivity, RK45 `rtol=1e-6`, component-scaled `atol`, one-minute horizon, zero epsilon, derivative states, transitions, local domains, Jacobians, perturbations, and coefficient diagnostics are identical to Test013B. DIA estimates all local fit state from DIA history.

Before Price profiling, predeclare descriptive activity on contiguous adjacent pairs: exact unchanged count/rate; nonzero count/rate; absolute movement Q25/Q50/Q75/Q90/Q95/Q99/max; relative movement Q50/Q90/Q95/Q99; absolute P1/P2 Q50/Q90/Q95/Q99/max; decimal precision; smallest and most common nonzero increments. Produce comparable SPY/QQQ characteristics where frozen source evidence permits.

Movement bands are quantiles of DIA absolute contiguous one-minute movement on the primary cover, with fixed labels Q0-Q25, Q25-Q50, Q50-Q75, Q75-Q90, Q90-Q99, Q99-Q100. Boundaries are descriptive and cannot select or alter a model. Zero/nonzero movement and frozen near-zero/non-near-zero state strata are also descriptive only.

Primary cover is F0_W15 intersect F4_L1_W30. Sensitivity cover is F4 W15/W30/W60. Classification uses the complete replication signature and quiet-regime evidence. No smoothing, interpolation, synthetic movement, clipping, outlier deletion, Volume, P&L, trading, or retuning is permitted.

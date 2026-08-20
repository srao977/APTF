# APTF Test 010 Volume Interval and State-Update Method V0.1

## Frozen channel

V_RAW, V_N=`ROLLING_MEDIAN_RATIO_15`, V1, and V2 are copied from Test 009V. Volume is observed participation/result; Volume-causes-Price is not asserted.

## Causal interval descriptors

For trailing intervals k=3,5,8,15 including current observation, calculate raw Volume mean/median/min/max/range/population standard deviation/CV/max-median ratio; mean V_N relative to baseline 1; counts/fractions V_N>=2/5/10; current/max V_N; observations since max; ELEVATED/EXTREME counts; consecutive persistence above V_N>=1; V1/V2 signs and contiguous sign persistence.

## Volume representation candidates

All predict next V_N one step and use no Price or trading labels:

- `VOLUME_POINT`: persistence, V_N_hat(n+1)=V_N(n).
- `VOLUME_DERIVATIVE`: one-step Taylor observer using frozen V1/V2 and revealed next h for scoring.
- `VOLUME_INTERVAL`: for each k, predict by current trailing median V_N_k.
- `VOLUME_INTERVAL_DERIVATIVE_UPDATE`: for each k, causal local 60-transition standardized SVD fit mapping `[V_N, mean_k, median_k, std_k, max/median_k, V1, V2]` to next V_N. At O_n training uses feature/target pairs only through target O_n; prediction targets O_(n+1).

Rank deficiency/nonfinite fit or condition number >1e8 is invalid. No P&L/BUY/SELL/crossing information enters selection.

## Selection and metrics

Report valid forecasts, failures, condition, coefficient stability where fitted, V_N MAE/RMSE/median absolute error/bias, regime-transition accuracy, burst persistence accuracy (whether V_N>=2 persists), noise sensitivity, and ODE/state-update suitability.

Select lexicographically: maximum valid forecasts, minimum failures, minimum V_N MAE, minimum RMSE, simplest representation, then shorter interval. Because V_N/V1/V2 are discontinuous/noisy ratios, a discrete G_V state update is the default architectural form unless ODE continuity evidence is strong.
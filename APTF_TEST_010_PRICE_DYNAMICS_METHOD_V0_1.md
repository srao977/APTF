# APTF Test 010 Price Dynamics Method V0.1

## Frozen state and structural dynamics

$$X_P=[P,P1,P2],\qquad \dot P=P1,\qquad \dot P1=P2.$$

Only curvature evolution is identified:

$$J_{P,n}=\dot P2_n=\frac{P2_n-P2_{n-1}}{(t_n-t_{n-1})/60}.$$

J_P uses frozen current/prior P2 and actual elapsed minutes only.

## Candidate families

For local training samples, non-intercept state features are standardized from that trailing training window only. Constant/rank-deficient features invalidate the fit. SVD least squares is used; normal equations and implicit regularization are prohibited.

- `PRICE_LINEAR`: `[1,z(P),z(P1),z(P2)]`.
- `PRICE_AFFINE_TIME`: linear features plus standardized `t_local`, where `t_local` is actual elapsed minutes relative to current fit endpoint.
- `PRICE_QUADRATIC_DIAGONAL`: linear features plus `z(P)^2,z(P1)^2,z(P2)^2`; no cross terms or higher order.

Windows: 15, 30, 60 completed J_P samples. Test 009's P1/P2 aperture remains 15 and is never changed.

## Conditioning

- Exact rank deficiency: fit failure.
- Standardized-design condition number > 1e8: unstable/invalid.
- Nonfinite coefficients/predictions: invalid.
- Coefficient stability: median absolute step change in coefficients after mapping each fit to standardized feature coordinates; reported per candidate.

No ridge is silently introduced. Complexity order is LINEAR < AFFINE_TIME < QUADRATIC_DIAGONAL.

## Walk-forward prediction

At O_n, fit only through J_P,n and emit frozen J_hat_P,n. After O_(n+1) arrives, reveal actual elapsed minutes $h$ and score:

$$\hat P2_{n+1}=P2_n+\hat J_{P,n}h,$$
$$\hat P1_{n+1}=P1_n+P2_nh+\tfrac12\hat J_{P,n}h^2,$$
$$\hat P_{n+1}=P_n+P1_nh+\tfrac12P2_nh^2+\tfrac16\hat J_{P,n}h^3.$$

This is a one-step constant-jerk approximation, **not Runge-Kutta**. The next timestamp is used only by the evaluator after model emission; no next price/state enters fitting.

## Selection

Select lexicographically without labels/P&L: maximum valid forecasts, minimum unstable/failed fits, minimum P2 MAE, minimum P2 RMSE, highest P2-evolution sign accuracy, simplest family, then shortest lookback. Report all metrics and do not revise the rule afterward.

Session-boundary and gap forecasts are scored separately and cannot establish ordinary-intraday RK readiness.

# APTF Test 010 Dual-Engine Local Dynamics and Adaptive Control Foundation V0.1

Status: **PASS**  
Acceptance: **120/120 PASS**  
Test 011 readiness: **CONDITIONAL, PRICE-ONLY RK PROPAGATION**

PASS means causal identification, one-step validation, dual-engine separation, session discipline, complete interfaces, and immutability succeeded. It does not authorize a trading rule, cockpit threshold, AutoPilot, broker, or RK execution.

## Immutable authority

- Runtime Core: 22/22 unchanged.
- Test 009: 18/18 unchanged.
- Test 009V: 25/25 unchanged.
- Test 007/008: 35/35 unchanged.
- Frozen Emitter/Position State: unchanged.
- Runtime modifications, reserve Emitter reruns, trading retuning: 0.

## Price Engine

State and dynamics:

$$X_P=[P,P1,P2],\qquad F_P=[P1,P2,J_P].$$

$$J_{P,n}=(P2_n-P2_{n-1})/\Delta t_n.$$

Nine candidates were tested: linear, affine-time, and diagonal-quadratic local laws over 15/30/60 J_P observations. Primary: **PRICE_AFFINE_TIME_W15**.

- Walk-forward forecasts: 101,191.
- Failed warm-up fits: 14; unstable/singular: 0/0.
- Median/p95 condition: 18.834356561997836 / 39.439602904393325.
- P2 MAE/RMSE/median AE/bias: 0.002125690083990186 / 0.011399229350711077 / 0.0011925149699517357 / -0.000011765290454094744.
- P2 evolution sign accuracy: 69.53978120583847%.
- Curvature-state sign accuracy: 87.9860857190857%.
- Intraday P/P1/P2 MAE: 0.0876149925 / 0.0164726435 / 0.0019521965.
- Overnight P2 MAE: 0.1624028876; weekend/holiday: 0.2696448351.
- Overnight/weekend level extrapolation was catastrophic, so cross-session integration is prohibited.

Price RK readiness: **CONDITIONAL** for one elapsed minute of `INTRASESSION_CONTINUOUS` only, followed by a real observation and full re-estimation.

## Volume Engine

Volume remains an observed participation/result channel; Volume-causes-Price is not asserted.

All intervals 3/5/8/15 include mean, median, min/max/range/std/CV, burst ratios/counts/fractions, persistence, and V1/V2 observer state. Total interval rows: 404,801. V1/V2 sign-change events: 141,920.

Ten one-step representations were compared independently of Price/trading labels. The frozen coverage-first rule selected:

```text
G_V: V_N_hat(n+1) = V_N(n)
```

- Valid forecasts: 101,205.
- V_N MAE/RMSE/median AE/bias: 2.2071033753 / 27.4794671247 / 0.4988814318 / -0.0000331101.
- Regime accuracy: 48.95015068425473%.
- Burst-persistence accuracy: 77.78864680598785%.

The 15-row interval median had lower MAE, 1.7441472516, but 13 fewer forecasts. It is retained as the primary condition descriptor. Pointwise derivative Taylor was unusable (MAE 5,011.60, RMSE 730,735.12).

Volume evolution is therefore a **discrete G_V observer update**, not an ODE. Volume RK readiness: **NO**.

## Dual-engine Control

Control rows: 101,206. Price and Volume emission IDs remain separate; no scalar mix exists.

- BOTH_PERSISTENT: 19,177.
- BOTH_TRANSITIONING: 11,081.
- PRICE_TRANSITION_VOLUME_STABLE: 3,311.
- VOLUME_TRANSITION_PRICE_PERSISTENT: 67,622.
- INCONCLUSIVE: 15.
- New trading actions: 0.

Volume observer-event offsets to nearest frozen Price crossing:

- Before: 57,315 (40.3854%).
- At: 18,490 (13.0285%).
- After: 66,115 (46.5861%).

The at-crossing event share, 13.0285%, is essentially the 13.0546% crossing-row baseline. Temporal lead/lag does not justify a causal claim.

## Session control

127 observed local-date sessions and 126 inter-session gaps were preserved. Gaps range 28,860 to 288,840 seconds. Session close resets neither engine, changes no color, and creates no zero state. Test 011 must retain final evidence, wait for the next real observation, admit it, and re-estimate rather than integrate blindly through the gap.

Execution window is frozen `is_regular_session=true`, local `[09:30,16:00)`. Mathematical state spans premarket, regular, and after-hours observations continuously.

## Cockpit readiness

Color readiness is **CONDITIONAL**. No thresholds were created.

- Price continuous candidates: |P1|, |P2|, |J_P|, persistence, P2 error estimate, condition, gap status.
- Volume candidates: V_N, interval-15 dispersion/burst/persistence, V1/V2 event persistence.

Colors never mean BUY/HOLD/SELL. Execution Window and AutoPilot OFF/ARMED/ON remain unimplemented downstream architecture.

## Direct answers

1. Runtime Core modified? **NO.**
2. Test 009 Price derivatives modified? **NO.**
3. Test 009V Volume values modified? **NO.**
4. Independent engines preserved? **Yes.**
5. Collapsed scalar indicator? **NO.**
6. Price state X_P? **[P,P1,P2].**
7. Price F_P? **[P1,P2,PRICE_AFFINE_TIME_W15(P,P1,P2,t_local)].**
8. Most stable/selected Price family? **Affine state evolution with centered local time.**
9. Price identification window? **15 observations.**
10. One-step Price accuracy? **P2 MAE 0.00212569, RMSE 0.01139923, evolution sign 69.54%, curvature sign 87.99%; contiguous P MAE 0.0876.**
11. Is dP2/dt stable enough? **Conditionally, for one-minute contiguous propagation only.**
12. Volume state X_V? **{V_N, IntervalState_15, Observer(V1,V2,sign,persistence)}.**
13. Most informative/stable Volume interval? **15 observations by lowest interval MAE and best smoothing.**
14. Interval state outperform pointwise derivatives? **Yes decisively; derivative Taylor was unstable/noisy.**
15. V1/V2 sign changes useful? **Yes as frequent observer events, not primary dynamics.**
16. Volume before some Price transitions? **Yes temporally, 57,315 events.**
17. At some transitions? **Yes, 18,490.**
18. After some transitions? **Yes, 66,115.**
19. Causal lead/lag claim justified? **NO; event frequency is high and at-crossing concentration matches baseline.**
20. Volume ODE or update? **Discrete G_V state update.**
21. Price suitable for RK? **CONDITIONAL, one-minute contiguous only.**
22. Volume suitable for RK? **NO.**
23. Can Volume remain observer while Price uses RK? **Yes; this is the recommended dual-engine design.**
24. Future Price color quantities? **|P1|, |P2|, |J_P|, persistence, model error, condition, gap state.**
25. Future Volume color quantities? **V_N, interval-15 dispersion/burst/persistence, V1/V2 event persistence.**
26. Color thresholds created? **NO.**
27. BUY/HOLD/SELL changed? **NO.**
28. AutoPilot implemented? **NO.**
29. Broker implemented? **NO.**
30. Session close resets engines? **NO.**
31. Session gaps in Test 011? **Do not integrate; preserve state, wait for real observation, then re-estimate.**
32. Exact Price interface? **Emission-carried X_P, standardized affine coefficients/scaling, F_P=[P1,P2,J_P], one-minute domain, condition/error metadata.**
33. Exact Volume interface? **Discrete G_V point update plus interval-15 state and V1/V2 observer events; no RK integration.**
34. Evaluate RK45? **Yes, in Test 011 only.**
35. Evaluate DOP853? **Yes, in Test 011 only.**
36. Any RK solver executed? **NO.**
37. Sufficient for Test 011? **CONDITIONAL: Price interface is evaluable/stable for one contiguous minute; Volume remains discrete; gaps and longer horizons are prohibited.**

## Final discipline

No classifier, trading rule, P&L selection, scalar Price/Volume indicator, SHORT, color boundary, AutoPilot, broker, RK solver, or multi-step trajectory was created.

Next action: **STOP FOR HUMAN REVIEW. Do not begin Test 011 or implement Runge-Kutta.**
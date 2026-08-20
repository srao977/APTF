# APTF Test 011 RK45 Adaptive Price Trajectory Control with Independent Discrete Volume Observer V0.1

Status: **PASS**  
Acceptance: **140/140 PASS**  
Empirical Price-RK result: **NOT VALID ENOUGH FOR CURRENT CONTROL PROPAGATION**

PASS means the authorized RK45 experiment was causal, complete, failure-preserving, reconciled, additive, and immutable. It does not mean RK45 improved the frozen model.

## Numerical configuration

- SciPy: `1.18.0`; solver: `solve_ivp(method="RK45")`; time: minutes.
- Tolerance study: rtol `1e-6`, `1e-8`, `1e-10`; deterministic 1,024-case sample.
- Component atol: `[rtol*sigma_P, min(rtol*sigma_P1,0.1*epsilon), rtol*sigma_P2]`.
- Primary: **TOL_A / rtol 1e-6**, the loosest converged tolerance.
- TOL_A vs TOL_B maximum scale-normalized difference: `0.0534363`; state/crossing disagreements: 0/0.
- Median atols P/P1/P2: `1.1340e-7 / 3.3117e-8 / 4.3586e-9` (emission-specific vectors retained).
- P&L/trading labels used: no.

## Eligibility and causality

- Actionable observations: 101,206.
- Eligible: 90,974.
- Policy-ineligible: 10,232: TIME_GAP 9,837; SESSION_BOUNDARY 380; NO_PRICE_MODEL 14; NO_NEXT_OBSERVATION 1.
- RK success: 90,968; failure: 6, all preserved as `NUMERICALLY_UNSTABLE` with no fabricated projection.
- Adaptive-loop audits: 90,968/90,968 projection-persist/reveal/score ordering PASS.
- Future leakage violations: 0.
- Multi-minute, gap, overnight, weekend RK: 0.

## Price result

| Metric | Result |
|---|---:|
| P MAE / RMSE / median AE / bias | 0.08776846 / 0.14043340 / 0.05920384 / -0.00013257 |
| P1 MAE / RMSE / median AE / bias | 0.01840923 / 0.55182224 / 0.01032980 / -0.00206666 |
| P2 MAE / RMSE / median AE / bias | 0.04838932 / 8.89357804 / 0.00368468 / -0.03341120 |
| Price movement sign accuracy | 46.46579017% |
| P1 sign accuracy | 88.88400317% |
| P2 sign accuracy | 78.44296896% |
| Frozen derivative-state accuracy | 66.44864128% |

Projected upper crossings: 1,410; actual eligible upper crossings: 5,717. TP/FP/TN/FN = 1,029/381/84,870/4,688; precision 0.7298, recall 0.1800.

Projected lower crossings: 1,282; actual eligible lower crossings: 5,715. TP/FP/TN/FN = 967/315/84,938/4,748; precision 0.7543, recall 0.1692.

At actual upper crossings, 3,323 projections retained P1>0/P2<0 precursor structure, but only 1,029 projected the crossing. Lower: 3,374 retained P1<0/P2>0, while 967 projected crossing.

## RK45 versus Test 010

Identical overlap: 90,968 observations.

| Component | Test 010 MAE | RK45 MAE | Test 010 RMSE | RK45 RMSE |
|---|---:|---:|---:|---:|
| P | 0.08761725 | 0.08776846 | 0.13619776 | 0.14043340 |
| P1 | 0.01647177 | 0.01840923 | 0.02475845 | 0.55182224 |
| P2 | 0.00195209 | 0.04838932 | 0.00303603 | 8.89357804 |

Test 010 P2 sign/state accuracy: 70.4544%/88.9434%; RK45: 78.4430%/66.4486%. RK45 improved terminal P2 sign but materially degraded state accuracy and every MAE. Overall result: **WORSE**, not equivalent.

Tolerance convergence proves this is not loose solver error. Perturbation amplification median/p95/max was approximately P 1.009/1.047/4.650, P1 1.428/4.886/137.664, P2 7.384/31.689/907.958. Continuous intermediate-state evaluation of frozen F_P is locally sensitive.

## Volume and Control

- Volume observer rows: 101,206; G_V updates: 101,205; Volume RK: 0.
- V1/V2 observer-event rows: 78,715 (141,920 individual sign events in Test 010 authority).
- Interval-15 warm-up unavailable: 13; final interval available despite no next G_V target.

Control rows: 101,206:

- Price transition / Volume changing: 2,098.
- Price transition / Volume stable: 594.
- Price stable / Volume changing: 68,746.
- Both stable: 19,530.
- Inconclusive: 10,238.
- New BUY/SELL/HOLD, SHORT, AutoPilot, broker: 0.

Price and Volume references remain separate; no scalar mix exists.

## Session discipline

All 380 prohibited session boundaries were audited: 127 premarket→regular, 127 regular→after-hours, and 126 after-hours→next premarket. Same-session missing-row gaps: 9,837. RK attempts across any such boundary/gap: 0. Session close resets neither engine.

## Cockpit and next step

Price color readiness: **NO with current RK/F_P**. Volume descriptive color readiness: **CONDITIONAL**. No thresholds were created.

The next test should stabilize/reparameterize local Price dynamics and assess RK compatibility. Do not proceed directly to colors, longer horizons, or execution mapping.

## Direct answers

1. Runtime modified? **NO.**
2. Test 009 modified? **NO.**
3. Test 009V modified? **NO.**
4. Test 010 modified? **NO.**
5. Price state exactly [P,P1,P2]? **Yes.**
6. Exact Test 010 F_P used? **Yes, per-emission PRICE_AFFINE_TIME_W15.**
7. F_P frozen per solve? **Yes.**
8. Primary solver? **RK45.**
9. Tolerances? **rtol 1e-6 primary; component-scaled vector atol; 1e-8/1e-10 sensitivity.**
10. Selected without outcomes? **Yes.**
11. RK eligible? **90,974.**
12. Ineligible? **10,232.**
13. Any session-gap RK? **NO.**
14. Any future row used during projection? **NO.**
15. Projection persisted before reveal? **Yes, 90,968/90,968 successes.**
16. F_P re-estimated after each new real observation? **Yes where next model authority exists.**
17. F_P used beyond one minute? **NO.**
18. P MAE/RMSE? **0.08776846 / 0.14043340.**
19. P1 MAE/RMSE? **0.01840923 / 0.55182224.**
20. P2 MAE/RMSE? **0.04838932 / 8.89357804.**
21. Price movement sign accuracy? **46.4658%.**
22. P1 sign accuracy? **88.8840%.**
23. P2 sign accuracy? **78.4430%.**
24. Derivative-state accuracy? **66.4486%.**
25. Projected upper crossings? **1,410.**
26. Upper correspondence? **Precision 72.98%, recall 18.00%.**
27. Projected lower crossings? **1,282.**
28. Lower correspondence? **Precision 75.43%, recall 16.92%.**
29. RK45 improve Test 010? **No, worse on all state MAEs.**
30. Numerically confirm local representation? **No as a propagator; tolerance convergence confirms solver consistency but exposes F_P instability away from endpoint.**
31. Multi-minute trajectories? **NO.**
32. Volume RK? **NO.**
33. Volume independent discrete observer? **Yes.**
34. Volume state? **[V_N,IntervalState_15,Observer(V1,V2)].**
35. Volume role? **Observed participation/result, not Price cause.**
36. Engines separate in Control? **Yes.**
37. Scalar mixture? **NO.**
38. Future Price condition quantities? **Projected P1/P2/J_P/deltas, zero distance/crossing, model condition/error, solver work, perturbation amplification, gap state.**
39. Volume quantities? **V_N, interval-15 dispersion/burst/persistence, V1/V2 signs/persistence/events, G_V error.**
40. Color thresholds? **NO.**
41. New trading rules? **NO.**
42. AutoPilot? **NO.**
43. Broker? **NO.**
44. One-minute adaptive RK45 valid enough to remain current control propagator? **NO for this F_P.**
45. Adaptive loop causal across history? **Yes operationally, with 0 leakage; predictive quality is inadequate.**
46. Price ready for cockpit envelopes? **NO until dynamics are stabilized.**
47. Volume ready? **CONDITIONAL for descriptive participation envelopes only.**
48. Next Test? **Local Price dynamics stabilization/RK-compatibility audit, not colors or longer horizons.**

No exact market extrema, Price causation by Volume, or color-to-trading mapping is claimed.

Next action: **STOP FOR HUMAN REVIEW. Do not begin Test 012.**
# APTF Test 014 Result V0.1

Status: **PASS**  
Acceptance: **130/130 PASS**  
Classification: **SPY_P_ENGINE_EMISSION_CONDITIONAL**

## Three layers

1. **Mathematical Price Engine:** frozen experimental F4_L1_W30, state `[P,P1,P2]`, one-minute RK45. It remains conditionally validated and is not promoted into frozen Runtime Core.
2. **Human cockpit color:** `P_EMISSION_V0_1`, an explainable compression retaining every numerical field, phase, turning tendency, confidence, domain, stability, and reasons.
3. **Future execution decision:** not implemented. GREEN/AMBER/RED are not BUY/HOLD/SELL.

## Split and policy

Development used 37,887 rows/88 sessions through 2023-08-04. Untouched Test014 policy validation used 17,312 rows/39 sessions from 2023-08-07. The validation rows were previously present in SPY F4 development, so this validates only the new emission policy.

Development selected one-step direct-reversal debounce. Policy SHA-256: `cae56998bb061cb477b01e9f44b5e47358185841e79d01fd03e5e8afc99a1e7a`. It reduced direct reversals from 889 to 27 on development while preserving precursor recall, but total color changes rose slightly.

## Untouched policy validation

| Evidence | Result |
|---|---:|
| GREEN / AMBER / RED | 18.33% / 62.56% / 19.10% |
| In-session color changes | 5,245 |
| Changes/session | 134.49 |
| Direct GREEN->RED / RED->GREEN | 0 / 0 |
| Local maxima detected | 357 / 1,601 (22.30%) |
| Local minima detected | 378 / 1,601 (23.61%) |
| Median detected lead | 4 minutes |
| False deterioration / recovery | 53.99% / 53.57% |
| RK failures / INVALID | 0 / 0 |

Prior AMBER appears before 93.63% of maxima and 93.13% of minima, but AMBER occupies 62.56% overall and is therefore not discriminating enough. Prior RED/maximum and GREEN/minimum rates are 45.53% and 43.35%. The policy provides causal trajectory context but insufficiently selective turn warning.

## Domain and confidence

OUT_OF_DOMAIN validation P2 MAE/RMSE is 0.003834/0.005313 versus 0.003054/0.004200 IN_DOMAIN. LOW confidence P2 MAE/RMSE is 0.003786/0.005273 versus 0.002961/0.003969 HIGH. Magnitude reliability degrades as intended, but sign/state accuracy increases in LOW/OUT_OF_DOMAIN strata, so confidence must not be described as probability calibration. Domain exit never automatically maps RED.

## Real-time foundation

`MarketObservation`, `PriceEngine.observe`, and JSON-serializable `PriceEmission` are additive runtime-oriented interfaces. Full historical replay through this interface is deterministic and byte-equivalent to the validation harness. Execution schema, cockpit specification, paper-account specification, and SPY-only completion roadmap are present but inactive.

Four objectively selected validation charts cover trend, quiet, reversal, and noisy sessions under `output/test014_charts`.

## Decision

The emission is causal, explainable, deterministic, and structurally compatible with a future cockpit, but turn recall, false warnings, and chatter prevent READY classification. Do not activate cockpit reliance, V Engine integration, execution, paper trading, live feed, or broker. Refine and independently validate the P-emission policy first without P&L.

## Direct answers

1. SPY source unchanged? **Yes.**
2. Frozen prior tests preserved? **Yes.**
3. Test006B lineage verified? **Yes; read-only foundational Emitter evidence, no rerun.**
4. Test007 HOLD semantics preserved? **Yes: FLAT remains FLAT; LONG remains LONG.**
5. Price/Volume separation preserved? **Yes.**
6. Test013C unchanged? **Yes.**
7. EEM skipped? **Yes.**
8. VXX skipped? **Yes.**
9. Authoritative SPY Price model verified? **Yes.**
10. Exact authority? **F4 centered/scaled affine ridge, lambda 1, W30, `[P,P1,P2]`, RK45 one minute.**
11. State preserved? **Yes.**
12. RK45 preserved? **Yes.**
13. One-minute causal propagation preserved? **Yes.**
14. Future observations in E_P(t)? **No.**
15. Numerical emission created? **Yes.**
16. Current P/P1/P2 preserved? **Yes.**
17. Projected P/P1/P2 preserved? **Yes.**
18. Acceleration/deceleration identified? **Yes.**
19. Turning tendency identified? **Yes.**
20. Domain state preserved? **Yes.**
21. Confidence preserved? **Yes, deterministic and non-probabilistic.**
22. Reason codes for every color? **Yes.**
23. GREEN simply P1>0? **No.**
24. RED simply P1<0? **No.**
25. Color equals trade action? **No.**
26. Chronological split used? **Yes.**
27. Split? **Development through 2023-08-04; validation from 2023-08-07, 88/39 sessions.**
28. Policy frozen before validation? **Yes.**
29. Policy SHA-256? **cae56998bb061cb477b01e9f44b5e47358185841e79d01fd03e5e8afc99a1e7a.**
30. Validation used for tuning? **No.**
31. Validation maxima? **1,601.**
32. Prior deterioration emission? **357, 22.30%.**
33. Median maximum lead? **4 minutes.**
34. Validation minima? **1,601.**
35. Prior recovery emission? **378, 23.61%.**
36. Median minimum lead? **4 minutes.**
37. False precursor rate? **54.54% combined; 53.99% deterioration and 53.57% recovery.**
38. GREEN occupancy? **18.33%.**
39. AMBER occupancy? **62.56%.**
40. RED occupancy? **19.10%.**
41. Color changes/session? **134.49 in-session.**
42. Direct GREEN->RED? **0 in validation.**
43. Direct RED->GREEN? **0 in validation.**
44. Hysteresis necessary? **Necessary for direct-reversal suppression, insufficient for overall chatter.**
45. Frozen before validation? **Yes.**
46. IN_DOMAIN performance? **P2 MAE/RMSE 0.003054/0.004200; sign 82.04%; state 64.79%.**
47. OUT_OF_DOMAIN performance? **P2 MAE/RMSE 0.003834/0.005313; sign 93.34%; state 89.26%.**
48. Confidence correlated with reliability? **Magnitude error worsened from HIGH to LOW, but sign/state did not; mixed.**
49. Domain exit automatically RED? **No.**
50. RK failures INVALID? **Policy guarantees yes; observed failures were zero.**
51. Volume used? **No.**
52. P/V fusion? **No.**
53. P&L tuning? **No.**
54. BUY implemented? **No.**
55. SELL implemented? **No.**
56. SHORT implemented? **No.**
57. Execution Controller activated? **No.**
58. Broker connected? **No.**
59. MarketObservation contract? **Yes.**
60. PriceEmission contract? **Yes.**
61. Historical/live shared interface? **Yes, vendor-neutral MarketObservation.**
62. PriceEmission JSON serializable? **Yes.**
63. Future Execution Policy schema? **Yes, inactive.**
64. Paper-account specification? **Yes, not implemented.**
65. Cockpit specification? **Yes.**
66. Real-time roadmap? **Yes, SPY-only.**
67. Reusable logic runtime-oriented? **Yes, additive `spy_price_engine`.**
68. Validation logic separate? **Yes, under `diagnostics`.**
69. Replay deterministic? **Yes.**
70. Classification? **SPY_P_ENGINE_EMISSION_CONDITIONAL.**
71. Ready as cockpit lamp? **Not for active reliance; experimental review only.**
72. Next missing component? **Refined, independently validated P-emission policy with lower chatter and better turn discrimination.**
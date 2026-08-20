# APTF Test 013C Result V0.1

Status: **PASS**  
Acceptance: **187/187 PASS**  
Classification: **SECOND_EXTERNAL_REPLICATION_CONDITIONAL**

## Source and cover

DIA was unseen and predesignated before profiling. The source has 119,715 rows from 2022-09-30 04:00:00 through 2023-09-29 17:22:00 across 251 dates. `close` maps to $P$. Fourteen initialization rows were excluded. Primary cover is 84,361 rows and sensitivity cover is 72,702 rows, both spanning 251 sessions.

## Activity characterization

DIA has 3,627 unchanged contiguous prices (3.43%), median absolute movement 0.06, Q95 0.26, Q99 0.45, and median relative movement 0.0181%. SPY/QQQ have the same 0.06 raw median and higher unchanged rates. DIA raw upper movement quantiles are somewhat lower, but relative activity is above SPY and near QQQ. The quietness impression is mixed, not a source-precision effect.

## Primary replication

| Metric | F0_W15 | F4_L1_W30 |
|---|---:|---:|
| P2 MAE / RMSE | 0.011789 / 0.284681 | 0.003055 / 0.004294 |
| P2 Q99 / Q99.9 | 0.077171 / 0.317172 | 0.013901 / 0.025635 |
| P2 maximum | 78.179149 | 0.077392 |
| P2 sign accuracy | 78.41% | 87.53% |
| State accuracy | 66.89% | 75.88% |
| Perturbation Q99 | 66.1613 | 2.6398 |
| Domain exit rate | 77.60% | 45.92% |
| Jacobian max-real Q99 | 4.8075 | 0.7233 |
| RK failures | 0 | 0 |

F4 reduces central, tail, extreme, perturbation, domain, and Jacobian instability while improving P2 sign by 9.113 points and state accuracy by 8.989 points. This closely reproduces SPY and QQQ.

## Low-motion evidence

On exact-zero movement rows, F4 reduces P2 MAE from 0.009757 to 0.002338, improves P2 sign from 80.30% to 88.69%, and lowers exits from 77.14% to 45.21%. F4 improves P2 MAE/RMSE, sign/state, and domain behavior in every movement band. Stabilization is not dependent on large movements.

## Decision

The three-instrument replication signature is strong, but the result remains conditional because transition recall is approximately 10-11%, local-domain exits remain 45.92%, and positive Jacobian maxima remain common. W30 is acceptably robust and unchanged. No Runtime or cockpit promotion is authorized. EEM is the recommended next predesignated replication.

## Direct answers

1. DIA source located? **Yes.**
2. SHA-256? **3b76423cc064f553ba2d7ad3407687f1ea61f0de8ad242f5347410a9f6be930f.**
3. Period? **2022-09-30 04:00:00 through 2023-09-29 17:22:00 local source time.**
4. Rows? **119,715.**
5. Sessions? **251.**
6. Prior architecture development use? **No.**
7. Frozen before profiling? **Yes.**
8. Freeze SHA-256? **a5eb9a9867cc2b08ec9670a3609df79f033bb10bda2df025be110d6eea42c6ba.**
9. Price mapped as SPY/QQQ? **Yes, close.**
10. F4 unchanged? **Yes.**
11. Lambda exactly 1? **Yes.**
12. W30 unchanged? **Yes.**
13. State `[P,P1,P2]`? **Yes.**
14. RK45 unchanged? **Yes.**
15. Derivatives unchanged? **Yes.**
16. Zero/tolerance unchanged? **Yes.**
17. SPY coefficients transferred? **No.**
18. QQQ coefficients transferred? **No.**
19. DIA identified local F_P causally? **Yes.**
20. Future DIA observations in fits? **No.**
21. Future DIA observations in RK? **No.**
22. Exactly unchanged consecutive prices? **3,627.**
23. Percentage? **3.4291%.**
24. Smallest nonzero increment? **0.0001.**
25. Median absolute movement? **0.06.**
26. Q95 absolute movement? **0.26.**
27. Q99 absolute movement? **0.45.**
28. Median relative movement? **0.00018094 (0.0181%).**
29. Visual quietness supported? **Mixed; not materially quieter.**
30. Quieter after Price-level adjustment? **No clear material quietness; above SPY and near QQQ median relative movement.**
31. Source precision explanation? **No; all three sources show four decimals and 0.0001 minimum increment.**
32. Unchanged observations preserved? **Yes.**
33. Initialization rows excluded? **Yes, 14.**
34. Primary common cover? **84,361.**
35. Sessions represented? **251.**
36. DIA F0 P2 MAE? **0.0117890021.**
37. DIA F4 P2 MAE? **0.0030547639.**
38. DIA F0 P2 RMSE? **0.2846812277.**
39. DIA F4 P2 RMSE? **0.0042938518.**
40. DIA F0 P2 Q99.9? **0.3171716136.**
41. DIA F4 P2 Q99.9? **0.0256351509.**
42. DIA F0 P2 maximum? **78.1791488705.**
43. DIA F4 P2 maximum? **0.0773916218.**
44. DIA F4 P2 sign accuracy? **87.5262%.**
45. DIA F4 state accuracy? **75.8775%.**
46. DIA F4 perturbation Q99? **2.6397650197.**
47. DIA F4 exit rate? **45.9241%.**
48. DIA F4 Jacobian Q99? **0.7232780589.**
49. RK failures? **F4 0; F0 0.**
50. Material stabilization? **Yes.**
51. Central error replicated? **Yes.**
52. Tail improvement replicated? **Yes.**
53. P2 sign improvement replicated? **Yes.**
54. Exact sign improvement? **+9.1132 percentage points.**
55. Versus SPY/QQQ? **SPY +8.9973, QQQ +9.0082, DIA +9.1132 points.**
56. State improvement replicated? **Yes.**
57. Exact state improvement? **+8.9888 percentage points.**
58. Perturbation stabilization? **Yes.**
59. Domain stabilization? **Yes, partially; exits remain high.**
60. Jacobian stabilization? **Yes, partially; magnitude falls but positivity remains.**
61. F4 on exact-zero/low-motion? **Yes, materially stabilized.**
62. F4 on higher-motion observations? **Yes.**
63. Dependent on high-motion rows? **No.**
64. Windows broadly consistent? **Yes.**
65. W30 replaced? **No.**
66. Lambda retuned? **No.**
67. Derivatives changed? **No.**
68. Zero tolerance changed? **No.**
69. Smoothing added? **No.**
70. Unchanged rows removed? **No.**
71. Volume used? **No.**
72. P&L calculated? **No.**
73. Execution logic changed? **No.**
74. SHORT implemented? **No.**
75. Cockpit thresholds? **No.**
76. AutoPilot? **No.**
77. Runtime Core modified? **No.**
78. Classification? **SECOND_EXTERNAL_REPLICATION_CONDITIONAL.**
79. Three-instrument conclusion? **Strong, conditional replication of the same method.**
80. Adaptive method supported? **Yes, conditionally.**
81. Universality? **No.**
82. EEM next? **Yes, predesignated and unchanged.**
83. Cockpit work in parallel? **No; resolve replication/domain/transition evidence first.**
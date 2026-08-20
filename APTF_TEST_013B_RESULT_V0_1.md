# APTF Test 013B Result V0.1

Status: **PASS**  
Acceptance: **176/176 PASS**  
Classification: **CONDITIONALLY_EXTERNALLY_VALIDATED_CONTINUOUS_CANDIDATE**

## Source and execution

QQQ was established as unseen before scoring. The immutable source contains 210,482 rows from 2022-09-30 04:00:00 through 2023-09-29 19:47:00 across 251 dates. Source `close` was mapped to $P$. The first 14 rows initialized the frozen causal quadratic derivative state.

Primary common cover contains 118,628 origins across 251 sessions. Sensitivity common cover contains 97,712 origins across the same 251 sessions. QQQ estimated all local centers, scales, and coefficients from its own causal history. Future leakage violations, SPY coefficient transfers, recursive predicted-state substitutions, alternative solvers, Volume inputs, P&L, trading changes, clipping, and deleted outliers are all zero.

## Primary scorecard

| Metric | F0_W15 | F4_L1_W30 |
|---|---:|---:|
| P MAE / RMSE | 0.129555 / 0.210780 | 0.129365 / 0.200650 |
| P1 MAE / RMSE | 0.029678 / 1.123782 | 0.026151 / 0.039197 |
| P2 MAE / RMSE | 0.100976 / 19.633515 | 0.004027 / 0.006105 |
| P2 median | 0.006502 | 0.002871 |
| P2 Q90 / Q95 | 0.026375 / 0.041386 | 0.008566 / 0.011304 |
| P2 Q99 / Q99.5 | 0.113713 / 0.188038 | 0.019702 / 0.024967 |
| P2 Q99.9 / maximum | 0.923775 / 6032.834209 | 0.049030 / 0.184976 |
| P2 RMSE/MAE | 194.4365 | 1.5159 |
| Price / P1 / P2 sign | 48.38% / 88.90% / 78.27% | 48.36% / 88.13% / 87.27% |
| Derivative state | 67.24% | 76.26% |
| Upper precision / recall | 73.33% / 19.23% | 68.15% / 11.45% |
| Lower precision / recall | 75.10% / 17.45% | 69.26% / 10.26% |
| Perturbation Q99 | 50.3518 | 2.6663 |
| Domain exit rate | 77.78% | 45.07% |
| Jacobian max-real Q99 | 4.9461 | 0.7655 |
| RK failures | 1 | 0 |

F4 materially stabilized QQQ relative to QQQ F0. The same central stabilization directions observed on SPY reappeared on QQQ.

## Window sensitivity

On 97,712 common rows, W15/W30/W60 P2 MAE is 0.004155/0.003977/0.004049 and P2 RMSE is 0.006011/0.005820/0.005997. W30 is not highly fragile. It remains primary and was not replaced.

## Decision

Method generalization is supported, coefficient transfer was not tested, and universality cannot be claimed. External validation remains conditional because transition recall is weak, F4 still exits its local envelope on 45.07% of paths, and nearly all local Jacobians retain a positive maximum-real eigenvalue despite substantial magnitude reduction.

Runtime and cockpit promotion remain prohibited. DIA is the recommended next independent replication.

## Direct answers

1. QQQ source located? **Yes.**
2. Exact SHA-256? **c326e1e63886c444f75bb3d0bd87907490eac220931a742050faf3a03815e55e.**
3. Period? **2022-09-30 04:00:00 through 2023-09-29 19:47:00 America/New_York local source time.**
4. Rows? **210,482.**
5. Trading sessions? **251 date sessions.**
6. Source column mapped to P? **close.**
7. Mapping identical to SPY? **Yes.**
8. Prior QQQ use in Tests009-013? **No source-data use; one provider-neutral schema capability test only.**
9. QQQ in F4 development? **No.**
10. QQQ in lambda selection? **No.**
11. QQQ in W30 selection? **No.**
12. Unseen status established before scoring? **Yes.**
13. Contract frozen before scoring? **Yes.**
14. Freeze SHA-256? **180a434860271f4268f86a7eb76b86af059bb4753158a357cc83911301c47f98.**
15. Primary exactly F4_L1_W30? **Yes.**
16. Lambda exactly 1? **Yes.**
17. State exactly `[P,P1,P2]`? **Yes.**
18. RK45 unchanged? **Yes.**
19. Horizon exactly one contiguous intraday minute? **Yes.**
20. SPY coefficients transferred? **No.**
21. SPY centers transferred? **No.**
22. SPY scales transferred? **No.**
23. QQQ identified its own local F_P? **Yes.**
24. Future QQQ observations in current fits? **No.**
25. Future QQQ observations inside RK? **No.**
26. Projections persisted before reveal? **Yes; solver outputs were frozen before the separate scoring pass.**
27. Initialization rows excluded? **Yes.**
28. Initialization rows? **14.**
29. Primary common cover? **118,628.**
30. Primary sessions? **251.**
31. QQQ F0 P2 MAE? **0.1009764664.**
32. QQQ F4 P2 MAE? **0.0040274580.**
33. QQQ F0 P2 RMSE? **19.6335153348.**
34. QQQ F4 P2 RMSE? **0.0061050963.**
35. QQQ F0 P2 Q99.9? **0.9237751236.**
36. QQQ F4 P2 Q99.9? **0.0490301229.**
37. QQQ F0 maximum P2 error? **6032.8342087408.**
38. QQQ F4 maximum P2 error? **0.1849756473.**
39. QQQ F4 P2 sign accuracy? **87.2737%.**
40. QQQ F4 derivative-state accuracy? **76.2586%.**
41. QQQ F4 upper precision? **68.1493%.**
42. QQQ F4 upper recall? **11.4522%.**
43. QQQ F4 lower precision? **69.2586%.**
44. QQQ F4 lower recall? **10.2557%.**
45. QQQ F4 perturbation Q99? **2.6663140204.**
46. QQQ F4 local-domain exit rate? **45.0695%.**
47. QQQ F4 Jacobian max-real Q99? **0.7654645695.**
48. F4 RK failures? **0.**
49. F4 materially stabilized QQQ? **Yes.**
50. P2 MAE pattern generalized? **Yes.**
51. P2 RMSE pattern generalized? **Yes.**
52. Extreme-tail improvement generalized? **Yes.**
53. P2 sign improvement generalized? **Yes.**
54. Derivative-state improvement generalized? **Yes.**
55. Perturbation stabilization generalized? **Yes.**
56. Local-domain stabilization generalized? **Yes, partially; exits remain high.**
57. Jacobian stabilization generalized? **Yes, partially; magnitudes fell but positivity remains.**
58. W15/W30/W60 broadly consistent? **Yes.**
59. W30 highly fragile? **No.**
60. W30 replaced? **No.**
61. Lambda retuned? **No.**
62. QQQ-specific model created? **No.**
63. Volume used by F_P? **No.**
64. QQQ Volume analyzed as a second engine? **No.**
65. Price/Volume fusion created? **No.**
66. P&L calculated? **No.**
67. BUY/HOLD/SELL modified? **No.**
68. SHORT implemented? **No.**
69. Cockpit colors created? **No.**
70. AutoPilot implemented? **No.**
71. Broker connected? **No.**
72. Runtime Core modified? **No.**
73. Final classification? **CONDITIONALLY_EXTERNALLY_VALIDATED_CONTINUOUS_CANDIDATE.**
74. Cross-instrument adaptive candidate supported? **Yes, conditionally.**
75. Coefficient transfer supported? **No; it was not the tested hypothesis.**
76. Method generalization supported? **Yes.**
77. Universality claim supported? **No.**
78. DIA next? **Yes, as a predesignated independent replication.**
79. Specific concern before/through replication? **Local-domain exits, low transition recall, and positive local max-real eigenvalues.**
80. Begin cockpit envelopes in parallel? **No; complete DIA replication first.**
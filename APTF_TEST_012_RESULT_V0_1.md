# APTF Test 012 Price Vector-Field Identification and RK45 Compatibility V0.1

Status: **PASS**  
Acceptance: **140/140 PASS**  
Outcome: **conditional stabilized continuous candidate found; discrete evolution remains current safe architecture pending independent validation**

## Baseline diagnosis

All 90,968 Test 011 projections and six solver failures were preserved. P2 absolute error median/Q90/Q95/Q99/Q99.5/Q99.9/max was `0.00368468 / 0.01786465 / 0.02737300 / 0.07365958 / 0.12106008 / 0.56330347 / 2632.48781515`.

The 91 top-0.1% trajectories had median max-real eigenvalue 8.136 versus 1.481 typical, physical P2 feedback 8.301 versus 1.621, condition 36.24 versus 18.05, local-domain exit 100% versus 1.10% matched controls, and median within-minute F_P growth 3,356x. Initial P2 was not the primary discriminator. The mechanism is positive continuous P2 feedback causing F_P growth after leaving local support.

## Candidate study

Candidate freeze SHA-256: `41e067ae63acab713d7a7c8161356dc7429646710b8dc9e4b2cf3b5c42a7d55f`. Implemented variants: 22; F5 was predeclared NOT IMPLEMENTED because a scalable nonarbitrary constrained estimator could not be authorized. Exact common cover: 45,658 rows; candidate projection rows: 1,004,476; RK failures/nonfinite endpoints: 0.

F1/F2/F3 are coordinate-equivalent affine views and matched exactly. Ridge λ=1 materially stabilized the vector field.

| Metric | F0 W15 | F4 λ1 W30 |
|---|---:|---:|
| P MAE | 0.10226744 | 0.10233640 |
| P1 MAE | 0.01888602 | 0.02034894 |
| P2 MAE | 0.01019328 | 0.00309358 |
| P2 RMSE | 0.04708815 | 0.00420998 |
| P2 median AE | 0.00543404 | 0.00238362 |
| P2 Q99 | 0.07165190 | 0.01275624 |
| P2 Q99.9 | 0.31004895 | 0.02333245 |
| P2 max | 8.05651673 | 0.06057020 |
| RMSE/MAE | 4.6195 | 1.3609 |
| P2 sign | 78.26% | 87.25% |
| state accuracy | 66.92% | 75.95% |
| upper precision/recall | 75.66% / 19.68% | 71.75% / 11.97% |
| lower precision/recall | 77.71% / 18.37% | 71.52% / 11.08% |
| perturbation Q99 | 95.52 | 2.73 |
| median condition | 19.42 | 7.83 |
| median max-real eigenvalue | 1.84 | 0.42 |
| local-envelope exit | 77.62% | 45.97% |

F4 λ1 W15 has best direction/state/perturbation; W30 best endpoint/Q99.9; W60 best maximum tail/domain/conditioning. F4 λ1 W30 is the strongest overall compromise, but lower transition recall and substantial domain exits remain.

## Decision

`[P,P1,P2]` supports a **conditional** one-minute continuous field under tested ridge identification. Recommended experimental candidate: centered/scaled affine ridge λ=1, W30. It is not authorized to replace frozen F0 or enter Control/Runtime until an independent chronological validation passes. RK45 remains experimental. Current safe evidence favors Test 010 discrete adaptive evolution.

## Direct answers

1–5. Runtime/Test009/Test009V/Test010/Test011 modified? **NO / NO / NO / NO / NO.**
6. Outliers preserved? **Yes.**
7–10. Test011 P2 median/Q99/Q99.9/max? **0.00368468 / 0.07365958 / 0.56330347 / 2632.48781515.**
11. Main distinction? **Positive Jacobian/P2 feedback, F_P growth, and local-domain exit.**
12. Large initial P2? **No clear association.**
13. Large initial F_P? **Mixed; severe upper tail higher.**
14. F_P grows rapidly? **Yes, median 3,356x severe.**
15. Poor conditioning? **Moderate association.**
16. Positive eigenvalues? **Strong association.**
17. Domain exit? **Strong: 100% severe.**
18. t_local instability? **Removing time improves tails, but ridge is the decisive stabilizer; mixed contribution.**
19. J_P normalized by Δt? **Yes.**
20. Gap targets excluded? **Yes.**
21. Leakage? **0.**
22. Structural identities preserved? **Yes.**
23. Only dP2/dt investigated? **Yes.**
24–25. Lowest P2 MAE/RMSE? **F4 λ1 W30.**
26. Smallest Q99.9? **F4 λ1 W30.**
27. Smallest maximum? **F4 λ1 W60.**
28–29. Best P2 sign/state? **F4 λ1 W15.**
30. Best transition precision? **F4 λ0.01 W15.**
31. Best transition recall? **F0 W15.**
32. Best perturbation robustness? **F4 λ1 W15.**
33. Best conditioning? **Affine W60 coordinate-equivalent views.**
34. Lowest domain exit? **F4 λ1 W60.**
35. Removing time improve stability? **Yes versus F0, with endpoint tradeoffs.**
36–37. Centering/scaling? **Numerically useful but function-class equivalent without regularization; not sufficient alone.**
38. Regularization improve stability? **Yes materially.**
39. F5 implemented? **NO, predeclared with reason.**
40. Explosions reduced without clipping? **Yes; ridge reduced max from 8.06 to ~0.06.**
41. Trajectories clipped? **NO.**
42. RK45 constant? **Yes.**
43. Alternative solver rescue? **NO.**
44–45. P&L/trading labels used? **NO / NO.**
46–47. Volume added/modified? **NO / NO.**
48. Best continuous field materially better? **Yes in P2/tails/stability; not uniformly in P/P1/transitions.**
49. Direction/transition information sufficient? **Direction yes conditionally; transition recall remains weak.**
50. Tail stability acceptable? **Materially improved, conditional pending independent validation.**
51. Perturbation stability? **Materially improved; conditional.**
52. Keep RK45? **Conditional experimental evaluation only.**
53. Discrete evolution favored now? **Yes until independent validation.**
54. State insufficient? **Not established; ridge stabilization shows state may suffice locally.**
55. Next problem? **Independent chronological validation of F4 λ1 W30 and W15/W60 sensitivity.**
56. Begin cockpit colors? **NO.**

No Volume experiment, trading rule, P&L, color, AutoPilot, broker, clipping, winsorization, or alternative solver was used.

Next action: **STOP FOR HUMAN REVIEW. Do not begin the next test.**
# APTF Test 014B Result V0.1

## Scope Separation

- PRICE ENGINE MATHEMATICS: **FROZEN**
- PRICE EMISSION: **FROZEN INPUT TO INTERPRETER**
- COCKPIT INTERPRETATION: **TEST-014B SUBJECT**
- EXECUTION: **NOT PART OF TEST**

## Classification

**SPY_P_ENGINE_COCKPIT_CONDITIONAL**

V0.2 improves readability, but untouched-validation precision/recall or false-warning evidence remains mixed; no V0.3 was created.

## Validation Comparison

| Metric | V0.1 | V0.2 | Delta |
|---|---:|---:|---:|
| AMBER occupancy | 62.5635% | 17.0344% | -45.5291% |
| Changes/session | 134.4872 | 112.3846 | -22.1026 |
| Maxima precision | 46.0118% | 44.4444% | -1.5674% |
| Maxima recall | 22.2986% | 13.5540% | -8.7445% |
| Minima precision | 46.4260% | 46.9767% | 0.5507% |
| Minima recall | 23.6102% | 13.8039% | -9.8064% |

## Regime Diagnostics

| Regime | Sessions | AMBER | Changes/session |
|---|---:|---:|---:|
| QUIET | 6 | 15.97% | 101.50 |
| UP_TREND | 8 | 16.64% | 108.12 |
| DOWN_TREND | 5 | 17.16% | 114.60 |
| REVERSAL | 12 | 17.30% | 123.92 |
| NOISY | 8 | 17.68% | 111.62 |

## Direct Answers

1. Yes; Test 014 was reproduced at the baseline gate.

2. Validation had 17312 observations; GREEN 3174, AMBER 10831, RED 3307, INVALID 0; 5245 changes and 134.487179487179 changes/session.

3. Yes; the SPY source hash was unchanged.

4. Yes; Price Engine mathematics was unchanged.

5. Yes; F4 was unchanged.

6. Yes; lambda remained 1.

7. Yes; W remained 30.

8. Yes; RK45 was unchanged.

9. Yes; [P,P1,P2] was unchanged.

10. Yes; the projection horizon remained one minute.

11. Yes; MarketObservation was unchanged.

12. Yes; PriceEmission was preserved.

13. Yes; P_EMISSION_V0_1 was retained as control.

14. Five V0.2 candidates plus the V0.1 control.

15. One- and two-observation persistence, normalized zero approach, projected-P1 crossing, and state-aware hysteresis families.

16. Yes; the family was deliberately limited to five candidates.

17. TRANSITION_EVIDENCE_P1: crossing, or opposing acceleration with normalized zero proximity <= 0.90 and deceleration strength >= 0.05; one observation; no candidate hold.

18. P1 zero proximity and deceleration strength.

19. Z1=abs(projected_P1)/max(abs(P1),abs(projected_P1),epsilon); D1=opposing_abs(projected_P1-P1)/max(abs(P1),epsilon).

20. Causal per-row velocity normalization; no future or full-cover statistic is used.

21. epsilon=0.0035332071428566536; it bounds both direction and ratio denominators.

22. One qualifying observation; longer persistence candidates lost too much development recall.

23. An observed P1 direction change receives a one-row AMBER bridge; candidate hold is zero.

24. UP/DOWN stable, accelerating, decelerating; TURN_UP/DOWN_CANDIDATE; DIRECTION_CHANGE_TRANSITION; NEAR_STATIONARY; UNCERTAIN; INVALID.

25. GREEN / AMBER / RED.

26. Yes; INVALID is retained separately.

27. No; P1 > 0 and P2 < 0 does not automatically mean AMBER.

28. No; P1 < 0 and P2 > 0 does not automatically mean AMBER.

29. Opposition alone is insufficient; normalized proximity and minimum deceleration strength, or an actual projected crossing, are required.

30. Yes on development; zero proximity was retained in the selected transition filter.

31. Yes; projected-P1 crossing was useful in 48.42% of validation crossing events.

32. Conditionally; persistence improved precision but longer lengths reduced recall.

33. Yes for transparent sequence diagnostics; no retrospective sequence entered the policy.

34. It was evaluated; forcing LOW confidence to AMBER was not selected.

35. Domain state is retained, but automatic domain coloring was not selected.

36. 62.563539741220%.

37. 17.034426987061%.

38. -45.529112754159% absolute; -72.772597174776% relative.

39. 134.487179487179.

40. 112.384615384615.

41. 22.102564102564, or 16.434699714013%.

42. 2.0 minutes.

43. 1.0 minutes.

44. 46.011816838996% vs 44.444444444444%.

45. 22.298563397876% vs 13.554028732042%.

46. 53.988183161004% vs 55.555555555556%.

47. 4.0 vs 3.0 minutes.

48. 46.426043878273% vs 46.976744186047%.

49. 23.610243597751% vs 13.803872579638%.

50. 53.573956121727% vs 53.023255813953%.

51. 4.0 vs 4.0 minutes.

52. Mixed; minima improved while maxima worsened.

53. Yes; medians remained 3 and 4 minutes.

54. No; both retained more than half of V0.1 recall.

55. Yes; occupancy fell by 45.53 percentage points.

56. Yes; chatter fell 16.43%.

57. Yes; direct GREEN->RED count is 0.

58. Yes; direct RED->GREEN count is 0.

59. Quiet periods: AMBER 15.97%, 101.50 changes/session.

60. Sustained trends: UP AMBER 16.64% and DOWN AMBER 17.16%.

61. Reversals: AMBER 17.30%, 123.92 changes/session.

62. Noisy sessions: AMBER 17.68%, 111.62 changes/session.

63. No; future turn labels were isolated to retrospective scoring.

64. No; validation was not used to tune V0.2.

65. Yes; V0.2 was frozen and hashed before validation.

66. bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef.

67. No; P&L was not used.

68. No; Volume was not used.

69. No; the V Engine was not modified.

70. No; BUY was not implemented.

71. No; SELL was not implemented.

72. No; SHORT was not implemented.

73. No; an Execution Controller was not implemented.

74. No; no broker was connected.

75. No; no external ETF was used.

76. Yes; the interpreter accepts one PriceEmission at a time.

77. Previous motion/color, opposing direction/count, and candidate direction/age.

78. Yes; all retained state is bounded.

79. 3.300000 microseconds.

80. 7.700000 microseconds.

81. Yes; two complete replays were byte-equivalent before artifact serialization.

82. SPY_P_ENGINE_COCKPIT_CONDITIONAL.

83. No; the lamp remains conditional.

84. The independent SPY V Engine is next only if the P cockpit is classified READY.

85. Maxima false-warning rate worsened and both directional recalls declined; the stability gain is real but transition discrimination remains mixed.

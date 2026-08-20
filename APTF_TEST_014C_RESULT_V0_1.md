# APTF Test 014C Result V0.1

## Scope Separation

- P ENGINE: **frozen conditional observer; not modified**
- V ENGINE: **Test-014C subject**
- P/V INTERVAL OBSERVATION: **descriptive only; no fusion**
- EXECUTION: **absent**

## Classifications

- V Engine: **SPY_V_ENGINE_COCKPIT_READY**
- Dual observation: **SPY_PV_INTERVAL_OBSERVATION_READY**

## V Validation

GREEN 50.7278%; AMBER 40.8214%; RED 8.4508%; INVALID 0.0000%. Changes/session: 44.7692. Median interval: 7.0 minutes.

## Interval Evidence

P intervals: 14611. V intervals: 5713. Joint intervals: 18561. P/V/joint invariants: PASS/PASS/PASS. Duration convention: observation count for contiguous one-minute emissions; final duration is retrospective only, while aligned rows expose causal age-so-far.

## Direct Answers

1. Yes. 2. Yes. 3. bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef. 4. No. 5. No.

6. Test 009V causal normalized Volume and derivatives; Test 010 discrete G_V point observer plus 15-row interval state; Test 011 independent discrete observer, no RK.

7. Source volume, preserved as V_RAW. 8. V_N=V_RAW/trailing-15 median. 9. Causal 3-row quadratic first derivative. 10. Its second derivative.

11. ROLLING_MEDIAN_RATIO_15. 12. Yes. 13. Yes. 14. Sparse time-of-day normalization was rejected; causal local median retained.

15. No. 16. No. 17. No. 18. No. 19. No. 20. No. 21. Not applicable. 22. Existing authority rates Volume ODE suitability weak and selects discrete G_V.

23. Point +/-10 immediate; point +/-20 confirmation-2; interval-mean +/-10 confirmation-2; interval-mean +/-20 confirmation-3. 24. Four.

25. Minimum development changes/session under explicit occupancy and median-duration constraints. 26. Yes. 27. Yes. 28. f719134f241b00888099e237c02f237a2db4b59f02b25ea5498c51006991bcd8.

29. Activity above the causal baseline band. 30. Activity near baseline or pending confirmation. 31. Activity below the causal baseline band. 32. No.

33. 50.727818853974%. 34. 40.821395563771%. 35. 8.450785582255%. 36. 0.000000000000%. 37. 44.769230769231.

38. 13.0 minutes. 39. 6.0 minutes. 40. 4.0 minutes.

41. 6.0 minutes. 42. 1.0 minutes. 43. 6.0 minutes.

44. Yes. 45. Yes. 46. No. 47. No. 48. No. 49. duration_minutes=observation_count for contiguous one-minute emissions; elapsed_seconds is end-start. 50. Yes. 51. No.

52. 14611. 53. 5713.

54. 20.189362294625%. 55. 7.518796992481%. 56. 1.434140907825%. 57. 0.000000000000%.

58. 95.964783565664%. 59. 82.061628760088%. 60. 61.041819515774%. 61. 28.576669112252%.

62-65. All nine occupancies and duration statistics are in APTF_TEST_014C_PV_JOINT_REACTION_WINDOWS_V0_1.csv.

66. 1658 (31.306646525680%). 67. 2283 (43.108006042296%). 68. 1355 (25.585347432024%). 69. 1.0 minutes. 70. No. 71. No.

72. Yes. 73. Yes. 74. Yes. 75. Yes. 76. Yes. 77. No. 78. No. 79. No. 80. No. 81. No. 82. No. 83. No. 84. No. 85. No.

86. Yes. 87. 3.200000 microseconds. 88. SPY_V_ENGINE_COCKPIT_READY. 89. SPY_PV_INTERVAL_OBSERVATION_READY.

90. Yes. 91. Review the five full-session contiguous bands, short-interval tails, joint-state persistence, and descriptive transition separation before defining execution policy.

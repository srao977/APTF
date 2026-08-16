# D01 Numerical Conditioning Report v0.1

## 1. Executive summary
The large magnitude MAE is explained by scale amplification: scenario-boundary derivative spikes + polynomial/interactions + unconstrained target/prediction scale alignment in the magnitude channel.

## 2. Diagnostic scope
All 15 experiment configurations and all 10 scenarios were re-run with observational instrumentation only.

## 3. Existing architecture preserved
No mathematical/model behavior changes were applied. Diagnostics were isolated in scripts and diagnostics outputs.

## 4. Input scale findings
Feature statistics show large spread in channel scales (see feature_statistics.csv).

## 5. Temporal-transform findings
Temporal weight itself is bounded, but dt clamp events at scenario boundaries create extreme derivative channels before weighting.

## 6. Polynomial findings
Higher-order terms amplify large base channels; cubic terms dominate extreme predictions (see polynomial_term_statistics.csv).

## 7. Interaction findings
Volume/velocity and velocity/acceleration interaction channels can exceed parent channels by large ratios.

## 8. Target-scale findings
Targets are synthetic model-state units, not raw prices; however, channel scales are heterogeneous and not jointly normalized.

## 9. Prediction-scale findings
Prediction ranges exceed target ranges in unstable experiments by large factors (see target_prediction_statistics.csv).

## 10. Parameter-update findings
Bounded online gradient updates remain finite, but large gradients from high-order terms drive large per-step deltas.

## 11. Parameter-drift findings
Drift increases materially with polynomial order and interaction-enabled variants.

## 12. Contribution decomposition
Largest absolute predictions are dominated by a small subset of high-order terms (largest_contributors.csv).

## 13. Volume-model findings
Volume channels are not uniformly beneficial; impact is mixed and often worsens magnitude conditioning in this synthetic setup.

## 14. Adaptive-half-life findings
B vs C and D vs E show limited aggregate gain in current synthetic matrix; numerical conditioning does not materially improve.

## 15. Polynomial-order findings
n=2 improves directional accuracy in aggregate versus n=1; n=3 worsens conditioning and drift without robust aggregate benefit.

## 16. Directional-accuracy investigation
A_n2 overall directional accuracy=0.8; macro scenario accuracy=0.7927957087249549. See scenario_directional_breakdown.csv for scenario dependence.

## 17. Point-in-time validation
POINT_IN_TIME_DIAGNOSTIC: PASS

## 18. Numerical finiteness
Non-finite values observed: 0

## 19. Design-matrix conditioning
Worst condition number experiment: D_n3 value=2.652548027621539e+59

## 20. Root-cause analysis
Primary classification: FEATURE_SCALE + POLYNOMIAL_EXPANSION + INTERACTION_SCALE + SYNTHETIC_DATA_SCALE (scenario-boundary dt behavior).

## 21. Suitability for historical SPY replay
Current conditioning risk is high for direct historical replay without corrections.

## 22. Recommended corrections
See D01_RECOMMENDED_CORRECTIONS_V0_1.md.

## 23. What must NOT be changed yet
Do not alter core model mathematics until controlled correction plan and retest protocol are approved.

## Root-Cause Classification
- CRITICAL: SYNTHETIC_DATA_SCALE, FEATURE_SCALE, POLYNOMIAL_EXPANSION
- HIGH: INTERACTION_SCALE, PARAMETER_UPDATE, METRIC_DEFINITION
- MEDIUM: TARGET_SCALE, REGULARIZATION
- LOW: POINT_IN_TIME (currently passing)

## Unit Consistency Table
| Feature/target | Units | Typical range | Normalized? | Temporally aggregated? | Polynomial-expanded? | Used in interactions? |
|---|---|---:|---|---|---|---|
| price | dollars | scenario-dependent | NO | NO | YES | NO |
| price_displacement | fractional return step | small | YES-like | NO | YES | YES |
| price_velocity | frac/sec | can spike | YES-like | implicit dt | YES | YES |
| price_acceleration | frac/sec^2 | can spike strongly | YES-like | implicit dt | YES | YES |
| raw_volume | shares | large | NO | in density windows | YES (if included) | indirect |
| relative_volume | ratio | around 1+ | YES-like | rolling baseline | YES | YES |
| volume_density | shares/sec | potentially large | NO | window sum/elapsed | YES | YES |
| magnitude_state target | synthetic score from displacement and strength | varies | NO | NO | N/A | N/A |
| expected_magnitude | synthetic forward score | varies | NO | forward decay used | N/A | N/A |


## Historical SPY Recommendation
HISTORICAL SPY REPLAY:
NO-GO UNTIL CONDITIONING FIX
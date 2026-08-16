# D01 Recommended Corrections v0.1

## Issue 1
- Issue: Scenario-boundary time reset with persistent model state produces dt clamp at 1e-6 and extreme velocity/acceleration bursts.
- Evidence: first_instability_events.csv and feature_statistics.csv (price_velocity/price_acceleration spikes at scenario boundaries).
- Proposed correction: reset temporal state between scenarios for matrix evaluation or enforce monotonic global timestamps across concatenated scenarios.
- Expected benefit: removes artificial derivative blow-ups unrelated to model capacity.
- Possible downside: changes continuity assumptions across synthetic scenarios.
- Affected files: src/aptf_d01/runtime/experiment_runner.py, providers synthetic replay concatenation strategy.
- Retest required: full 15x10 matrix and determinism check.

## Issue 2
- Issue: Unscaled polynomial expansion magnifies already-large channels (especially cubic terms and interaction terms).
- Evidence: polynomial_term_statistics.csv and largest_contributors.csv.
- Proposed correction: scale-aware basis (standardized or bounded features before polynomial expansion).
- Expected benefit: improved numerical conditioning and lower drift.
- Possible downside: requires recalibration of thresholds and interpretation.
- Affected files: src/aptf_d01/parametric/basis.py and upstream feature scaling stage.
- Retest required: full matrix, range diagnostics, and metric comparison.

## Issue 3
- Issue: Magnitude channel target/prediction scale mismatch grows under polynomial/interactions.
- Evidence: target_prediction_statistics.csv prediction-to-target range ratios.
- Proposed correction: target scaling strategy and/or output-channel-specific learning-rate regularization.
- Expected benefit: reduced extreme magnitude errors.
- Possible downside: different convergence profile.
- Affected files: src/aptf_d01/model/adaptive_parametric_model.py and src/aptf_d01/parametric/multi_output_model.py configuration plumbing.
- Retest required: matrix and directional/magnitude tradeoff analysis.
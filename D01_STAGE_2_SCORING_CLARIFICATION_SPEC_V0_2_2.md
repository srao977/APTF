# D01 Stage 2 Scoring Clarification Specification v0.2.2

**AUTHORITATIVE SOURCE:** `D01_STAGE_2_SCORING_CLARIFICATION_ADDENDUM_V0_2_2.md`  
**PARENT AUTHORITIES:** Stage 2 Design v0.2 and Scoring Clarification v0.2.1  
**FREEZE ID:** `D01_STAGE2_SCORING_V0_2_2_FROZEN_20260815T185154Z`

In case of conflict, the frozen v0.2.2 addendum controls for the topics extracted here. This document creates no independent scientific authority.

## 1. Primary Records

Use the existing frozen eligible anchor population. Eligibility is fixed at anchor emission and is not changed by future availability. For each dimension and coordinate, one valid anchor contributes one equal-weight record.

Availability is dimension-specific. Exclude an unavailable anchor only from the relevant statistic and record a deterministic reason. Report eligible, available, excluded, and reason counts.

## 2. Primary 15-Minute Scores

At the fixed 15 elapsed-minute coordinate:

$$
\rho_S=\operatorname{Spearman}(strength_t,|b_{15,t}|E_{15,t}),
$$

$$
\rho_C=\operatorname{Spearman}(coherence_t,E_{15,t}),
$$

$$
\rho_U=\operatorname{Spearman}(uncertainty_t,A_{realized,15,t}),
$$

where

$$
A_{realized,15,t}=\frac{(1-E_{15,t})+D_{15,t}/(1+D_{15,t})+I_{amb,15,t}}{3}.
$$

Each expected direction is positive. Each primary null is zero.

## 3. Required Coordinates

- Strength: finite strength, slope, and efficiency.
- Coherence: finite coherence and efficiency.
- Uncertainty: finite uncertainty and all realized ambiguity components.

No imputation is permitted. Missing coordinates are not failures.

## 4. Exclusion Reasons

Use deterministic reason tracking, including as applicable:

- `BOUNDARY_CENSORED`
- `COORDINATE_UNAVAILABLE`
- `NONFINITE_PREDICTOR`
- `NONFINITE_SLOPE`
- `NONFINITE_EFFICIENCY`
- `AMBIGUITY_COMPONENT_UNAVAILABLE`

An exclusion from one statistic has no effect on another statistic for which the anchor is valid.

## 5. Secondary Diagnostics

The other fixed horizons, 1/5/30/60 minutes, and every adaptive 0.5x/1.0x/2.0x observation-half-life, forward-half-life, and forward-interval coordinate are secondary diagnostics.

Do not pool horizons, average horizons, build a composite horizon, choose the best horizon, or substitute a secondary result for the primary 15-minute result. Secondary diagnostics never alter a primary point estimate, interval, support label, or classification.

## 6. Weighting and Bootstrap

One valid anchor equals one record with weight one. Path length, overshoot, block, class, session, gap, duration, and adaptive scale do not alter scientific weight.

Retain the frozen 1,800-minute blocks, support thresholds, 2,000 (`2000`) deterministic chronological moving-block replicates, two-sided 95% percentile intervals, and four-level classifications. Bootstrap complete anchor records with block identity intact.

## 7. Continuing Authority

All Stage 2 v0.2 and v0.2.1 rules not explicitly clarified above remain unchanged, including observer geometry, duration concordance, perturbation co-primary adjudication, causality, reserve exclusion, deterministic replay, and canonical sealing.

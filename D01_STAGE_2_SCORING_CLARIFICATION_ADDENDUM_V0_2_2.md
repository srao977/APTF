# D01 Stage 2 Scoring Clarification Addendum v0.2.2

## 1. Status and Authority

**Status:** FROZEN SCORING CLARIFICATION ADDENDUM  
**Freeze ID:** `D01_STAGE2_SCORING_V0_2_2_FROZEN_20260815T185154Z`  
**Parent authorities:** `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md` and `D01_STAGE_2_SCORING_CLARIFICATION_ADDENDUM_V0_2_1.md`

This addendum supplements, and does not replace, Stage 2 Design v0.2 or Scoring Clarification v0.2.1. Those authorities continue to control every topic not explicitly clarified here. In a conflict limited to the primary horizon, anchor population, coordinate availability, exclusion, or weighting rules for strength, coherence, or uncertainty, this v0.2.2 addendum controls.

No historical primary outcome or reserve observation value was inspected. D01, the data partition, the observer, the fixed and adaptive horizon sets, support thresholds, bootstrap, censoring, reserve, replay, perturbation, and classification rules are unchanged.

## 2. Common Eligible Anchor Population

The primary population for strength, coherence, and uncertainty is the existing frozen eligible anchor population produced by canonical causal replay. No new warm-up, model-health, session, gap, direction, perturbation-class, or outcome-dependent population filter is introduced.

Eligibility is decided at anchor emission using only information available at that anchor. Future coordinate availability is not part of anchor eligibility. Each eligible anchor is considered once for each primary dimension.

## 3. Primary Coordinate

For strength, coherence, and uncertainty, the single primary coordinate is the fixed horizon of 15 elapsed minutes. The observer resolves that coordinate under the already-frozen first-at-or-after, overshoot, boundary, gap, session, and censoring policies.

Other fixed horizons, 1, 5, 30, and 60 elapsed minutes, are secondary diagnostics. All adaptive coordinates, 0.5x, 1.0x, and 2.0x observation half-life, forward half-life, and forward interval, are secondary diagnostics.

There is no pooling across horizons, no averaging across horizons, no composite horizon statistic, no best-horizon selection, and no replacement of the 15-minute primary result by any secondary result. Multiplicity remains descriptive as frozen.

## 4. Strength Primary Statistic

For eligible anchor $t$, let $S_t$ be emitted D01 strength. At the resolved 15-minute coordinate, let $b_{15,t}$ be realized through-origin raw-close slope and $E_{15,t}$ be realized path efficiency.

Define the realized strength target:

$$
Y_{S,t}=|b_{15,t}|E_{15,t}.
$$

The primary statistic is:

$$
\rho_S=\operatorname{Spearman}(S_t,Y_{S,t}).
$$

Expected direction: $\rho_S>0$.  
Primary null: $\rho_S=0$.

## 5. Coherence Primary Statistic

For eligible anchor $t$, let $C_t$ be emitted D01 coherence. At the resolved 15-minute coordinate, let $E_{15,t}$ be realized path efficiency.

The primary statistic is:

$$
\rho_C=\operatorname{Spearman}(C_t,E_{15,t}).
$$

Expected direction: $\rho_C>0$.  
Primary null: $\rho_C=0$.

## 6. Uncertainty Primary Statistic

For eligible anchor $t$, let $U_t$ be emitted D01 uncertainty. At the resolved 15-minute coordinate, use the frozen v0.2.1 realized ambiguity index:

$$
A_{realized,15,t}=\frac{(1-E_{15,t})+D_{15,t}/(1+D_{15,t})+I_{amb,15,t}}{3}.
$$

The primary statistic is:

$$
\rho_U=\operatorname{Spearman}(U_t,A_{realized,15,t}).
$$

Expected direction: $\rho_U>0$.  
Primary null: $\rho_U=0$.

## 7. Coordinate Availability and Exclusions

Coordinate availability is evaluated independently for each dimension at 15 elapsed minutes.

- Strength requires finite anchor strength, finite realized slope, and finite path efficiency.
- Coherence requires finite anchor coherence and finite path efficiency.
- Uncertainty requires finite anchor uncertainty and every finite component required by the frozen realized ambiguity index.

An eligible anchor missing a required coordinate or component is excluded only from the relevant statistic. It remains in the eligible anchor population and may contribute to every other statistic for which its required coordinates are available. There is no imputation and an exclusion is not counted as failure.

For every primary and secondary statistic, report total eligible anchors, available records, excluded records, and exclusion counts by deterministic reason code. At minimum support `BOUNDARY_CENSORED`, `COORDINATE_UNAVAILABLE`, `NONFINITE_PREDICTOR`, `NONFINITE_SLOPE`, `NONFINITE_EFFICIENCY`, and `AMBIGUITY_COMPONENT_UNAVAILABLE` as applicable.

## 8. Anchor Record and Weighting

One valid eligible anchor contributes exactly one record to a dimension/statistic at a coordinate. Every valid anchor record has equal weight one. Repeated bars inside the observer path do not create repeated records. Overshoot does not change record weight. Session, gap, block, class, duration, or adaptive-scale membership does not change record weight.

Block-bootstrap resampling preserves complete anchor records and their block identities. Duplicate selection of a block in a bootstrap replicate is resampling, not scientific weighting.

## 9. Support, Bootstrap, and Classification

The existing 1,800 elapsed-minute support blocks, `ADEQUATE >=30`, `LIMITED 10-29`, `INSUFFICIENT <10`, deterministic 2,000-replicate (`2000`) chronological moving-block bootstrap, two-sided 95% percentile interval, and four-level classification rules remain unchanged.

Primary support and classification for strength, coherence, and uncertainty use only their respective valid 15-minute anchor records. Secondary diagnostics cannot alter primary support, interval, effect, or classification.

## 10. Unchanged Rules

All v0.2 and v0.2.1 rules remain frozen, including:

- the eleven Stage 2 dimensions and their expected positive primary effects after orientation;
- 15-minute primary effects already frozen for state/kinematics, perturbation magnitude, and perturbation class;
- censor-aware duration concordance for persistence, reversal propensity, observation half-life, forward half-life, and forward interval;
- separate perturbation-class co-primary contrasts and their specialized adjudication;
- raw-close observer independence, sign/mirror invariance, causal replay, canonical sealing, reserve hard stop, and no tuning or model correction.

## 11. Non-Execution Attestation

- D01 modified: NO
- Stage 2 Design v0.2 modified: NO
- Scoring Clarification v0.2.1 modified: NO
- Historical primary outcomes inspected: NO
- Reserve observation values inspected: NO
- Historical replay started for this clarification: NO
- Scientific scores calculated for this clarification: NO

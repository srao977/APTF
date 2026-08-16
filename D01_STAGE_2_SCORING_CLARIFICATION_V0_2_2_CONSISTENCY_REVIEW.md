# D01 Stage 2 Scoring Clarification v0.2.2 Consistency Review

## 1. Review Status

**Reviewed addendum:** `D01_STAGE_2_SCORING_CLARIFICATION_ADDENDUM_V0_2_2.md`  
**Implementation extract:** `D01_STAGE_2_SCORING_CLARIFICATION_SPEC_V0_2_2.md`  
**Parents:** Stage 2 Design v0.2 and Scoring Clarification v0.2.1  
**Freeze ID:** `D01_STAGE2_SCORING_V0_2_2_FROZEN_20260815T185154Z`

This is a pre-implementation scientific consistency review. No primary historical outcome or reserve observation value was inspected.

## 2. Scope

The addendum resolves only the remaining primary-coordinate and record-construction ambiguity for strength, coherence, and uncertainty. It selects 15 elapsed minutes, defines per-dimension availability, freezes relevant-only exclusions with reason tracking, and requires one valid anchor/one equal-weight record.

It adds no observable, horizon, threshold, fitted weight, dataset filter, model correction, or execution result.

**Result: PASS**

## 3. Parent Compatibility

Strength remains association with $|b|E$, coherence remains association with $E$, and uncertainty remains association with the v0.2.1 ambiguity index. Spearman statistics, positive expected directions, and zero nulls match the parent contracts.

The selected 15-minute coordinate already belongs to the frozen fixed horizon set and matches the primary fixed coordinate used by the previously clarified fixed-horizon dimensions.

**Result: PASS**

## 4. Anchor Population and Availability

The existing eligible anchor population is preserved. Future availability does not change eligibility and therefore cannot introduce outcome-dependent anchor selection. Dimension-specific availability prevents missing uncertainty components, for example, from removing an otherwise valid coherence record.

Explicit eligible, available, excluded, and reason counts make every reduction auditable. No unavailable value is imputed or counted as failure.

**Result: PASS**

## 5. Weighting

One eligible anchor can contribute at most one equal-weight record to a given statistic and coordinate. Intrahorizon bars, overshoot, sessions, gaps, blocks, classes, and duration do not replicate or reweight anchors. Bootstrap block reselection is uncertainty resampling only.

**Result: PASS**

## 6. Horizon and Multiplicity

The 15-minute primary is fixed before execution. The other fixed and all adaptive coordinates remain secondary. The prohibition on pooling, averaging, composites, best-horizon selection, or primary substitution prevents post-outcome optimization. Secondary diagnostics cannot alter primary effects or classifications.

**Result: PASS**

## 7. Support and Bootstrap

Support is calculated from valid 15-minute records using the frozen 1,800-minute block identities and thresholds. The deterministic 2,000-replicate (`2000`) moving-block percentile interval is unchanged. Complete anchor records are resampled, preserving predictor, outcome coordinates, exclusions, and block identity.

**Result: PASS**

## 8. Causality and Reserve

Anchor predictors are immutable D01 emissions. Realized coordinates are computed only by the independent future raw-close observer. Future data scores a past anchor but never changes its state or eligibility. The primary/reserve boundary and reserve hard stop are unchanged.

**Result: PASS**

## 9. Other Dimensions

State/kinematics, persistence, reversal propensity, perturbation magnitude, perturbation class, observation half-life, forward half-life, and forward interval remain governed by v0.2 and v0.2.1. Perturbation co-primary classification and censor-aware duration concordance are not changed.

**Result: PASS**

## 10. Canonical Extraction

The implementation-facing specification reproduces the controlling formulas, primary horizon, population, availability, exclusion, weighting, secondary, no-selection, support, and bootstrap rules without adding authority.

**Result: PASS**

## 11. Integrity and Non-Execution

Parent files were treated as immutable. This review contains no historical effects, intervals, classifications, primary values, or reserve values. D01 was not modified and historical replay was not started.

**Result: PASS**

## 12. Final Decision

**DESIGN CONSISTENCY: PASS**

No genuine scientific ambiguity remains for implementation of the eleven frozen Stage 2 dimensions.

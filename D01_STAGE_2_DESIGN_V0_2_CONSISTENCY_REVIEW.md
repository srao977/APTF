# D01 Stage 2 Design v0.2 Consistency Review

## 1. Review Status

**Reviewed document:** `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`  
**Decision register:** `D01_STAGE_2_PREIMPLEMENTATION_DECISION_REGISTER_V0_2.md`  
**Review scope:** internal scientific, causal, temporal, and experimental consistency  
**Implementation/replay:** not performed

## 2. Authority Reviewed

- `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_1.md`
- `D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md`
- `D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS.md`
- `D01_V0_2_STAGE_1_SYNTHETIC_ACCEPTANCE_FREEZE.json`
- frozen D01 v0.2 observation/state/output interfaces
- Stage 2 partition metadata only

No primary historical outcomes or reserve observation values were used.

## 3. Decision Resolution Check

| ID | Decision | Resolution | Consistency result |
|---|---|---|---|
| 01 | Frozen input mapping | Minimum raw close/volume/timestamp/session mapping | PASS |
| 02 | Warm-up/readiness | Three accepted observations plus causal finite/health predicate | PASS |
| 03 | Independent realized state | Raw-close log-geometry observer and sign-based invalidation | PASS |
| 04 | Evaluation horizons | Fixed 1/5/15/30/60 and adaptive 0.5x/1x/2x | PASS |
| 05 | Calibration/support/dependence | Continuous primary effects, predictor quintiles, 1,800-minute block bootstrap | PASS |
| 06 | Session/gap stratification | Deterministic metadata-only strata, no deletions/resets | PASS |
| 07 | Censoring | Per-horizon right censor and gap interval censor | PASS |
| 08 | Multiplicity/reporting | One primary contract per dimension; effect/CI classification; optional BH-FDR | PASS |
| 09 | Design freeze/primary protocol | Separate post-review freeze and phased replay/seal/score lifecycle | PASS |

All nine scientific/experimental decisions are resolved. Human approval to freeze is a governance gate, not an unresolved design definition.

## 4. Realized-State Observer Independence

The observer uses only anchor raw close, subsequent raw closes, and elapsed timestamps. It does not use later D01 states, D01 adaptive reference/scale, fitted D01 parameters, trading outcomes, or reserve observations.

The emitted DMO supplies the claim being evaluated; it does not create the future observable. Comparing the DMO direction hierarchy to independent raw-close slope/progress is therefore not circular.

**Result: PASS**

## 5. Point-in-Time Causality

Canonical replay precedes future scoring and contains no realized-state labels. DMO/FMO records are sealed before read-only scoring. Future observations may score immutable past states and cannot enter state creation.

The input mapping excludes historical derived returns/ranges and uses only raw causal contract fields. `receive_time=event_time` is explicitly identified as a replay availability proxy rather than measured latency.

**Result: PASS**

## 6. Persistence and State Invalidation

Persistence claims that the current state remains recognizable. The observer defines recognition continuously through signed progress/slope and invalidates only on independently observed opposite-side displacement plus opposite slope. $T_{valid}$ is therefore a direct duration claim rather than next-bar direction.

State weakening does not automatically invalidate; it remains a distinct category. Recovery/new-state behavior does not rewrite the anchor state. Right and interval censoring are retained for survival analysis.

**Result: PASS**

## 7. Reversal Definition

Realized reversal requires both endpoint displacement and prefix slope opposite the anchor DMO direction. This is stronger than a one-bar sign change and symmetric under coordinate mirroring. Reversal propensity is evaluated against incidence/proximity of that independent event.

The observer's reversal precedence is compatible with the frozen perturbation semantic addendum and does not alter D01's own classifier.

**Result: PASS**

## 8. Perturbation-Class Expectations

The class contract preserves the frozen distinction:

- magnitude answers how strong;
- class answers what kind;
- `NONE` does not mean detected but unclassified;
- reinforcement, contradiction, and reversal map to distinct future geometry;
- `STRUCTURAL/UNKNOWN` carries no forced directional expectation.

Class frequency is not an acceptance requirement, and inadequate class support yields `INCONCLUSIVE` rather than failure. This avoids conflict between semantic validity and prevalence.

**Result: PASS**

## 9. Half-Life Evaluation

Observation/forward half-life are evaluated as ordering/calibration claims against $T_{valid}$ and adaptive coordinates, not exact equality. Floor and ceiling masses are separated, preventing bounded values from being treated as unconstrained estimates.

The same independent invalidation event supports persistence and half-life analysis without changing meaning: persistence predicts recognizable duration; half-life predicts temporal relevance scale.

**Result: PASS**

## 10. Forward-Interval Evaluation

Forward interval is evaluated against validity duration and compatible path error at emitted coordinates. The `FORWARD_INTERVAL_RANGE_WARNING` remains visible. Compressed range may produce unsupported or inconclusive evidence but cannot trigger range widening during Stage 2.

This is consistent with the frozen elastic-horizon claim and the no-model-change rule.

**Result: PASS**

## 11. Horizons and Timestamp Geometry

Fixed and adaptive horizons are elapsed-time targets resolved by timestamps, not row counts. Requested/actual elapsed time and overshoot are recorded. Gap-crossing outcomes are stratified. Adaptive coordinates are frozen at DMO emission and cannot use later state updates.

The maximum requested coordinate, 1,800 minutes, consistently determines the dependence-preserving bootstrap block length.

**Result: PASS**

## 12. Session, Gap, and Missingness Policy

All sessions and natural gaps remain in one chronological trajectory. Transition strata are mutually exclusive by explicit priority and analysis-only. No reset, interpolation, forward fill, regular-hours restriction, or hidden row deletion is introduced.

Unavailable required input does not fabricate a DMO; elapsed time to the next accepted observation remains real. This is compatible with D01's gap handling.

**Result: PASS**

## 13. Censoring and Reserve Boundary

Per-horizon censoring permits short scores while preventing unavailable long scores. Survival uses right censoring at the primary boundary and interval censoring across observation gaps. Censoring is never failure and horizons are not shortened opportunistically.

The reserve boundary guard executes before value access, so no primary score can cross into reserve.

**Result: PASS**

## 14. Calibration, Support, and Serial Dependence

Continuous effects remain primary; quintiles use predictors only. Floor/ceiling/tied masses are handled explicitly. Support is determined by distinct temporal blocks, and uncertainty uses moving-block resampling whose length derives from the longest pre-registered horizon.

Overlapping anchors remain inside blocks; naive IID errors are prohibited. Optional p-values cannot control classifications and are multiplicity-adjusted if reported.

**Result: PASS**

## 15. Dimension Classification Logic

The four-level classification separates effect direction, interval evidence, support, and interpretability. It permits partial evidence and failure, avoids a cosmetic global PASS, and does not use outcome-selected thresholds.

Categorical perturbation evidence has explicit core contrasts and support behavior. Temporal variables use censor-aware concordance rather than uncensored equality.

**Result: PASS**

## 16. Canonical Replay, Seal, Parallelism, and Determinism

One sequential replay owns mutable D01 state. The immutable seal precedes up to 18 read-only scoring workers. A second independent sequential replay validates semantic fingerprints. No scoring task can mutate or call the canonical D01 instance.

This satisfies Windows process requirements while preserving chronological causality.

**Result: PASS**

## 17. Stage 1 and Reserve Integrity

Frozen D01 source/configuration/schema hashes remain unchanged. Stage 2 v0.2 is not frozen or implemented by this task. Any primary weakness creates evidence, not an in-place correction. Any future model candidate returns through Stage 1; reserve remains sealed.

**Result: PASS**

## 18. Contradiction Review

No contradiction was found among:

- realized-state observer and D01 state semantics;
- persistence and invalidation;
- reversal propensity and realized reversal;
- perturbation-class expectations and class precedence;
- half-life/forward interval and $T_{valid}$;
- timestamp horizons, gaps, and censoring;
- point-in-time replay and future scoring;
- support/multiplicity rules and dimension classifications.

No silent repair or design alteration was required during this review.

## 19. Final Decision

**DESIGN CONSISTENCY: PASS**

**Design status:** V0.2 - READY FOR HUMAN REVIEW

Next action: human review and explicit freeze decision. No Stage 2 implementation or replay is authorized by this document.
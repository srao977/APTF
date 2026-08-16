# D01 Stage 2 Historical State Validity Design v0.1

## 1. Document Status

**Status:** DRAFT V0.1 - READY FOR HUMAN REVIEW  
**Experiment stage:** Stage 2 - Historical State Validity  
**Execution status:** DESIGN ONLY - NOT IMPLEMENTED  
**Frozen model:** D01 v0.2, freeze ID `D01_V0_2_STAGE1_ACCEPTED_20260815T161928Z`

## 2. Relationship to Stage 1

Stage 1 asked whether D01 behaved according to its semantics under controlled synthetic behavior. It completed with 81/81 required assertions, 9/9 cross-scenario assertions, 43/43 ablation assertions, numerical-health PASS, determinism PASS, source-hash PASS, and 27/27 tasks completed.

Stage 2 asks whether those frozen semantic descriptions correspond to subsequently realized behavior in a real evolving system. Stage 2 does not reopen Stage 1 mathematics.

## 3. Stage 1 Frozen Baseline

The sole primary Stage 2 model is the exact baseline in `D01_V0_2_STAGE_1_SYNTHETIC_ACCEPTANCE_FREEZE.json`.

> D01 v0.2 SHALL NOT BE RETRAINED, RETUNED, RECALIBRATED, OR MODIFIED BEFORE OR DURING THE PRIMARY STAGE 2 EVALUATION.

Every future runner must load the freeze manifest, verify every source/configuration/design hash, and abort before historical replay on any mismatch with:

```text
STAGE_1_BASELINE_INTEGRITY_FAILURE
```

Internal online adaptation already defined by frozen v0.2 is model execution, not retraining.

## 4. Stage 2 Purpose

Stage 2 evaluates **state validity**. It estimates which D01 semantic dimensions are empirically supported, partially supported, unsupported, or inconclusive on the primary historical corpus.

Stage 2 is allowed to fail. Failure is evidence and must not trigger in-run correction.

## 5. Scientific Question

> When frozen D01 v0.2 describes the state of a real evolving system, are those state descriptions empirically consistent with subsequently realized system behavior?

## 6. What Stage 2 Is Not

Stage 2 is not a trading backtest, price-direction competition, parameter-fitting exercise, profitability test, or broker simulation. It does not evaluate P&L, Sharpe ratio, drawdown, allocation, sizing, transaction costs, or execution.

Stage 3 predictive/decision/trading validity remains future and unauthorized.

## 7. Historical Dataset

Logical source: `data/market/normalized/SPY_1min_normalized_v0_1.csv`  
SHA256: `73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D`  
Rows: 207,824  
Chronology: ascending `event_timestamp_utc`, duplicate timestamps: 0  
Timezone: assumed America/New_York with DST-aware UTC conversion  
Coverage: regular and extended sessions, from 04:00 through available after-hours observations.

Raw available fields include OHLCV, timestamps, session metadata, source traceability, data validity, and normalized derived fields. Frozen D01 Stage 2 inputs must remain within its provider-neutral contract. The proposed minimal mapping is `close -> price`, `volume -> volume`, timestamp fields, source quality, and availability mask. Exact mapping and treatment of pre-existing derived columns are a **PRE-IMPLEMENTATION DESIGN DECISION REQUIRED**; no new feature engineering is authorized.

## 8. Chronological Data Partition

Calendar-month, half-open boundaries:

```text
Primary Stage 2: [2022-09-30T04:00:00-04:00, 2023-03-30T04:00:00-04:00)
Reserve:         [2023-03-30T04:00:00-04:00, 2023-09-30T04:00:00-04:00)
```

Primary rows: 106,603. Reserve rows: 101,221. There is no overlap and no intentional gap. The source ends at `2023-09-29T19:48:00-04:00`, 8 hours 12 minutes before the nominal reserve boundary; this is dataset-native missing coverage.

Random splitting is prohibited.

## 9. Reserve Data Policy

The reserve is sealed. It may not influence design, implementation, debugging, thresholds, parameters, calibration, rules, visual inspection, statistics, distributions, correlations, D01 outputs, labels, prediction, trading, or P&L.

This design used only permitted reserve metadata: identity, hash, schema, timestamp boundary, and row count. Reserve observation values were not inspected and reserve analytics were not calculated.

## 10. Point-in-Time Causality

For each observation at time $t$, D01 may use only information available at or before $t$. D01 emits state at $t$. Later observations may score that already-emitted state but may not create or alter it.

> FUTURE DATA MAY SCORE A PAST STATE.  
> FUTURE DATA MAY NOT CREATE A PAST STATE.

Future scoring records must reference immutable DMO identity, model time, and state hash.

## 11. D01 Replay Model

Replay is strictly chronological within one SPY trajectory. D01 state persists from one observation to the next. Observations are never shuffled, and chronological updates are never parallelized within the trajectory.

Evaluation labels/evidence are computed after the causal DMO exists and must be kept logically separate from the replay input path.

## 12. Warm-Up Policy

Warm-up observations may initialize causal references, scales, parameters, and state but are not scored. The frozen design does not specify a universal readiness length.

**PRE-IMPLEMENTATION DESIGN DECISION REQUIRED:** define a point-in-time readiness condition using only internal model state/health and elapsed observations, not future outcomes. Candidate requirements include valid finite state, initialized adaptive reference/scale, no invalid health status, and a pre-registered minimum causal observation count. The length must be fixed before execution.

## 13. Historical Observation / Session Policy

Use all available chronological observations; do not silently restrict to 09:30-16:00. Preserve premarket, regular, and after-hours ordering. Session transitions are observable state transitions, not rows to delete.

Overnight gaps, weekends, holidays, missing bars, and irregular intervals remain in chronology. No interpolation, synthetic bars, or forward fill is allowed. D01 receives actual elapsed event time through its timestamp contract. Session-transition indicators may be retained for stratified diagnostics but may not alter frozen model inputs unless already in the frozen contract.

## 14. State-Validity Framework

Each DMO at $t$ is paired later with independently realized evidence over pre-registered horizons. Analyses should emphasize ordering, calibration, survival, and conditional consistency rather than binary pass thresholds chosen from outcomes.

Every dimension reports: empirically supported, partially supported, unsupported, or inconclusive, with uncertainty and sample coverage.

## 15. State / State-Level Validity

Semantic claim: level and kinematics characterize current normalized state and local evolution. Realized evidence may measure whether subsequent normalized observations remain consistent with the emitted local state path before state invalidation. Candidate scores include path deviation, sign-consistent state evolution, and bounded local propagation error.

**PRE-IMPLEMENTATION DESIGN DECISION REQUIRED:** define an independent realized state representation that does not simply reuse D01's adaptive reference and does not reduce validity to next-bar price direction.

## 16. Strength Validity

Claim: stronger states have greater evidence-weighted expression. Evaluate whether higher strength corresponds to more pronounced and stable realized state expression, conditional on uncertainty/coherence and available activity. Do not equate strength with future return magnitude alone.

Candidate scoring: ordered bins and monotonic association with realized state-expression magnitude/stability. Exact binning is to be pre-registered.

## 17. Coherence Validity

Claim: aligned evidence evolves more consistently. Compare high versus low coherence on subsequent state-path consistency and channel agreement persistence. Control for strength, uncertainty, session transitions, and sparse optional channels.

## 18. Persistence Validity

Claim: high persistence means the current inferred state remains recognizable longer. Candidate evidence is survival time until pre-registered state invalidation, not probability that price rises. Evaluate survival ordering and calibration against emitted persistence.

**PRE-IMPLEMENTATION DESIGN DECISION REQUIRED:** define state-recognition and invalidation criteria independently of future-tuned thresholds.

## 19. Uncertainty Validity

Claim: greater uncertainty corresponds to greater subsequent ambiguity, dispersion, instability, or state-estimation error. Evaluate calibration of uncertainty against realized path-error distributions and state-instability incidence. Do not equate uncertainty automatically with volatility.

## 20. Reversal-Propensity Validity

Claim: increasing reversal propensity corresponds to greater incidence or proximity of a realized state reversal. Evaluate time-to-reversal and reversal incidence by propensity bins, using a pre-registered state-relative reversal definition rather than next-bar direction.

## 21. Perturbation-Magnitude Validity

Claim: larger detected perturbations correspond to larger realized state transitions. Evaluate ordered relationships between magnitude and subsequent change in independently measured state/evolution, with session gaps and data quality separated as confounders.

## 22. Perturbation-Class Validity

Classes: `NONE`, `REINFORCING`, `CONTRADICTING`, `REVERSING`, `STRUCTURAL/UNKNOWN` (schema text may render the final class with a slash).

Compare class-conditional realized transition geometry: continuation/support, weakening without established reversal, opposite-direction transition, and ambiguous/data-structural behavior. Class validity requires distinguishable relationships, not equal frequency or trading profitability.

## 23. Observation-Half-Life Validity

Claim: the current observation-derived state remains relevant for a duration related to emitted half-life. Candidate scoring compares realized state-recognition survival with fractions/multiples of emitted half-life and calibration of relevance decay.

The half-life floor/ceiling create censoring and must be reported explicitly.

## 24. Forward-Half-Life / Forward-Interval Validity

Claim: D01's proposed horizon relates to how long the current state description remains useful. Evaluate state-validity survival and path error at fractions of, at, and beyond emitted forward half-life/interval.

Carry forward `FORWARD_INTERVAL_RANGE_WARNING` as a monitored diagnostic. Do not change D01. Stage 2 should determine whether the observed interval range still yields empirical discrimination.

## 25. Validity Matrix

| D01 output | Semantic claim | Realized historical observable | Point-in-time evaluation method | Expected relationship | Failure interpretation |
|---|---|---|---|---|---|
| State/level/kinematics | Characterizes current local state evolution | Independent realized state path and deviation | Freeze DMO at $t$; score later path only | Better local consistency than incompatible state geometry | State representation unsupported or observable definition inadequate |
| Strength | Evidence-weighted expression | Realized state-expression magnitude and stability | Ordered bins/continuous calibration | Stronger states show stronger/stabler expression | Strength semantics unsupported or confounded |
| Coherence | Evidence channels align | Subsequent path/channel consistency | Conditional ordering by coherence | Higher coherence gives more consistent evolution | Coherence lacks historical discrimination |
| Persistence | Current state remains recognizable | Time to state invalidation | Survival/time-to-event from DMO | Higher persistence gives longer survival | Persistence unsupported or invalidation definition inadequate |
| Uncertainty | State is less determinate | Realized error/ambiguity/instability | Error calibration and conditional dispersion | Higher uncertainty gives greater error/ambiguity | Uncertainty miscalibrated or observable mismatch |
| Reversal propensity | Current evolution may reverse | State-relative reversal incidence/time | Time-to-reversal analysis | Higher propensity gives greater/nearer reversals | Reversal channel unsupported |
| Perturbation magnitude | Disturbance strength | Realized transition magnitude | Ordered magnitude-to-transition analysis | Larger magnitude gives larger transitions | Magnitude lacks empirical meaning |
| Perturbation class | Disturbance kind | Class-conditional transition geometry | Compare subsequent geometry by frozen class | Classes are behaviorally distinguishable | Type inference unsupported historically |
| Observation half-life | Observation state relevance duration | State-recognition survival | Score at adaptive half-life fractions/multiples | Survival relates monotonically to half-life | Half-life validity unsupported/censored |
| Forward half-life/interval | Proposed state-validity horizon | Duration/path error of useful state description | Score before/at/after emitted horizon | Longer horizons correspond to longer validity | Horizon lacks discrimination; monitor warning |

## 26. Evaluation Horizons

Use both fixed diagnostic horizons and D01-derived adaptive horizons. Fixed horizons support comparability; adaptive horizons test D01's temporal claims. Candidate adaptive coordinates are fractions, one unit, and multiples of emitted half-life/forward interval.

**PRE-IMPLEMENTATION DESIGN DECISION REQUIRED:** pre-register exact fixed horizons and adaptive fractions/multiples before replay, based on semantic resolution and data cadence, not observed performance.

## 27. Scoring Principles

- Preserve continuous outputs; avoid unnecessary thresholding.
- Prefer calibration curves, monotonic ordering, survival analysis, and effect estimates with uncertainty.
- Report sample counts, censoring, missingness, session strata, and dependence.
- Account for overlapping horizons and serial dependence in uncertainty estimates.
- Pre-register binning, invalidation rules, and multiplicity handling.
- No threshold may be selected because it makes historical results pass.

## 28. Numerical Health

The eventual runner must enforce finite states, bounds, model health, chronological timestamps, and source/config hashes. Numerical failures are reported separately from semantic validity. Gaps and clipping are retained as diagnostics.

## 29. Determinism

Identical frozen source, configuration, dataset partition, and initial state must reproduce identical DMO/FMO fingerprints and score inputs. Deterministic verification must use an independent rerun and exclude PID/wall-clock metadata.

## 30. Parallel Execution Design

Future implementation should support `ProcessPoolExecutor(max_workers=18)` for independent evaluation dimensions, pre-registered diagnostics, and deterministic reruns. It must record real PID, parent PID, start/end, elapsed, status, unique workers, and peak concurrency.

Never parallelize chronological observations inside the single SPY D01 replay. A safe design is one canonical sequential replay producing immutable causal outputs, followed by parallel read-only scoring tasks.

## 31. Stage 2 Failure Policy

**STAGE 2 IS ALLOWED TO FAIL.**

Unsupported or inconclusive dimensions remain results. Do not modify D01, thresholds, or acceptance rules during the primary run. A failure does not retroactively invalidate the Stage 1 synthetic freeze; it limits historical claims.

## 32. Stage 2 Acceptance Philosophy

Do not require every variable to pass and do not manufacture a global PASS. Each dimension receives one of:

```text
EMPIRICALLY_SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
INCONCLUSIVE
```

The experiment should state what D01 actually knows. Overall conclusions summarize the dimension-level evidence and methodological integrity.

## 33. Reserve Unseal Policy

After the primary six-month Stage 2 run: STOP, REVIEW, DECIDE. Reserve does not run automatically.

Unsealing requires explicit future authorization after methodology is frozen, primary execution is complete, results are reviewed, and no acceptance-rule changes are pending. Reserve is confirmation evidence, not a second development dataset.

If primary results motivate model/method changes, reserve remains sealed. Any model change becomes a new candidate version and must return through Stage 1 before historical evaluation.

## 34. Relationship to Stage 3

Stage 2 may identify semantically valid state information that a future Stage 3 could evaluate for forecasting or decisions. Stage 2 does not design or test buy/sell rules, allocation, sizing, execution, costs, or profitability.

## 35. Future Output Artifacts

Proposed future root:

```text
output/d01_stage2_historical_state_validity/
  reports/
  metrics/
  diagnostics/
  traces/
  workers/
  manifests/
  logs/
```

The eventual manifest must record Stage 1 freeze ID/source hashes, Stage 2 design hash, dataset hash, primary/reserve boundaries, `reserve_accessed=false`, point-in-time validation, `model_source_changed=false`, `parameters_tuned=false`, worker evidence, and determinism evidence.

## 36. Hard Prohibitions

No retraining, retuning, recalibration, model modification, reserve access, random split, future leakage, interpolation, hidden session filtering, trading backtest, P&L, D02, D04, or broker logic is authorized.

No Stage 2 runner or launcher is created by this design task. Substantive future execution must be user-owned from external PowerShell after implementation authorization.

## 37. Pre-Implementation Open Decisions

The following must be settled and pre-registered before implementation:

1. Exact frozen-input mapping from normalized OHLCV to D01's `price`, `volume`, quality, and availability fields.
2. Causal warm-up/readiness condition and minimum observation count.
3. Independent realized-state representation and state-invalidation definition.
4. Fixed diagnostic horizons and adaptive half-life/interval fractions/multiples.
5. Binning/calibration methods, minimum support, and uncertainty estimation under serial dependence.
6. Session-transition and gap stratification policy without deleting chronology.
7. Censoring policy near Stage 2 end; no score may cross into sealed reserve.
8. Multiplicity/reporting policy across dimensions.
9. Stage 2 design freeze hash and formal primary-run acceptance/reporting protocol.

These decisions must not use reserve values and must not be selected to improve historical outcomes.
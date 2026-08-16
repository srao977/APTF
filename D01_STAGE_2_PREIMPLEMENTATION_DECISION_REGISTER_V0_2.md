# D01 Stage 2 Pre-Implementation Decision Register v0.2

## Document Status

**Status:** DESIGN V0.2 - READY FOR HUMAN REVIEW  
**Input design:** `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_1.md`  
**Frozen model:** D01 v0.2, freeze ID `D01_V0_2_STAGE1_ACCEPTED_20260815T161928Z`  
**Data use:** schema, timestamp metadata, frozen interfaces, design authority, and Stage 1 synthetic evidence only. No primary outcomes or reserve observation values were inspected.

## Decision 01 - Exact Frozen Input Mapping

**Question:** Which normalized historical fields enter the frozen D01 provider-neutral observation contract?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** D01 v0.2 Sections 5, 6, 32, and 34; frozen `NormalizedObservation`; Stage 1 freeze; normalized dataset schema.

**Decision:** Use only raw causal fields required by the frozen interface:

- constant `entity_id="SPY"`;
- `event_timestamp_utc` converted to UTC epoch seconds for `event_time`;
- `receive_time=event_time`, explicitly marked as a historical replay availability proxy because receipt timestamps are absent;
- contiguous one-based replay ordinal after canonical UTC sorting for `sequence_id`;
- `close -> price` without transformation;
- raw `volume -> volume` without transformation;
- `session_type -> session`;
- `source_quality=1.0` when `data_valid=true`, otherwise no observation is admitted because required numeric price/volume cannot be fabricated;
- availability mask: price/volume true when parseable; bid/ask/bid_size/ask_size false;
- optional quote fields are `None`.

All return/range/change columns, OHLC fields other than close, minute-of-session, and quality flags are excluded from D01 input. They may remain trace metadata. Future scoring uses raw close only.

**Rationale:** This is the minimum deterministic mapping consistent with the frozen interface and introduces no engineered predictor.

**Alternatives rejected:** OHLC averages, returns, indicators, derived volatility, inferred bid/ask, graded source quality from outcome behavior, and provider-native objects.

**Leakage risk:** Derived columns could accidentally carry evaluation features into replay; excluding them closes that path. `receive_time=event_time` must never be represented as measured latency.

**Implementation consequence:** The adapter must persist the exact mapping and hash, reject unavailable required inputs without filling them, and preserve elapsed time to the next accepted observation.

**Remaining human decision:** None.

## Decision 02 - Causal Warm-Up and Readiness

**Question:** When may emitted DMOs enter Stage 2 scoring?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** frozen state initialization, kinematics definitions, health contract, and update sequence.

**Decision:** Model execution starts at the first admissible primary observation. Scoring starts with the third accepted observation, provided the current DMO is finite, required price/volume availability is true, adaptive reference and scale are finite with scale above its configured floor, and `model_health != INVALID`.

Three observations are required because one initializes level/reference, two establish a first velocity interval, and three establish two velocity intervals and therefore acceleration/curvature. No longer history is required by the frozen implementation.

Readiness is evaluated causally per DMO. A temporary missing required input yields no DMO and no score; D01 is not reset. `DEGRADED_DATA`, `DEGRADED_NUMERICAL`, or `PERTURBED` remain scoreable with diagnostic strata if values are finite. `INVALID` is a primary replay integrity failure, not a tunable exclusion.

**Rationale:** The minimum count is derived from the highest frozen primitive derivative order, not historical performance.

**Alternatives rejected:** arbitrary 30/60/390-bar warm-ups, performance-based stabilization, session resets, and future-aware readiness.

**Leakage risk:** Choosing warm-up from outcome quality would tune the experiment. The fixed three-observation rule prevents this.

**Implementation consequence:** Warm-up DMOs are persisted but flagged `score_eligible=false`; no restart occurs when eligibility changes.

**Remaining human decision:** None.

## Decision 03 - Independent Realized-State Observer and Invalidation

**Question:** What independent future observable scores a DMO without circularity or reducing Stage 2 to next-bar direction?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** D01 state/kinematic semantics, no-primary-direction rule, FMO local geometry, persistence/reversal/half-life semantics, and perturbation addendum.

**Decision:** Define a transparent raw-close geometric observer. For anchor time $t$ and later raw close $C(t+u)$:

$$
y_t(u)=\log\left(\frac{C(t+u)}{C(t)}\right),\qquad x(u)=u\text{ in elapsed minutes}.
$$

For each horizon, compute endpoint displacement $y_t(h)$; through-origin least-squares slope $b_t(h)=\sum x_jy_j/\sum x_j^2$; quadratic through-origin curvature coefficient when at least two future points exist; path length $A_t(h)=\sum_j|y_j-y_{j-1}|$; efficiency $E_t(h)=|y_t(h)|/A_t(h)$ with $E=0$ when $A=0$; and normalized path deviation from the fitted line.

The DMO directional claim is $d_t=\operatorname{sign}(V_t)$, falling back to $\operatorname{sign}(A_t)$ and then $\operatorname{sign}(L_t)$ only when the preceding quantity is exactly zero. If all are zero, directional classifications and survival are `AMBIGUOUS/INCONCLUSIVE`, while non-directional magnitude/error observables remain available.

Classify a horizon:

- `CONTINUATION` when $d_t y_t(h)>0$ and $d_tb_t(h)>0$;
- `WEAKENING` when $d_t y_t(h)\ge0$ and $d_tb_t(h)\le0$;
- `REVERSAL` when $d_t y_t(h)<0$ and $d_tb_t(h)<0$;
- `AMBIGUOUS/INCONCLUSIVE` otherwise or when $d_t=0$.

Define $T_{valid}(t)$ as elapsed time to the first future observation whose prefix geometry is `REVERSAL`. No magnitude threshold is fitted. If reversal occurs across an observation gap, invalidation is interval-censored between the last compatible and first reversing observation. If no reversal is observed before the scoring boundary, the duration is right-censored.

**Rationale:** The observer is deterministic, model-independent, scale-free under log displacement, transparent, and useful for continuous geometry before classification.

**Alternatives rejected:** future D01 outputs as labels, next-bar direction, fitted hidden-state models, profit labels, volatility thresholds, ATR-scaled barriers, and data-selected tolerances.

**Leakage risk:** The observer uses future closes only after the anchor DMO is immutable. Observer values must never enter replay.

**Implementation consequence:** Replay and scoring are physically/logically separated. Every score references anchor trace/state hash and future raw-source row IDs.

**Remaining human decision:** None.

## Decision 04 - Evaluation Horizons

**Question:** Which fixed and adaptive temporal coordinates are pre-registered?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** 1-minute schema, D01 temporal geometry, half-life bounds, forward interval bounds, and fixed evaluation projections in the frozen design.

**Decision:** Fixed diagnostic horizons are 1, 5, 15, 30, and 60 elapsed minutes. Adaptive coordinates are 0.5x, 1.0x, and 2.0x each emitted observation half-life, forward half-life, and forward interval.

Lookup is timestamp-based. The first observation at or after the target coordinate supplies the endpoint; requested and actual elapsed time and overshoot are recorded. Targets traversing gaps are stratified and not represented as exact one-minute sampling. Targets crossing the primary boundary are censored.

**Rationale:** Fixed horizons are interpretable evaluation projections explicitly compatible with frozen design; adaptive coordinates test D01's own temporal claims. The maximum possible coordinate is 1,800 minutes from 2x the frozen 900-minute half-life cap.

**Alternatives rejected:** observation-count horizons, outcome-selected horizons, and adaptive-coordinate clipping for convenience.

**Leakage risk:** Adding/removing horizons after results would create selection bias. The set is fixed before implementation.

**Implementation consequence:** A common horizon resolver records target, actual endpoint, gap stratum, and censor status independently for every coordinate.

**Remaining human decision:** None.

## Decision 05 - Calibration, Support, and Serial Dependence

**Question:** How are continuous evidence, bins, support, and uncertainty handled without IID assumptions?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** continuous bounded DMO outputs, maximum pre-registered horizon, and Stage 2 calibration philosophy.

**Decision:** Continuous rank/calibration/survival effects are primary. Predictor-only empirical quintiles are secondary visualization/ordering summaries; boundaries are computed from the relevant primary-period D01 predictor without looking at outcomes. Tied/floor/ceiling masses are reported as separate groups, with interior values split into at most five quantiles. Categorical outputs use their native classes.

Dependence-preserving uncertainty uses a chronological moving-block bootstrap with 1,800 elapsed-minute blocks, derived from the maximum 2x temporal coordinate. Use 2,000 deterministic replicates and two-sided 95% percentile intervals. The random seed is derived from SHA256 of the Stage 2 design-freeze identity, not selected from results. Overlapping horizons remain within resampled blocks; naive IID errors are prohibited.

Support is measured in distinct populated 1,800-minute blocks:

- `ADEQUATE`: at least 30 blocks;
- `LIMITED`: 10-29 blocks;
- `INSUFFICIENT`: fewer than 10 blocks.

Each displayed class/bin/contrast must meet its own block support. Thirty is the conventional cluster count for asymptotic stability; ten is the minimum at which bootstrap reporting is retained as explicitly limited. These are reporting rules, not discovered properties.

**Rationale:** The policy preserves continuous evidence, handles serial dependence, and derives block length from design-time temporal exposure.

**Alternatives rejected:** IID standard errors, outcome-optimized bins, fixed-value bins without semantic authority, per-bar random bootstrap, and class failure based only on rarity.

**Leakage risk:** Quantiles may use predictor values but never outcomes. All methods and support labels are frozen before execution.

**Implementation consequence:** Scoring tasks produce point estimates and block-level sufficient records; one deterministic bootstrap engine produces intervals.

**Remaining human decision:** None.

## Decision 06 - Session and Gap Stratification

**Question:** How are session transitions and natural gaps retained and analyzed?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** all-session dataset metadata, no-fill policy, timestamp/session fields, and D01 elapsed-time handling.

**Decision:** Preserve one uninterrupted chronological D01 trajectory. Assign each transition exactly one analysis-only stratum in this priority:

1. `WEEKEND_OR_HOLIDAY_GAP`: local calendar-date difference at least two days;
2. `OVERNIGHT_GAP`: local date advances exactly one day;
3. `SESSION_TRANSITION`: same local date and `session_type` changes;
4. `DATA_GAP/IRREGULAR_INTERVAL`: same date/session and elapsed time exceeds 60 seconds;
5. `INTRASESSION_CONTINUOUS`: same date/session and elapsed time is in `(0,60]` seconds;
6. `START`: first observation.

UTC determines ordering/elapsed time; America/New_York local date/session metadata determines labels. Strata do not alter D01 input or delete observations.

**Rationale:** Priority is deterministic, mutually exclusive, and preserves actual system observation gaps.

**Alternatives rejected:** regular-hours filtering, session resets, interpolation, deleting gaps, and using outcome volatility to classify transitions.

**Leakage risk:** None when labels derive only from timestamps/session metadata.

**Implementation consequence:** Every anchor and horizon endpoint carries transition strata; aggregate and stratified evidence are both reported.

**Remaining human decision:** None.

## Decision 07 - Right and Interval Censoring

**Question:** How are unavailable future observations handled without reserve access?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** half-open partition boundary, adaptive horizons, survival requirements, and sealed-reserve policy.

**Decision:** No lookup may read timestamp `>= 2023-03-30T04:00:00-04:00`. Each horizon is independently right-censored if its target or first eligible endpoint reaches/crosses that boundary. Shorter available horizons remain scoreable. Survival without observed invalidation before boundary is right-censored at the last primary observation.

When a reversal/invalidation is first observed after a data/session gap, its event time is interval-censored in `(last compatible timestamp, first reversing timestamp]`. It is not assigned to an invented intermediate minute. Missing required input creates an observation gap; it is not a failure label.

**Rationale:** This preserves all available evidence, never shortens horizons opportunistically, and cannot touch reserve.

**Alternatives rejected:** dropping anchors wholesale, treating censoring as failure, truncating target horizons silently, or reading reserve endpoints.

**Leakage risk:** A strict boundary guard must execute before any row-value load for scoring.

**Implementation consequence:** Every score includes censor type/bounds; estimators must support right/interval censoring or mark the relevant analysis inconclusive.

**Remaining human decision:** None.

## Decision 08 - Multiplicity and Reporting

**Question:** How are ten dimensions and many horizons reported without significance mining?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** Stage 2 dimension-level philosophy and prohibition on global pass manufacturing.

**Decision:** Each dimension has one pre-registered primary effect/contrast and secondary horizon diagnostics. Primary evidence reports direction, magnitude, 95% block-bootstrap interval, support, calibration/monotonicity, and horizon consistency. P-values are not required and do not determine classification. If supplied as supplemental diagnostics, apply Benjamini-Hochberg FDR at `q=0.05` across the ten dimension-level primary tests as one family.

Dimension classification:

- `EMPIRICALLY_SUPPORTED`: adequate support; primary estimate has expected direction and its 95% interval excludes the null in that direction; no pre-registered primary contradiction.
- `PARTIALLY_SUPPORTED`: point estimate has expected direction but interval includes null, support is limited, or pre-registered subclaims are mixed without an opposite decisive primary result.
- `UNSUPPORTED`: adequate support and the 95% interval excludes null in the opposite direction, or a categorical primary contrast is decisively opposite.
- `INCONCLUSIVE`: insufficient support, invalid/censored observable, or interval/data quality prevents interpretation.

No global Stage 2 pass is computed from counts or p-values.

**Rationale:** Classification is deterministic yet permits failure and uncertainty.

**Alternatives rejected:** unadjusted p-value counting, post hoc primary-horizon selection, global majority PASS, and threshold tuning.

**Leakage risk:** Primary effect and expected direction must be frozen with Design v0.2 before execution.

**Implementation consequence:** Reports distinguish primary contracts from secondary diagnostics and record all pre-registered outcomes.

**Remaining human decision:** None.

## Decision 09 - Design Freeze and Primary Run Protocol

**Question:** How is Design v0.2 frozen and executed later?

**v0.1 status:** PRE-IMPLEMENTATION DESIGN DECISION REQUIRED.

**Authority consulted:** Stage 1 freeze contract, dataset partition manifest, reserve hard stop, determinism, and parallelism requirements.

**Decision:** This task does not freeze v0.2. After human approval, a separate task creates `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2_FREEZE.json` containing design SHA256, Stage 1 freeze ID/protected hashes, dataset SHA256, primary/reserve boundaries, evidence-contract hashes, realized-observer hash, and scoring-specification hash.

Future lifecycle:

1. Preflight verifies all freezes, boundaries, and reserve seal.
2. One canonical sequential primary-only replay produces immutable DMO/FMO records.
3. Replay output is hashed and sealed.
4. Up to 18 workers perform independent read-only scoring.
5. An independent sequential replay verifies deterministic semantic fingerprints.
6. Reports assign dimension-level evidence classifications.
7. Hard stop occurs before reserve access.

Any integrity failure aborts. Any primary semantic weakness is recorded; D01 v0.2 is not modified. A new candidate must return through Stage 1, and reserve remains sealed.

**Rationale:** The lifecycle separates causal state creation from future scoring and preserves an auditable baseline.

**Alternatives rejected:** scoring during replay, parallel state updates, automatic reserve run, in-place model correction, and freezing before human review.

**Leakage risk:** Replay/scoring separation and immutable seal prevent labels from feeding state creation.

**Implementation consequence:** A future runner/launcher task must implement phase gates, manifests, worker evidence, deterministic rerun, and user-owned execution.

**Remaining human decision:** Approval to freeze Design v0.2. The scientific decision itself is resolved; formal freeze authorization is intentionally pending human review.

## Resolution Summary

| Decision | Status |
|---|---|
| 01 Input mapping | RESOLVED |
| 02 Warm-up/readiness | RESOLVED |
| 03 Independent realized state | RESOLVED |
| 04 Evaluation horizons | RESOLVED |
| 05 Calibration/support/serial dependence | RESOLVED |
| 06 Session/gap stratification | RESOLVED |
| 07 Censoring | RESOLVED |
| 08 Multiplicity/reporting | RESOLVED |
| 09 Design freeze/primary protocol | RESOLVED; human approval to freeze remains pending |

# D01 Stage 2 Historical State Validity Design v0.2

## 1. Document Status

**Status:** DESIGN V0.2 - READY FOR HUMAN REVIEW  
**Experiment:** D01 v0.2 Stage 2 Historical State Validity  
**Implementation:** NOT STARTED  
**Historical replay:** NOT STARTED  
**Reserve:** SEALED  
**Stage 1 freeze:** `D01_V0_2_STAGE1_ACCEPTED_20260815T161928Z`

This document supersedes Stage 2 Design v0.1 as the proposed implementation authority only after human approval and a separate formal design-freeze task. It does not modify D01 v0.2 or the Stage 1 freeze.

## 2. Relationship to Stage 1

Stage 1 established synthetic semantic validity: 81/81 required assertions, 9/9 cross-scenario assertions, 43/43 ablation assertions, numerical health PASS, determinism PASS, source integrity PASS, and 27/27 tasks complete.

Stage 2 evaluates whether those frozen semantic outputs correspond to subsequently realized behavior in a real evolving system. The carried `FORWARD_INTERVAL_RANGE_WARNING` remains a monitored historical diagnostic, not an authorization to alter D01.

## 3. Frozen Baseline and Integrity Gate

The exact model/configuration/schema/design authority is recorded in `D01_V0_2_STAGE_1_SYNTHETIC_ACCEPTANCE_FREEZE.json`.

> D01 v0.2 SHALL NOT BE RETRAINED, RETUNED, RECALIBRATED, OR MODIFIED BEFORE OR DURING THE PRIMARY STAGE 2 EVALUATION.

Every future run loads and verifies all protected hashes before historical replay. Any mismatch aborts with:

```text
STAGE_1_BASELINE_INTEGRITY_FAILURE
```

Frozen internal online adaptation is model execution, not retraining.

## 4. Scientific Question

> When frozen D01 v0.2 describes the state of a real evolving system, are those state descriptions empirically consistent with subsequently realized system behavior?

Stage 2 tests state validity, not profitability, trade generation, or conventional next-bar prediction.

## 5. Historical Corpus and Partition

Dataset: `data/market/normalized/SPY_1min_normalized_v0_1.csv`  
SHA256: `73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D`

```text
Primary: [2022-09-30T04:00:00-04:00, 2023-03-30T04:00:00-04:00)
Reserve: [2023-03-30T04:00:00-04:00, 2023-09-30T04:00:00-04:00)
```

Primary observations: 106,603. Reserve observations: 101,221. Split is chronological, half-open, non-overlapping, and has no intentional gap. Reserve values remain sealed.

## 6. Frozen Historical Input Mapping

The replay adapter uses the minimum raw causal input required by frozen D01.

| Historical field | D01 input | Transformation | Causal? | Frozen-contract authority | Status | Reason |
|---|---|---|---|---|---|---|
| constant `SPY` | `entity_id` | literal string | Yes | entity-local topology/observation contract | INCLUDED | One frozen D01 trajectory |
| `event_timestamp_utc` | `event_time` | UTC epoch seconds | Yes | causal timestamp contract | INCLUDED | Canonical ordering and elapsed time |
| `event_timestamp_utc` | `receive_time` | same epoch seconds; historical availability proxy | Yes | receive-time field exists; source lacks receipt timestamp | INCLUDED | Deterministic replay proxy, not latency evidence |
| canonical sorted row ordinal | `sequence_id` | contiguous one-based integer | Yes | monotonic sequence contract | INCLUDED | Deterministic causal ordering |
| `close` | `price` | numeric identity | Yes | required price input | INCLUDED | Minimum raw price observation |
| `volume` | `volume` | numeric identity | Yes | required volume input | INCLUDED | Frozen volume mechanism |
| `session_type` | `session` | identity label | Yes | optional session field | INCLUDED | Traceability; current frozen math does not consume direction from it |
| `data_valid` | `source_quality` | `true -> 1.0`; invalid required row not admitted | Yes | source-quality and no-fabrication contract | INCLUDED | Avoid invented graded quality |
| parseability metadata | `availability_mask.price/volume` | true iff required value available | Yes | availability-mask contract | INCLUDED | Missing is not zero |
| absent quote fields | bid/ask/sizes and mask | `None`; availability false | Yes | optional quote contract | INCLUDED AS MISSING | No fabrication |
| `open`, `high`, `low` | none | none | Yes | not required by frozen minimum interface | EXCLUDED | Avoid expanding frozen input |
| returns/ranges/change columns | none | none | Some causal, but not required | no frozen requirement | EXCLUDED | No engineered predictor input |
| minute/source/quality text fields | trace metadata only | none | Yes | traceability only | EXCLUDED FROM D01 | Audit context, not model input |

If required close or volume is unavailable, no D01 observation is fabricated. The row is recorded as unavailable and the next accepted event preserves actual elapsed time. No interpolation or forward fill is permitted.

## 7. Point-in-Time Causality

At time $t$, D01 receives only fields available at or before $t$ and emits an immutable DMO/FMO. Future observations may score that state only after emission.

> FUTURE DATA MAY SCORE A PAST STATE.  
> FUTURE DATA MAY NOT CREATE A PAST STATE.

Replay inputs and scoring observables must be separate data products and code paths.

## 8. Causal Warm-Up and Readiness

Execution starts at the first admissible primary observation. The first two accepted DMOs are warm-up and are never scored. Scoring may begin at accepted observation three because three points establish level/reference, one velocity history, and acceleration/curvature history.

Per-DMO eligibility requires:

- accepted sequence at least three;
- finite DMO numeric fields;
- finite adaptive reference and scale above configured floor;
- price and volume availability true;
- `model_health != INVALID`.

Other health labels remain scoreable but stratified. Missing required input yields no DMO/score and does not reset state. `INVALID` is a replay-integrity failure. No session reset is allowed.

## 9. Canonical Replay Architecture

Run exactly one primary-only SPY trajectory in strict UTC order. D01 mutable state persists across all sessions and gaps. No chronological observation is parallelized or shuffled.

The canonical replay stores immutable DMO/FMO records with source row ID, model time, config hash, state hash, trace ID, score eligibility, and transition stratum. Future labels are absent from this phase.

## 10. Independent Realized-State Observer

The measuring instrument uses only subsequent raw close observations and anchor close. It uses no D01 state, parameter, adaptive reference, or later D01 output to construct realized geometry.

For anchor $t$, later elapsed time $u$ in minutes, and raw close $C$:

$$
y_t(u)=\log\left(\frac{C(t+u)}{C(t)}\right),\qquad x(u)=u.
$$

At each horizon compute:

1. endpoint displacement $y_t(h)$;
2. through-origin slope
$$b_t(h)=\frac{\sum_jx_jy_j}{\sum_jx_j^2};$$
3. through-origin quadratic coefficients $y=bx+\frac12ax^2$ when at least two future points exist;
4. path length $A_t(h)=\sum_j|y_j-y_{j-1}|$;
5. path efficiency $E_t(h)=|y_t(h)|/A_t(h)$, defined as zero if $A=0$;
6. RMS line-path deviation normalized by path length, defined as zero for a zero-length path;
7. maximum and terminal signed progress relative to the DMO claim.

Continuous geometry is primary. Discrete labels are derived secondarily.

## 11. State Compatibility and Invalidation

The DMO's state-direction claim is:

$$
d_t=\operatorname{sign}(V_t),
$$

falling back in order to $\operatorname{sign}(A_t)$ and $\operatorname{sign}(L_t)$ only if the preceding value is exactly zero. If all are zero, directional scoring and survival are inconclusive; non-directional realized geometry remains available.

At horizon $h$:

- `CONTINUATION`: $d_ty_t(h)>0$ and $d_tb_t(h)>0$;
- `WEAKENING`: $d_ty_t(h)\ge0$ and $d_tb_t(h)\le0$;
- `REVERSAL`: $d_ty_t(h)<0$ and $d_tb_t(h)<0$;
- `AMBIGUOUS/INCONCLUSIVE`: all other cases or $d_t=0$.

State validity duration $T_{valid}(t)$ is elapsed time to the first future observation whose prefix geometry becomes `REVERSAL`. This zero-crossing/sign rule is dimensionless and fixed by geometry; no historically selected barrier is used.

If reversal appears across a gap, invalidation time is interval-censored in `(last compatible, first reversing]`. If no invalidation appears before the available scoring boundary, it is right-censored.

## 12. Sign/Mirror Invariance

**Invariant:** multiplying every directional quantity in an anchor/future geometry by `-1` must leave efficiency, path deviation, compatibility category, $T_{valid}$, and semantic evidence classification unchanged except for coordinate signs.

This must become a mandatory implementation test for continuation, weakening, reversal, perturbation-class geometry, and invalidation.

## 13. Fixed Diagnostic Horizons

Pre-registered fixed elapsed-time horizons:

```text
1, 5, 15, 30, 60 minutes
```

They are evaluation projections, not D01 ontology. Lookup uses timestamps, never row counts. The first observation at or after target is used, with requested/actual elapsed time and overshoot recorded. Gap-crossing results carry their transition stratum.

## 14. Adaptive Temporal Horizons

Evaluate `0.5x`, `1.0x`, and `2.0x` each emitted:

- observation half-life;
- forward half-life;
- forward interval.

Coordinates are frozen at DMO emission. They are not updated by later D01 states. No opportunistic clipping is permitted; unavailable coordinates are censored. The maximum possible requested coordinate is 1,800 minutes.

## 15. Session and Gap Stratification

All observations remain in one trajectory. Classify each transition, in priority order:

1. `WEEKEND_OR_HOLIDAY_GAP`: local date difference at least two days;
2. `OVERNIGHT_GAP`: local date advances exactly one day;
3. `SESSION_TRANSITION`: same date, session label changes;
4. `DATA_GAP/IRREGULAR_INTERVAL`: same date/session, elapsed time greater than 60 seconds;
5. `INTRASESSION_CONTINUOUS`: same date/session, elapsed time in `(0,60]` seconds;
6. `START`: first observation.

UTC controls ordering; America/New_York controls local date/session labels. Strata affect analysis only, never frozen D01 input or state.

## 16. Right-Censoring Policy

No scorer may load an observation at or after reserve start `2023-03-30T04:00:00-04:00`.

- Censor each requested horizon independently if target/endpoint reaches the boundary.
- Preserve shorter available horizons.
- Right-censor survival at the last primary observation when no invalidation is observed.
- Interval-censor invalidation across gaps.
- Never treat censoring as semantic failure.
- Never shorten a requested horizon to manufacture a score.

The boundary guard executes before value access.

## 17. Calibration and Ordered Evidence

Continuous effects are primary: rank association, concordance/survival ordering, class contrasts, calibration curves, path errors, and monotonicity.

Secondary ordered summaries use predictor-only empirical quintiles. Outcomes never define bin edges. For half-life and other concentrated bounded variables, exact floor/ceiling masses are separate; interior values use up to five quantiles. If ties prevent five distinct groups, use fewer and report the reduction. Perturbation class uses native categories.

## 18. Minimum Support Policy

Support is the number of distinct populated 1,800-minute chronological blocks contributing to an estimate/class/bin:

```text
ADEQUATE:     >= 30 blocks
LIMITED:      10-29 blocks
INSUFFICIENT: < 10 blocks
```

Insufficient support forces `INCONCLUSIVE`; rarity alone is not failure. Limited support cannot yield `EMPIRICALLY_SUPPORTED`, but may yield `PARTIALLY_SUPPORTED`.

## 19. Serial-Dependence / Uncertainty Policy

Naive IID standard errors are prohibited. Use a chronological moving-block bootstrap with 1,800 elapsed-minute blocks, derived from the maximum requested adaptive horizon. Preserve all overlapping anchors/horizons inside blocks.

Use 2,000 deterministic replicates and two-sided 95% percentile intervals. Derive the seed from SHA256 of the eventual Stage 2 design-freeze identity. Report block count, replicate failures, interval type, and overlap policy.

## 20. Multiplicity Policy

Each semantic dimension has one primary pre-registered effect/contrast; horizon and stratum results are secondary diagnostics. Report effect direction/magnitude, 95% block interval, support, calibration, monotonicity, and horizon consistency.

P-values are optional and do not define classifications. If produced, apply Benjamini-Hochberg FDR at `q=0.05` across the ten primary dimension tests as one family. Unadjusted significance claims are prohibited.

## 21. Stage 2 Classification Rules

- `EMPIRICALLY_SUPPORTED`: adequate support; expected primary direction; 95% interval excludes null in that direction; no pre-registered primary contradiction.
- `PARTIALLY_SUPPORTED`: expected point direction with interval including null, limited support, or mixed subclaims without decisive opposite evidence.
- `UNSUPPORTED`: adequate support and interval excludes null opposite the expected direction, or a categorical primary contrast is decisively opposite.
- `INCONCLUSIVE`: insufficient support, invalid/censored observable, or inability to interpret the evidence.

No global PASS is generated from dimension counts or p-values. Stage 2 is allowed to fail.

## 22. Dimension-Level Evidence Contracts

| Dimension | Semantic claim | Independent observable | Primary score | Secondary diagnostics | Horizons | Expected relationship | Minimum support/censoring | Confounder strata | Classification application |
|---|---|---|---|---|---|---|---|---|---|
| State / kinematics | DMO describes local state evolution | Raw-close displacement, slope, curvature, efficiency, deviation | Sign/geometry concordance of DMO direction and realized slope/progress | Component-wise V/A/K mirror concordance and path error | All fixed; FMO coordinates | Positive concordance and compatible geometry | General block policy; per-horizon censoring | All transition strata | Standard four-level rule; zero-direction anchors inconclusive for direction |
| Strength | Stronger state has stronger realized expression | $|b|\times E$ and compatible-progress magnitude | Spearman association strength vs expression | Quintile ordering, stability by horizon | 5/15/30/60 and adaptive interval | Positive | General policy | Session/gap, uncertainty/coherence strata | Standard rule |
| Coherence | Aligned evidence yields consistent evolution | Path efficiency and inverse normalized deviation | Spearman coherence vs efficiency | Deviation ordering and continuation incidence | 5/15/30/60 | Positive efficiency; negative deviation | General policy | Session/gap, availability | Standard rule |
| Persistence | State remains recognizable longer | $T_{valid}$ | Censor-aware concordance between persistence and survival | Survival curves by predictor quintile | Full survival plus fixed/adaptive cuts | Higher persistence -> longer validity | Right/interval censoring mandatory | Session/gap, perturbation class | Standard rule using concordance null 0.5 |
| Uncertainty | Higher uncertainty means more ambiguity/error | $1-E$, normalized deviation, ambiguous incidence | Spearman uncertainty vs realized ambiguity index | Error calibration and instability incidence | 5/15/30/60 and adaptive | Positive | General policy | Session/gap, coherence | Standard rule |
| Reversal propensity | Higher propensity means nearer/more reversal | Reversal event and time-to-reversal | Censor-aware concordance with shorter reversal time | Horizon reversal incidence by quintile | Fixed plus forward interval | Higher propensity -> greater/nearer reversal | General survival support | Session/gap, perturbation class | Standard rule with direction adjusted for shorter time |
| Perturbation magnitude | Larger disturbance means larger transition | Maximum absolute raw-close displacement and slope change | Spearman magnitude vs realized transition magnitude | Horizon ordering and gap-separated results | 1/5/15/30/60 | Positive | General policy | Session/gap, class | Standard rule |
| Perturbation class | Class describes disturbance kind | Continuation/weakening/reversal/ambiguity geometry | Pre-registered class contrasts below | Class frequencies and transition matrix | 5/15/30 and forward interval | Distinguishable expected geometry | Per-class block support; rare -> inconclusive | Session/gap, magnitude | Categorical contract rule below |
| Observation half-life | Larger half-life means longer state relevance | $T_{valid}$ | Censor-aware concordance half-life vs survival | Validity at 0.5x/1x/2x; floor/ceiling strata | Adaptive observation HL | Positive ordering, not equality | Separate floor/ceiling; censoring | Session/gap, class | Standard rule |
| Forward half-life | Longer forward relevance means longer useful state | $T_{valid}$ and compatible path error | Concordance forward HL vs survival | Error at 0.5x/1x/2x | Adaptive forward HL | Positive survival; lower compatible error | General policy | Session/gap, uncertainty | Standard rule |
| Forward interval | Longer proposed interval means longer validity | $T_{valid}$ and compatible path error | Concordance interval vs survival | Error at 0.5x/1x/2x; emitted range diagnostic | Adaptive forward interval | Positive survival/discrimination | General policy | Session/gap, uncertainty | Standard rule; preserve range warning |

## 23. Perturbation-Class Evidence Contract

Expected realized geometry derives from the frozen semantic addendum:

- `NONE`: lower immediate realized transition magnitude than material classes; no directional profitability claim.
- `REINFORCING`: greater aligned progress/continuation and longer compatibility than `CONTRADICTING`/`REVERSING`.
- `CONTRADICTING`: more weakening and shorter compatibility than `REINFORCING`, without requiring every case to reverse.
- `REVERSING`: greater reversal incidence and shorter time-to-reversal than `REINFORCING`; reversal has semantic precedence.
- `STRUCTURAL/UNKNOWN`: greater ambiguous/data-structural incidence; no directional ordering requirement.

Primary contrasts are reinforcing versus contradicting on weakening/compatibility and reinforcing versus reversing on reversal/time-to-reversal. `NONE` magnitude and structural ambiguity are required secondary subclaims. `EMPIRICALLY_SUPPORTED` requires adequate support for both primary contrasts and expected intervals excluding null; mixed or limited subclaims yield partial; opposite decisive primary contrast yields unsupported; insufficient class support yields inconclusive. Equal class frequency is never required.

## 24. Half-Life Evidence Contract

Half-life is a temporal calibration claim, not an exact expiration forecast. Primary evidence is positive censor-aware concordance between emitted half-life and $T_{valid}$. Secondary evidence compares validity survival at 0.5x, 1.0x, and 2.0x emitted half-life.

Report observations at exact configured floor and ceiling separately; do not interpret those masses as ordinary interior calibration. Do not require realized survival to equal emitted half-life.

## 25. Forward-Interval Evidence Contract

Primary question:

> Does a larger emitted forward interval correspond to longer realized state validity?

Primary statistic is censor-aware concordance between emitted interval and $T_{valid}$. Secondary scores are compatible path error and continuation at 0.5x, 1.0x, and 2.0x interval.

`FORWARD_INTERVAL_RANGE_WARNING` is mandatory diagnostic context. If the emitted range is too compressed for adequate discrimination, classify interval validity `INCONCLUSIVE` or `UNSUPPORTED` according to support/effect rules. Never widen or retune the range during Stage 2.

## 26. Scoring Principles

- Preserve continuous variables and raw effect units.
- Keep anchor DMO identity immutable.
- Record actual elapsed time and target overshoot.
- Separate primary effects from secondary diagnostics.
- Report support and censoring before interpretation.
- Avoid thresholding where continuous scores suffice.
- Do not choose definitions from primary outcomes.

## 27. Numerical Health and Replay Integrity

Preflight validates hashes, schema, chronology, partition, and reserve seal. Replay enforces finite state, bounds, monotonic event/sequence order, and DMO/FMO schema. An `INVALID` DMO or nonfinite core state fails replay integrity and prevents scientific scoring from being presented as valid.

## 28. Immutable Replay Seal

After canonical replay, hash:

- ordered source-row/DMO/FMO identity records;
- resolved frozen configuration;
- DMO state hashes and trace IDs;
- primary boundary and input-mapping specification.

Scoring receives read-only sealed outputs. Any mutation or mismatch aborts with a distinct replay-integrity failure. Scoring cannot call mutable D01.

## 29. Parallel Read-Only Scoring Architecture

Use up to `ProcessPoolExecutor(max_workers=18)` only after the canonical seal. Independent evidence-contract and diagnostic tasks may execute concurrently against read-only records. Chronological D01 updates are never parallelized.

Persist task ID, dimension, PID, parent PID, start/end, elapsed, status, unique worker count, peak concurrency, and failures. Worker count configuration alone is not evidence.

## 30. Determinism Protocol

Perform an independent second sequential replay from identical frozen inputs and initial state. Compare ordered semantic fingerprints containing DMO state hashes, key semantic outputs, FMO intervals/samples, configuration hash, and source-row identity. Exclude PID/wall-clock metadata.

Determinism must pass before dimension-level results are accepted.

## 31. Primary Run Protocol

### Phase A - Preflight

Verify Stage 1 freeze, D01 source/config/schema/design hashes, Stage 2 design freeze, dataset hash, boundaries, chronology, input mapping, and `reserve_sealed=true`.

### Phase B - Canonical Causal Replay

Run exactly one chronological D01 trajectory through primary observations only. Persist immutable DMO/FMO records without future scores.

### Phase C - Immutability Seal

Hash canonical records and prohibit mutation.

### Phase D - Parallel Scoring

Execute independent read-only evidence contracts with at most 18 workers.

### Phase E - Determinism

Repeat canonical replay independently and compare fingerprints.

### Phase F - Report

Produce support, effects, intervals, censoring, strata, and four-level classifications for every dimension.

### Phase G - Hard Stop

Stop before reserve. User owns substantive execution from an external PowerShell launcher prepared by a separately authorized implementation task.

## 32. Stage 2 Design Freeze Procedure

This v0.2 document is not frozen by this task. After human approval, a separate task creates `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2_FREEZE.json` containing:

- design SHA256;
- Stage 1 freeze ID and protected hashes;
- dataset SHA256 and primary/reserve boundaries;
- evidence-contract hashes;
- realized-state-observer specification hash;
- scoring specification hash;
- decision-register and consistency-review hashes.

No runner may execute without that freeze.

## 33. Reserve Hard Stop

Reserve cannot run automatically. No scorer or replay process may read reserve values. After the primary report: STOP, REVIEW, DECIDE.

Future reserve authorization requires frozen methodology, completed/reviewed primary results, no pending rule changes, and explicit human approval. If primary evidence motivates any model or methodology change, reserve remains sealed.

## 34. No Model Modification After Primary Results

Primary weakness is recorded, not repaired. Any D01 change creates a new candidate version that returns through Stage 1. The frozen v0.2 baseline remains immutable, and reserve may not develop the candidate.

## 35. Stage 2 Failure and Reporting Philosophy

Stage 2 is allowed to fail by dimension. Results may be supported, partial, unsupported, or inconclusive. No cosmetic global PASS is required. Methodological integrity, causality, freeze integrity, determinism, and reserve sealing are separate hard gates.

## 36. Future Output Contract

Future root:

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

The run manifest records Stage 1 freeze, Stage 2 design freeze, dataset/partition hashes, `reserve_accessed=false`, point-in-time validation, model/config integrity, parameter tuning false, canonical seal, worker evidence, bootstrap specification, censoring, and determinism.

## 37. Relationship to Stage 3

No trade labels, entries/exits, long/short policy, sizing, transaction costs, Sharpe, drawdown, brokerage, or P&L appear in Stage 2. Any future predictive/decision/trading validity belongs to separately authorized Stage 3 after review of Stage 2 evidence.

## 38. Hard Prohibitions

Do not modify D01 v0.2, tune parameters, use primary outcomes to alter methods, inspect reserve values, run reserve calculations, interpolate observations, filter sessions silently, implement D02/D04, or perform trading analysis.

## 39. Resolution Status

All nine v0.1 pre-implementation design decisions are resolved in this document. Formal human approval and a separate design-freeze task remain required before implementation.

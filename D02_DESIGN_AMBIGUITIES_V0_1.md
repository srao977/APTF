# D02 Design Ambiguities v0.1

## 1. Hard-stop status

**Status:** EIGHT GENUINE D02 MATHEMATICAL GAPS  
**Decision:** D02 DESIGN NOT FREEZE-READY

The repository provides causal ingredients but no authorized formulas for the following mandatory or lifecycle-significant D04 fields. This document intentionally does not select formulas.

## 2. Scientific gaps

### 2.1 `direction`

- **Why D04 requires it:** mandatory `Direction` enum in `ReturnShape`.
- **Available D01 information:** current level and full projected FMO level/velocity path.
- **Why insufficient:** the historical example $\operatorname{sign}(\hat L_t(h)-L_t)$ does not select $h$, specify terminal versus regional shape, or define a scale-aware NEUTRAL region. State/kinematics is empirically unsupported as directional prediction.
- **Missing scientific choice:** projection horizon/region and neutral materiality rule.
- **Smallest clarification:** define one causal FMO coordinate/path statistic and one causal scale-aware three-way classification rule, explicitly non-trading.
- **Downstream consequence:** no valid mandatory D04 direction.

### 2.2 `shape_quality`

- **Why D04 requires it:** mandatory, largest current shape weight, reason codes, and evaluation output.
- **Available D01 information:** coherence, strength, uncertainty, support ratio, and projected paths.
- **Why insufficient:** no authority defines whether quality means smoothness, agreement, support, low uncertainty, path consistency, or a composite. D04 weights score an already-constructed value; they do not construct it.
- **Missing scientific choice:** quality ontology, coordinates, aggregation, and normalization.
- **Smallest clarification:** define a bounded causal quality functional and its evidence interpretation.
- **Downstream consequence:** capturability shape component cannot be calculated legitimately.

### 2.3 `forward_support`

- **Why D04 requires it:** mandatory weighted score and low-support reason code.
- **Available D01 information:** unbounded `state_support_ratio` plus bounded projected strength, persistence, uncertainty, and reversal propensity.
- **Why insufficient:** current support ratio is not bounded `[0,1]`; no authority says whether support is current or path-wide, nor how to aggregate and normalize it.
- **Missing scientific choice:** support semantics, path horizon, aggregation, and causal normalization.
- **Smallest clarification:** choose current-versus-forward meaning and define one bounded transformation using only Q_t.
- **Downstream consequence:** mandatory D04 support score is unavailable.

### 2.4 `expected_lifetime_seconds`

- **Why D04 requires it:** mandatory; nonpositive values expire the shape and the value multiplies capturability.
- **Available D01 information:** forward interval, forward half-life, and projected paths.
- **Why insufficient:** interval extent, half-life, and threshold-crossing validity are different temporal semantics. Stage 2 found interval and half-life inconclusive.
- **Missing scientific choice:** exact meaning of lifetime and its relation to re-evaluation/expiration.
- **Smallest clarification:** select one authorized duration definition and specify behavior at context-only reevaluations.
- **Downstream consequence:** D04 safety and lifetime component are undefined.

### 2.5 `magnitude_score`

- **Why D04 requires it:** mandatory weighted shape score.
- **Available D01 information:** current level, projected levels, interval, and strength.
- **Why insufficient:** no authority selects terminal displacement, maximum excursion, path extent, signed/absolute treatment, or a causal scale that maps unbounded normalized displacement to `[0,1]`. `perturbation_magnitude` measures innovation, not expected return.
- **Missing scientific choice:** path statistic, horizon, direction treatment, and normalization.
- **Smallest clarification:** define one FMO displacement functional and a frozen causal normalization independent of outcomes.
- **Downstream consequence:** expected-move magnitude cannot enter D04.

### 2.6 `decay_score`

- **Why D04 requires it:** mandatory and inverted in shape scoring.
- **Available D01 information:** forward half-life and projected strength/persistence decay.
- **Why insufficient:** D01 defines coordinate-wise decay but not which coordinate, reference horizon, or path summary is D04's scalar degradation score.
- **Missing scientific choice:** decay target, horizon, and scalar aggregation.
- **Smallest clarification:** define a bounded scalar summary of one or more existing projected decay paths.
- **Downstream consequence:** D04 inverse-decay component is undefined.

### 2.7 `reversal_risk`

- **Why D04 requires it:** mandatory, inverted in shape scoring, and thresholded for reason codes.
- **Available D01 information:** current and projected reversal propensity plus perturbation class.
- **Why insufficient:** propensity is not declared a probability; direct transfer versus path maximum/terminal/integral is unspecified. Stage 2 evidence is inconclusive.
- **Missing scientific choice:** whether semantics remain propensity or become a path risk aggregate, and which aggregate.
- **Smallest clarification:** align D04 naming/semantics with either direct propensity or one explicitly defined causal FMO aggregate.
- **Downstream consequence:** reversal penalty cannot be interpreted or validated.

### 2.8 `active`

- **Why D04 requires it:** defaults true but controls safety closure and entry eligibility; therefore it is lifecycle-significant.
- **Available D01 information:** model time, interval, half-life, and each successful new Q_t emission.
- **Why insufficient:** no rule defines when a shape expires if D04 reevaluates because context changes without a new Q_t. Always true defeats expiration; wall-clock/future-row checks violate deterministic event-time semantics.
- **Missing scientific choice:** validity duration and invocation-time event semantics.
- **Smallest clarification:** define causal event-time expiry relative to the reviewed lifetime contract and specify who reevaluates it.
- **Downstream consequence:** stale-shape safety behavior is undefined.

## 3. Non-scientific interface blockers

These are not counted among the eight mathematical gaps but still block complete mandatory coverage:

- `candidate_id` belongs to the D04/D03 control/candidate boundary and has no Q_t source.
- `candidate_rr` is mandatory in the prototype model but unused by D04 core. D01 explicitly prohibits confusing `state_support_ratio` with trade reward/risk. It should be removed or relocated only through a separately authorized D04 interface revision.
- `return_shape_id` serialization and `version` persistence/restore rules need deterministic engineering definitions.

## 4. Resolution constraints

The gaps cannot be resolved by historical outcome fitting, first-six-month formula selection, reserve access, D04 placeholder weights, Stage 2 observer values, or trading-performance optimization. Each clarification must be justified from system semantics and frozen before implementation.

## 5. Stop decision

Per the hard-stop policy, no D02 schema or freeze manifest is created. The next action is human review and scientific clarification.

# D01 Stage 2 Implementation Design Ambiguity

## Status

**STAGE_2_IMPLEMENTATION_DESIGN_AMBIGUITY**

Implementation stopped before creation of Stage 2 code, runners, launchers, replay artifacts, or scientific outputs.

## Frozen Authority Verification

- Stage 1 freeze ID: `D01_V0_2_STAGE1_ACCEPTED_20260815T161928Z` - PASS
- Stage 1 protected hashes - PASS
- Stage 2 freeze manifest SHA256 `094AF0595575F93B045AEEC6E993128CF3D6EBEC31565602D9394AB52694AABF` - PASS
- Five frozen Stage 2 specification hashes - 5/5 PASS
- Dataset SHA256 `73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D` - PASS

No frozen authority was modified.

## Blocking Ambiguity 1: Uncertainty Primary Observable

The frozen evidence contract specifies:

```text
Independent observables:
    1 - efficiency
    normalized deviation
    ambiguous incidence

Primary score:
    Spearman uncertainty vs realized ambiguity index
```

The frozen design does not define the scalar `realized ambiguity index` as a deterministic function of those three components. It does not specify:

- component normalization;
- weights;
- sum, mean, maximum, product, or lexicographic aggregation;
- horizon aggregation;
- treatment of the binary ambiguous-incidence component alongside continuous components;
- null value after aggregation.

The implementation prompt explicitly requires:

```text
If the frozen spec gives components but not a canonical scalar combination,
STOP and report:
SCORING_SPEC_AMBIGUITY
rather than inventing weights.
```

Any implementation choice would create new scientific behavior after design freeze and could materially change rank association, bootstrap intervals, and the final evidence classification.

## Blocking Ambiguity 2: State/Kinematics Primary Statistic

The frozen evidence contract names the primary score as:

```text
Sign/geometry concordance of DMO direction and realized slope/progress
```

The observer defines direction, slope, endpoint progress, and compatibility categories, but the scoring specification does not define one canonical primary statistic from them. Missing details include:

- whether concordance is a binary fraction, rank statistic, signed score, or joint slope/progress statistic;
- how slope and endpoint progress are combined when they disagree;
- the primary horizon or horizon aggregation;
- the null value used by the four-level confidence-interval rule;
- whether ambiguous anchors are omitted, treated as censored, or retained as a separate outcome in the primary estimate.

Choosing among these alternatives would alter the scientific primary effect and cannot be delegated to implementation.

## Blocking Ambiguity 3: Perturbation-Magnitude Realized Transition Scalar

The frozen contract states:

```text
Independent observable:
    maximum absolute raw-close displacement and slope change

Primary score:
    Spearman perturbation magnitude vs realized transition magnitude
```

No canonical scalar `realized transition magnitude` is defined from maximum absolute displacement and slope change. The design does not specify normalization, weighting, aggregation, or which component is primary. Selecting one changes the Spearman statistic and classification.

## Blocking Ambiguity 4: Categorical Perturbation-Class Primary Effects

The frozen class contract requires two primary contrasts:

1. `REINFORCING` versus `CONTRADICTING` on weakening and compatibility.
2. `REINFORCING` versus `REVERSING` on reversal incidence and time-to-reversal.

Each contrast contains two outcomes, but no canonical combined effect, precedence rule, statistical estimator, null, or confidence-interval construction is frozen. The classification rule requires both primary contrasts and expected intervals, so implementation cannot choose one outcome or invent a composite without changing scientific authority.

## Blocking Ambiguity 5: Interval-Censored Concordance Estimator

Persistence, reversal propensity, observation half-life, forward half-life, and forward interval require censor-aware concordance with interval censoring retained.

The decision register permits marking a component inconclusive if a chosen estimator cannot consume interval censoring, but no estimator is selected by the frozen design. Choosing an estimator is consequential because alternatives differ in comparable-pair definitions, handling of interval overlap, null distribution, and bootstrap behavior.

This ambiguity could be resolved either by freezing a specific valid interval-censored concordance estimator or by explicitly freezing a rule that the primary estimate is `INCONCLUSIVE` whenever interval-censored events are present. The current design does not authorize either choice.

## Why Implementation Cannot Proceed Partially

The requested runner must implement all eleven evidence contracts, bootstrap their primary effects, and produce four-level classifications. The undefined primary statistics are therefore on the critical path to:

- scoring schema;
- worker task contracts;
- bootstrap sufficient records;
- null definitions;
- dimension classifications;
- reports and manifests;
- implementation freeze identity.

Implementing replay infrastructure while leaving scientific contracts unresolved would not satisfy the authorized task's preparation gate and would risk freezing an implementation with invented behavior.

## Required Design Clarification

Before implementation, a new human-approved frozen clarification must define at minimum:

1. Exact formula for the uncertainty `realized ambiguity index`, including component scaling, weights/aggregation, horizon policy, and null.
2. Exact state/kinematics primary statistic, horizon policy, ambiguous-anchor handling, and null.
3. Exact perturbation realized-transition scalar from displacement and slope change.
4. Exact estimator/effect for each perturbation-class primary contrast, including how paired outcomes are combined or separately adjudicated.
5. Exact interval-censored concordance estimator and null, or an explicit frozen inconclusive policy.

The clarification must be approved and frozen before code implementation. Existing frozen Design v0.2 and specification files must not be edited in place; use an addendum or successor design authority with new hashes.

## Integrity and Execution Attestation

- D01 v0.2 modified: NO
- Stage 1 freeze modified: NO
- Stage 2 frozen design/specifications modified: NO
- Parameters tuned: NO
- Stage 2 package created: NO
- Stage 2 Python runner created: NO
- Stage 2 PowerShell launcher created: NO
- Historical replay started: NO
- Primary scientific outcomes inspected: NO
- Reserve observation values inspected: NO
- Reserve accessed: NO
- Stage 3 implemented: NO

## Final Decision

**STAGE_2_IMPLEMENTATION_DESIGN_AMBIGUITY**

Implementation is blocked pending frozen scientific clarification.
# D01 Stage 2 Primary Empirical Characterization Closeout v0.2

## 1. Status

**STAGE 2 COMPLETE - DIMENSION-LEVEL EMPIRICAL CHARACTERIZATION ACCEPTED**

Stage 2 is a completed experiment. It is neither a global PASS nor a global FAIL. Its accepted output is the frozen dimension-level characterization below.

Stage 2 will not be repeated, optimized, reframed, or extended against the consumed primary period.

## 2. Purpose

Stage 2 asked whether frozen D01 v0.2 state descriptions at model time $t$ were empirically consistent with independently observed subsequent raw-market geometry. It did not test trading rules, profitability, execution, P&L, or BUY/SELL/HOLD accuracy.

The causal structure was:

```text
authorized observations at or before t
    -> frozen D01 v0.2 state at t
    -> independently realized future raw-close geometry
    -> frozen dimension-level scoring
```

## 3. Corpus and Isolation

Primary corpus:

```text
[2022-09-30T04:00:00-04:00, 2023-03-30T04:00:00-04:00)
```

- Records: 106,603
- Eligible anchors: 106,601
- Dataset SHA256: `73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB5E6A1055D`
- Reserve accessed: NO
- Outcome/decision columns used as inputs: NO
- D01 modified: NO
- Parameters tuned: NO

## 4. Canonical Replay and Integrity

- Canonical replay seal: `6CF2BE31F8815ADB3B5B2E70916A4CD5CDAF427783DA9098E5167313EB70F981`
- Anchor evidence seal: `37AA735D5ECD2F93C6C6A084AD4025A08B5714870919EF36BEEFC856E07F6C8D`
- Semantic fingerprint: `F5F1D5F3229FFC2B79EF6F1CB65961FFF0FD9788FC9EC8E6BEC9534A4A739572`
- Point-in-time validation: PASS
- Determinism: PASS
- Numerical health: PASS
- Frozen implementation integrity: PASS
- Reserve hard stop: PASS

## 5. Accepted Dimension-Level Evidence

### Empirically Supported

**Strength**

- Primary effect: `0.1280187733`
- 95% CI: `[0.1125364826, 0.1438115248]`
- Operational meaning: may be described as empirically supported D01 state information about subsequent realized expression, defined by absolute slope and path efficiency.
- It may not be described as directional, causal, profitable, or independently sufficient for a trade decision.

**Perturbation Magnitude**

- Primary effect: `0.0640641833`
- 95% CI: `[0.0504809905, 0.0778738130]`
- Operational meaning: may be described as empirically supported information about subsequent realized transition magnitude.
- It may not be described as validated perturbation class, direction, causality, or profitability.

### Partially Supported

**Coherence**

- Primary effect: `0.0035698264`
- 95% CI: `[-0.0117912882, 0.0186294481]`
- Operational meaning: remains limited/unresolved. It must not be promoted to an independently validated market predictor. Any future use must disclose its partial status.

### Unsupported Under Frozen Stage 2 Semantics

**State/Kinematics**

- Primary effect: `-0.0060375482`
- 95% CI: `[-0.0090254457, -0.0030105598]`
- Operational meaning: may remain a mathematically defined D01 quantity, but may not be described as a historically validated directional predictor under the frozen 15-minute state-geometry hypothesis.

**Persistence**

- Primary effect: `-0.0023134156`
- 95% CI: `[-0.0042790690, -0.0003909978]`
- Operational meaning: may remain a mathematically defined D01 quantity, but may not be described as a historically validated realized-persistence predictor under the frozen survival hypothesis.

### Inconclusive

The following remain limited/unresolved and may not be silently promoted to validated predictors:

- Uncertainty
- Reversal Propensity
- Perturbation Class
- Observation Half-Life
- Forward Half-Life
- Forward Interval

Forward Interval canonical result:

- effect: `-0.0020978238`
- 95% CI: `[-0.0041440592, 0.0000308957]`

## 6. One-Level Operational Evidence Categories

### Category A - Empirically Supported

Dimensions: Strength, Perturbation Magnitude.

Stage 3 design may treat these as empirically supported D01 state information. This status alone does not authorize any decision rule.

### Category B - Limited / Unresolved

Dimensions: Coherence, Uncertainty, Reversal Propensity, Perturbation Class, Observation Half-Life, Forward Half-Life, Forward Interval.

These remain valid D01 state coordinates but are not independently validated market predictors. Any Stage 3 use must retain and report this status.

### Category C - Empirically Unsupported Under Frozen Stage 2 Semantics

Dimensions: State/Kinematics, Persistence.

Stage 3 may not claim that State/Kinematics is a historically validated directional predictor or that Persistence is a historically validated realized-persistence predictor. This claim boundary does not require removing either coordinate from D01.

## 7. Model State Is Not a Trading Decision

Stage 2 state validity is not Stage 3 trading validity.

Stage 3 asks a new question:

```text
causal observations at t
    -> frozen D01 state at t
    -> frozen Stage 3 Decision Processor
    -> committed decision at t
    -> future outcome revealed to evaluator
    -> decision scored
```

Stage 2 correlations do not imply decision quality, causality, profitability, or sufficient BUY/SELL/HOLD information.

## 8. D01 and Stage 2 Closure

- D01 v0.2 remains frozen and unchanged.
- D01 v0.3 is not created or authorized.
- Stage 2 scoring and hypotheses remain frozen.
- No new Stage 2 diagnostics, alternatives, subsets, regimes, horizons, or thresholds are authorized.
- Stage 2 is not being repeated.

## 9. Reserve

The remaining period is sealed:

```text
[2023-03-30T04:00:00-04:00, 2023-09-30T04:00:00-04:00)
```

It is reserved exclusively for a future one-way evaluation of the complete frozen executable trading system. It is not available for Stage 2 confirmation or Stage 3 development.

## 10. Transition Boundary

Stage 3 is ready for human design review only. This closeout does not define decision vocabulary behavior, entries, exits, positions, costs, execution, or metrics.

Any future Stage 3 design must consume frozen D01 v0.2 and preserve the operational evidence categories in this closeout.

## 11. Final Closeout

**STAGE 2 COMPLETE - DIMENSION-LEVEL EMPIRICAL CHARACTERIZATION ACCEPTED**

- Model changes: NONE
- Parameter changes: NONE
- Stage 2 rerun required: NO
- Reserve: SEALED
- Stage 3: NOT STARTED

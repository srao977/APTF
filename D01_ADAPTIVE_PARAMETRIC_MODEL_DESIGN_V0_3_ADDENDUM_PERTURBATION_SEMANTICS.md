# D01 Adaptive Parametric Model Design v0.3 Addendum: Perturbation Semantics

**Document:** `D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS`  
**Status:** FROZEN SEMANTIC CLARIFICATION  
**Applies to:** D01 v0.2 implementation and subsequent compatible versions  
**Adds to:** `D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md`  
**Does not replace:** the D01 v0.2 implementation design

## 1. Purpose

This addendum resolves the ambiguity between perturbation magnitude and perturbation semantic class discovered during D01 v0.2 synthetic semantic acceptance.

The perturbation state is:

$$
Q_t = (q_t, c_t)
$$

where:

- $q_t$ is perturbation magnitude or strength;
- $c_t$ is perturbation semantic class.

Magnitude answers **HOW STRONG?**

Class answers **WHAT KIND?**

Neither component substitutes for the other.

## 2. Authoritative Semantic Decision

`NONE` means:

> No materially detectable perturbation is present at model time $t$.

`NONE` must not mean:

> A perturbation was detected, but its magnitude was insufficient to assign a semantic class.

Once a perturbation is materially detected, D01 must assign its best causal semantic class. Class assignment must not be suppressed solely because magnitude did not cross a class-specific severity threshold.

## 3. Perturbation State Contract

The emitted perturbation state must preserve both components:

```text
perturbation_magnitude = q_t
perturbation_class = c_t
```

The required class domain remains:

```text
NONE
REINFORCING
CONTRADICTING
REVERSING
STRUCTURAL/UNKNOWN
```

The magnitude must remain bounded and deterministic. The class must be selected from current and prior causal state only.

## 4. Material Detection

Detection and semantic typing are separate stages.

For normalized innovation magnitude $q_t$, define the implementation materiality floor from the existing numerical contract:

$$
q_{material} = \sqrt{\epsilon}
$$

where $\epsilon$ is the configured numerical denominator epsilon.

A perturbation is materially detected when either:

1. $q_t > q_{material}$; or
2. source quality is sufficiently degraded to require `STRUCTURAL/UNKNOWN` treatment.

This floor is a numerical detectability boundary, not a fitted market threshold and not a scenario-tuned parameter.

If neither condition holds, the class is `NONE`.

## 5. Semantic Typing Order

For a materially detected perturbation, apply the following deterministic priority:

1. **STRUCTURAL/UNKNOWN** when source quality is below the configured structural-quality boundary.
2. **REVERSING** when current and prior nonzero velocity have opposite signs.
3. **CONTRADICTING** when the velocity change opposes the prior nonzero velocity without establishing a sign reversal.
4. **REINFORCING** for other materially detected innovations compatible with continuation or state strengthening.

Formally, with prior velocity $V_{t-1}$ and current velocity $V_t$:

$$
\Delta V_t = V_t - V_{t-1}
$$

Reversal evidence exists when:

$$
V_{t-1} V_t < 0
$$

Contradiction evidence exists when:

$$
V_{t-1} \ne 0
\quad\text{and}\quad
V_{t-1}\Delta V_t < 0
$$

after excluding reversal.

The fallback class for a materially detected, non-structural, non-reversing, non-contradicting perturbation is `REINFORCING`, not `NONE`.

## 6. Threshold Semantics

Class-specific magnitude or severity thresholds may be retained for diagnostics, severity bands, or downstream policy, but they must not turn a materially detected perturbation back into `NONE`.

In particular:

- magnitude thresholds answer how strong the perturbation is;
- directional/state relations answer what kind of perturbation it is;
- semantic class selection must not require a second, higher magnitude gate after material detection.

## 7. Downstream Semantics

Downstream mechanisms may use $q_t$, $c_t$, or both according to their declared contracts.

- Adaptive learning-rate modulation may use $q_t$ as a bounded continuous factor.
- Persistence may respond to contradictory or reversing $c_t$.
- Uncertainty may respond to magnitude, structural class, and data quality.
- Reversal propensity may respond to contradictory or reversing $c_t$.
- Half-life perturbation reset must use $c_t$ consistently; a detected contradiction or reversal must not lose its reset solely because magnitude is below a class-specific severity threshold.
- Forward interval may use $q_t$ continuously.

No downstream component may infer that `NONE` means an unclassified but detected perturbation.

## 8. DMO and Trace Requirements

The existing DMO fields remain authoritative and jointly represent $Q_t$:

```text
perturbation_magnitude
perturbation_class
```

Structured traces must make the following reviewable for each observation:

```text
innovation magnitude
materiality floor
material detection result
prior velocity
current velocity
velocity change
source quality
selected perturbation class
perturbation magnitude
```

No DMO schema rename is required by this addendum.

## 9. Causality, Determinism, and Bounds

The clarification preserves all v0.2 invariants:

- classification is entity-local and point-in-time causal;
- identical input, configuration, and initial state produce identical magnitude and class;
- magnitude, learning-rate effects, state, half-life, and forward interval remain bounded;
- no future observation contributes to detection or typing;
- no historical or reserve data is required to implement this semantic contract.

## 10. Required Verification

Implementation verification must include at least:

1. zero or numerically immaterial innovation produces `NONE`;
2. material compatible innovation produces `REINFORCING`;
3. material opposing velocity change produces `CONTRADICTING`;
4. material sign reversal produces `REVERSING`;
5. degraded source quality produces `STRUCTURAL/UNKNOWN`;
6. all non-`NONE` classes preserve bounded magnitude and adaptation effects;
7. contradictory/reversing classes reach persistence, reversal, and half-life consumers;
8. deterministic replay and point-in-time causality remain unchanged.

Targeted synthetic revalidation must verify perturbation classification and half-life event response before any historical experiment.

## 11. Non-Goals

This addendum does not:

- replace the D01 v0.2 implementation design;
- tune perturbation thresholds to synthetic scenarios;
- redefine strength, uncertainty, persistence, or reversal propensity;
- authorize changes to scenario generators or acceptance windows;
- authorize historical or reserve-data use;
- implement D02, D04, broker, position, or trading-policy behavior.

## 12. Final Semantic Invariant

For every D01 output:

> If `perturbation_class == NONE`, D01 asserts that no materially detectable perturbation is present.

Conversely:

> If a perturbation is materially detected, D01 emits its best causal semantic class even when its magnitude is moderate.

This invariant is the controlling clarification for all D01 perturbation classification, reporting, and class-dependent response behavior.
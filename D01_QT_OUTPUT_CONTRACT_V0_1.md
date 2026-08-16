# D01 Q_t Output Contract v0.1

## 1. Contract status

**Status:** CANONICAL PRE-STAGE-3 OUTPUT CONTRACT; DOCUMENTATION ONLY

`Q_t` is the structured current output tuple emitted by frozen D01 v0.2 at causal time `t`. It is not a simplistic numerical vector. Machine-readable field metadata is in `D01_QT_OUTPUT_SCHEMA_V0_1.json`.

```text
Q_t = {
  identity: {model_time, entity_id, model_version},
  current_state: {state_level, state_velocity, state_acceleration,
    state_curvature, strength, coherence, persistence,
    perturbation_magnitude, perturbation_class, uncertainty,
    reversal_propensity, state_support_ratio,
    observation_half_life, forward_half_life},
  forward_state: {forward_interval, forward_samples}
}
```

This is exactly **19 top-level canonical fields**: `3 + 14 + 2`.

## 2. Emission timing and causality

`D01V02Model.step` validates sequence order, uses only the current normalized observation and prior runtime state, updates all causal coordinates, then assembles `DMOOutput` and `FMOOutput`. `Q_t` is available only after that step succeeds. Later observations do not revise the already emitted `Q_t`.

There is no nullable/missing-field mode in the returned dataclasses. Authorized unavailable quote coordinates are represented upstream through constructed availability flags and `None` defaults; they are not canonical fields. Invalid causal sequence or nonfinite-policy failure prevents a valid emission rather than filling `Q_t` with future or imputed values.

## 3. Field contract

| # | Canonical field | Exact implementation source | Type / units | Contractual range | Update, initialization, persistence, and perturbation path | Stage 2 status |
|---:|---|---|---|---|---|---|
| 1 | `model_time` | `model.py::D01V02Model.step`, `DMOOutput.model_time` | float; UTC event seconds | No numeric bound; monotonic causal | Current event time; carried as identity; no perturbation path | N/A |
| 2 | `entity_id` | `model.py::D01V02Model.step`, `DMOOutput.entity_id` | string identifier | Configured identifier | Fixed at model construction; persistent; no perturbation path | N/A |
| 3 | `model_version` | `model.py::D01V02Model.step`, from `D01V02Config.model_version` | string version | Accepted `0.2` | Fixed by configuration; no perturbation path | N/A |
| 4 | `state_level` | `kinematics.py::compute_kinematics` | float; normalized displacement | `NOT_SPECIFIED`; unbounded | Recomputed from adaptive reference/scale; first output `0` because reference equals price; not perturbation-driven | State/Kinematics: unsupported |
| 5 | `state_velocity` | `kinematics.py::compute_kinematics` | float; normalized displacement/s | `[-50,50]` | Recomputed using prior level; runtime prior `0`; hard clipped; not perturbation-driven | State/Kinematics: unsupported |
| 6 | `state_acceleration` | `kinematics.py::compute_kinematics` | float; normalized displacement/s^2 | `[-200,200]` | Recomputed using prior velocity; runtime prior `0`; hard clipped; not perturbation-driven | State/Kinematics: unsupported |
| 7 | `state_curvature` | `kinematics.py::compute_kinematics` | float; normalized kinematic curvature | `[-200,200]` | Recomputed each observation and hard clipped; not perturbation-driven | State/Kinematics: unsupported |
| 8 | `strength` | `strength.py::compute_strength` | float score | `[0,1]` | Runtime default `0`, but first emission is recomputed using current signals and prior uncertainty `0.15`; indirect, not direct, perturbation effect | Supported |
| 9 | `coherence` | `coherence.py::compute_coherence` | float agreement ratio | `[0,1]` | Recomputed from displacement, velocity, acceleration, and volume evidence; no direct perturbation input | Limited/unresolved |
| 10 | `persistence` | `persistence.py::update_persistence` | float recursive score | `[0,1]` | Runtime default `0`; recursively updated; perturbation class applies a direct penalty | Unsupported |
| 11 | `perturbation_magnitude` | `perturbation.py::classify_perturbation` | float normalized innovation | `[0,1]` | Runtime default `0`, first emission recomputed; direct perturbation coordinate | Supported |
| 12 | `perturbation_class` | `perturbation.py::classify_perturbation` | enum string | `NONE`, `REINFORCING`, `CONTRADICTING`, `REVERSING`, `STRUCTURAL/UNKNOWN` | Classified each observation; no emitted runtime default | Limited |
| 13 | `uncertainty` | `uncertainty.py::compute_uncertainty` | float score | `[0,1]` | Runtime default `0.15`, first emission recomputed; directly uses innovation and structural/unknown indicator | Limited |
| 14 | `reversal_propensity` | `reversal.py::compute_reversal_propensity` | float score | `[0,1]` | Runtime default `0.1`, first emission recomputed; perturbation class directly contributes | Limited |
| 15 | `state_support_ratio` | `model.py::D01V02Model.step` | float ratio | `>=0`; no finite upper bound | Recomputed as strength*persistence / epsilon-protected uncertainty+reversal denominator; indirect perturbation effects | Not independently tested |
| 16 | `observation_half_life` | `half_life.py::adapt_half_life` | float seconds | `[15,900]` | Recursive baseline `120`, updated before first emission; class directly shortens selected perturbations | Limited |
| 17 | `forward_half_life` | `half_life.py::adapt_half_life` | float seconds | `[15,900]` | Recursive baseline `120`, updated before first emission; class directly affects update and sample decay | Limited |
| 18 | `forward_interval` | `forward.py::compute_forward_interval`, source `FMOOutput.interval_length` | float seconds | `[10,600]` | Recomputed from baseline `60` and current state; magnitude is a direct input | Limited |
| 19 | `forward_samples` | `model.py::D01V02Model.step`, source `FMOOutput.samples` | `list[FMOSample]` | Exactly configured count; accepted/default `8` | Regenerated each observation; inherits current state and forward-half-life decay; indirect perturbation effects | Not independently tested as a structured list |

All 19 are `DIRECTLY_AVAILABLE` at the future Stage 3 input boundary. Availability does not override evidence status.

## 4. Nested FMO sample contract

The accepted configuration has `ForwardConfig.sample_count = 8`, so each accepted/default `forward_samples` list contains exactly eight `FMOSample` objects. Configuration can theoretically alter the count; the invariant is exactly `config.forward.sample_count` objects.

| Nested field | Type / units | Contractual range | Source semantics |
|---|---|---|---|
| `tau` | float seconds | `0 < tau <= forward_interval` | Elastic sample coordinate from `forward.py::forward_samples` |
| `level` | float projected normalized displacement | `NOT_SPECIFIED`; unbounded | `level + velocity*tau + 0.5*acceleration*tau^2` |
| `velocity` | float projected normalized displacement/s | `[-50,50]` | Bounded current velocity multiplied by decay in `(0,1]` |
| `uncertainty` | float score | `[0,1]` | Current uncertainty increased with decay loss and clipped |
| `strength` | float score | `[0,1]` | Current strength decayed and clipped |
| `persistence` | float score | `[0,1]` | Current persistence decayed and clipped |
| `reversal_propensity` | float score | `[0,1]` | Current reversal propensity increased with decay loss and clipped |

These are structured projections, not future observations or observed outcomes.

## 5. Adaptation boundary

Adaptive reference/scale, recursive persistence and half-lives, current signal recomputation, and forward projection are part of frozen D01 computation. `parameter_state` and `parameter_update_magnitude` remain diagnostics and are not canonical market state. No Stage 2 result is fed back into adaptation.

## 6. Explicit exclusions

The returned DMO contains exactly **9 emitted diagnostic/internal/identity-integrity fields excluded from canonical `Q_t`**:

`parameter_state`, `parameter_update_magnitude`, `data_quality`, `model_health`, `dmo_schema_version`, `fmo_schema_version`, `config_hash`, `state_hash`, `trace_id`.

They remain available in the returned DMO for diagnostics, but the initial Stage 3 interface **must not consume them** without a future explicit architecture revision and design justification. Additional `RuntimeState`, snapshot, and `TraceRecord` fields are internal/diagnostic and are not included in this count of nine emitted diagnostics.

Exactly **12 Stage 2 observer/evaluator concepts are outside `Q_t`**: realized displacement; slope; quadratic coefficient/curvature; path length; efficiency; normalized deviation; maximum signed progress; terminal signed progress; realized category; `T_valid`/censor state; realized ambiguity index; realized transition magnitude.

Exactly **4 future/prohibited classes are outside `Q_t` and unavailable to causal construction**: future raw observations before reveal; outcome/benchmark labels; BUY/SELL/HOLD or vendor decisions; reserve data.

## 7. Claim boundary

`Q_t` is a causal availability contract, not a trading-sufficiency claim. Strength and perturbation magnitude are supported only within their frozen Stage 2 semantic claims. Limited and unsupported coordinates remain directly available but cannot be promoted to validated predictors. This contract defines no Stage 3 rule.

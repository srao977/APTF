# D01 Stage 2 to Q_t Reconciliation v0.1

## 1. Purpose

This document reconciles all **11** frozen Stage 2 tested dimensions to direct canonical `Q_t` fields and to independent observer quantities. Direct fields are causal outputs at `t`; observer quantities are computed only from later revealed raw close/time geometry and are never part of `Q_t`.

## 2. Complete dimension reconciliation

| # | Stage 2 dimension | Direct canonical Q_t field(s) | Independent observer/evaluator quantities | Frozen status | Stage 3 interpretation boundary |
|---:|---|---|---|---|---|
| 1 | Strength | `strength` | `slope`, `efficiency`, `maximum_signed_progress`, `terminal_signed_progress` as realized-expression geometry | `SUPPORTED` | Supported state information associated with subsequent realized expression; not directional, causal, profitable, or independently sufficient. |
| 2 | Perturbation Magnitude | `perturbation_magnitude` | `realized_displacement`, `slope`, `realized_transition_magnitude` | `SUPPORTED` | Supported information about subsequent realized transition magnitude; not validated class, direction, causality, profitability, or sufficiency. |
| 3 | Coherence | `coherence` | `efficiency`, `normalized_deviation`, `realized_category` | `LIMITED_UNRESOLVED` | Partially supported and unresolved; not an independently validated predictor. |
| 4 | Uncertainty | `uncertainty` | `efficiency`, `normalized_deviation`, `realized_ambiguity_index`, `realized_category` | `LIMITED` | Explicitly unresolved; not validated ambiguity or risk information. |
| 5 | Reversal Propensity | `reversal_propensity` | `realized_category`, `T_valid`/censor state, `maximum_signed_progress`, `terminal_signed_progress` | `LIMITED` | Not a validated reversal predictor or trade-timing signal. |
| 6 | Perturbation Class | `perturbation_class` | `realized_category`, `efficiency`, `normalized_deviation`, `T_valid`/censor state | `LIMITED` | Unresolved semantic type; not validated reinforcing, contradicting, or reversing decision evidence. |
| 7 | Observation Half-Life | `observation_half_life` | `T_valid`/censor state, with realized-category compatibility | `LIMITED` | Unresolved temporal coordinate; not validated state-relevance duration. |
| 8 | Forward Half-Life | `forward_half_life` | `T_valid`/censor state, `normalized_deviation`, `realized_category` | `LIMITED` | Unresolved forward-temporal coordinate; not a validated useful-state horizon. |
| 9 | Forward Interval | `forward_interval` sourced from `FMOOutput.interval_length` | `T_valid`/censor state, `normalized_deviation`, `realized_category` | `LIMITED` | Unresolved interval coordinate; not a validated useful horizon and must retain its range warning. |
| 10 | State/Kinematics | `state_level`, `state_velocity`, `state_acceleration`, `state_curvature` | `realized_displacement`, `slope`, `quadratic_coefficient_or_curvature`, `path_length`, `efficiency`, `normalized_deviation`, `maximum_signed_progress`, `terminal_signed_progress`, `realized_category` | `EMPIRICALLY_UNSUPPORTED_UNDER_FROZEN_STAGE_2_SEMANTICS` | Four direct mathematical fields remain available; the realized comparator is observer-only. No validated directional claim. |
| 11 | Persistence | `persistence` | `T_valid`/censor state and realized-category compatibility | `UNSUPPORTED` | Mathematical recursive state only; not a validated realized-persistence predictor. |

Every tested dimension maps to at least one direct `Q_t` field. `State/Kinematics` maps to four fields. No tested dimension maps an observer quantity into `Q_t`.

## 3. Observer-only inventory

The complete conceptual observer/evaluator inventory is **12** fields:

1. realized displacement;
2. slope;
3. quadratic coefficient/curvature;
4. path length;
5. efficiency;
6. normalized deviation;
7. maximum signed progress;
8. terminal signed progress;
9. realized category;
10. `T_valid`/censor state;
11. realized ambiguity index;
12. realized transition magnitude.

These quantities were independent comparators used to characterize D01 dimensions. They are not emitted by D01, are not canonical `Q_t`, and cannot be available at anchor time without leakage.

## 4. Forward sample reconciliation

`forward_samples` is directly and causally available as a structured list. Its components inherit State/Kinematics, Strength, Persistence, Uncertainty, Reversal Propensity, and Forward Half-Life semantics. Stage 2 did not test the complete list as a single independent dimension, so its status is `NOT_TESTED_AS_INDEPENDENT_DIMENSION`; component evidence restrictions remain attached.

## 5. Evidence authority placement

```text
Q_t at t ---------------------------> future Stage 3 input boundary
  |
  +-> frozen Stage 2 evidence register constrains permissible claims

future raw close/time after t ------> observer quantities ------> evaluator only
```

The evidence register does not append fields to `Q_t`, update it, or convert realized geometry into causal state.

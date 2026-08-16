# D01 Pre-Stage-3 Architecture Trace v0.1

## 1. Status and authority

**Status:** PRE-STAGE-3 DOCUMENTATION ONLY; STAGE 3 NOT DESIGNED

This trace is subordinate to the verified frozen authority chain. The exact closeout-freeze SHA256 is `2CBDD76F97036E5546132DEE171ADFA2B0DD376F7DDF9E5D6E3C8E87F09208EE`; the canonical Stage 2 replay seal is `6CF2BE31F8815ADB3B5B2E70916A4CD5CDAF427783DA9098E5167313EB70F981`. This document changes no frozen artifact, implementation, empirical result, or reserve boundary.

## 2. Architecture history

| Stage | Purpose | Result | Present authority consequence |
|---|---|---|---|
| Stage 1 | Synthetic acceptance of D01 v0.2 behavior and implementation contract | Accepted and frozen | D01 v0.2 is the sole accepted market-state inference model. |
| Stage 2 | Causal historical characterization of each preregistered D01 dimension against independently realized future geometry | Complete; dimension-level empirical characterization accepted | Evidence categories constrain interpretation of emitted state. They do not alter the time-varying state or authorize trading claims. |
| Stage 3 | Future design of a complete trading-decision system | Not designed and not started | No decision vocabulary, thresholds, rules, position logic, execution assumptions, costs, benchmark, or scoring design is authorized here. |

## 3. Causal architecture

```text
At or before t
  event_timestamp_utc, close, volume, session_type, data_valid
  + constructed entity/sequence/availability/mask coordinates
                         |
                         v
                  frozen D01 v0.2
                         |
                         v
          canonical Q_t (19 structured fields)
                         |
       +-----------------+------------------+
       |                                    |
       v                                    v
Stage 2 evidence authority          future Stage 3 boundary
constrains claims about Q_t         Stage3Input_t = (Q_t, ExecutionContext_t)
but never mutates Q_t               design remains undefined

After commitment/reveal only:
future raw observations -> independent evaluator/outcomes
```

The evidence register is interpretation metadata, not an input stream, adaptive parameter, mask, or time-varying coordinate of `Q_t`.

## 4. Canonical output lineage

`D01V02Model.step` accepts one normalized causal observation, updates the runtime state, constructs `DMOOutput`, constructs `FMOOutput`, and returns both. The canonical state contract is a structured view over those current returned objects:

```text
Q_t = {
  identity: model_time, entity_id, model_version;
  current_state: state_level, state_velocity, state_acceleration,
    state_curvature, strength, coherence, persistence,
    perturbation_magnitude, perturbation_class, uncertainty,
    reversal_propensity, state_support_ratio,
    observation_half_life, forward_half_life;
  forward_state: forward_interval, forward_samples
}
```

Count: identity `3` + current state `14` + forward state `2` = **19 canonical top-level fields**. `forward_interval` is sourced from `FMOOutput.interval_length`; `forward_samples` is sourced from `FMOOutput.samples`.

## 5. Input isolation

| Source coordinate | Available at t | Allowed into D01 | Role |
|---|---:|---:|---|
| `event_timestamp_utc` | YES | YES | Event/receive time source |
| `close` | YES | YES | Current price |
| `volume` | YES | YES | Current activity input |
| `session_type` | YES | YES | Current session metadata |
| `data_valid` | YES | YES | Current validity/availability metadata |
| Constructed identity, sequence, quality, quote-unavailable, and availability masks | YES | YES | Deterministic adapter coordinates |
| Derived source columns | MAY EXIST | NO | Excluded by positive projection |
| Outcome/decision/vendor columns | MAY EXIST | NO | Excluded and prohibited |
| Future raw observations before reveal | NO | NO | Causal violation |
| Reserve rows/data | NO | NO | Sealed final-backtest evidence |

The adapter positively selects the five named source fields. Derived and outcome columns are not candidates for selection.

## 6. Separation counts

- Canonical `Q_t`: **19** top-level fields.
- Returned DMO diagnostics excluded from `Q_t`: **9**: `parameter_state`, `parameter_update_magnitude`, `data_quality`, `model_health`, `dmo_schema_version`, `fmo_schema_version`, `config_hash`, `state_hash`, `trace_id`.
- Stage 2 observer/evaluator concepts outside `Q_t`: **12**: realized displacement, slope, quadratic coefficient/curvature, path length, efficiency, normalized deviation, maximum signed progress, terminal signed progress, realized category, `T_valid`/censor state, realized ambiguity index, realized transition magnitude.
- Future/prohibited classes: **4**: future raw observations before reveal; outcome/benchmark labels; BUY/SELL/HOLD or vendor decisions; reserve data.

`RuntimeState`, snapshots, and `TraceRecord` contain additional internal/diagnostic coordinates. They are neither canonical `Q_t` fields nor members of the nine returned DMO diagnostics count.

## 7. Boundary conclusion

The architecture is ready to state an input interface, not to select a decision design. Stage 2 evidence restricts claims about `Q_t`; it does not turn observer quantities into inputs, alter D01, or authorize Stage 3 rules.

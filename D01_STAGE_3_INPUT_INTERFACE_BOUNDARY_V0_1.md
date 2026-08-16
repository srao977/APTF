# D01 Stage 3 Input Interface Boundary v0.1

## 1. Status

**Status:** INPUT INTERFACE BOUNDARY ONLY; STAGE 3 DESIGN NOT STARTED

This document defines no BUY/SELL/HOLD vocabulary, decision algorithm, threshold, horizon choice, position rule, cost, execution rule, benchmark, evaluator, or backtest procedure.

## 2. Interface

```text
Stage3Input_t = (Q_t, ExecutionContext_t)
```

`Q_t` is the exactly 19-field structured contract in `D01_QT_OUTPUT_CONTRACT_V0_1.md` and `D01_QT_OUTPUT_SCHEMA_V0_1.json`. All 19 fields are directly available after successful causal D01 emission at `t`; frozen Stage 2 evidence status constrains claims and does not change availability.

`ExecutionContext_t` is intentionally **undefined** at this boundary. A future design may define only nonpredictive operational context available at or before `t`, such as a causal clock, venue/session operability, or already committed system state. This possibility is not authorization for any particular field. It may not carry alternate market inference, future information, labels, recommendations, or reserve evidence.

## 3. Sole market-inference authority

D01 v0.2 is the sole market-state inference authority for the initial Stage 3 architecture. Stage 3 may receive the canonical `Q_t`; it may not introduce arbitrary indicators, technical studies, learned predictors, alternate models, vendor analytics, or transformed market features absent a future explicit architecture revision, causal specification, evidence plan, consistency review, and freeze.

This restriction does not predetermine which `Q_t` coordinates a future Stage 3 design may admit or how it may use them. Those are still-open design choices.

## 4. Causal input table

| Input class | Available at decision time t | Allowed in initial interface | Condition |
|---|---:|---:|---|
| Canonical `Q_t` identity fields (3) | YES | YES | Identity only |
| Canonical `Q_t` current-state fields (14) | YES | YES | Evidence status must travel with interpretation |
| Canonical `Q_t` forward-state fields (2) | YES | YES | Projections, not observed futures |
| Future nonpredictive `ExecutionContext_t` | POSSIBLE | UNDEFINED | Must be explicitly designed, causal, operational, and nonpredictive |
| DMO diagnostics excluded from `Q_t` (9) | Technically returned | NO | Initial Stage 3 interface must not consume without future explicit design justification |
| `RuntimeState`, snapshot, `TraceRecord` internals | Internal | NO | Diagnostic/internal, not interface state |
| Stage 2 observer/evaluator quantities (12) | NO at t | NO | Outcome-side evidence only after reveal |
| Future raw observations before reveal | NO | NO | Leakage |
| Outcome or benchmark labels | NO | NO | Evaluator-side only after commitment |
| BUY/SELL/HOLD, recommendations, vendor decisions | NO | NO | Prohibited alternate decision evidence |
| Reserve data | NO | NO | Sealed until complete executable-system freeze |

## 5. Diagnostic exclusion

The returned `DMOOutput` includes exactly nine fields outside canonical market state:

`parameter_state`, `parameter_update_magnitude`, `data_quality`, `model_health`, `dmo_schema_version`, `fmo_schema_version`, `config_hash`, `state_hash`, `trace_id`.

Their presence in the returned object does not make them Stage 3 inputs. The initial interface must not consume them. A future proposal would need field-specific semantic necessity, causal timing, non-leakage proof, evidence treatment, and a revised frozen contract.

## 6. Required ordering

```text
causal observation available at or before t
    -> frozen D01 v0.2 step
    -> immutable Q_t emission
    -> future Stage 3 processor using frozen Stage3Input_t
    -> immutable decision commitment
    -> future/outcome reveal
    -> evaluator and benchmark scoring
```

No future observation, outcome, benchmark, historical decision, or reserve field can cross left of commitment.

## 7. Evidence constraints

- Supported: `strength`, `perturbation_magnitude`, within narrow frozen semantic claims only.
- Limited/unresolved: `coherence`, `uncertainty`, `reversal_propensity`, `perturbation_class`, `observation_half_life`, `forward_half_life`, `forward_interval`.
- Unsupported under frozen Stage 2 semantics: State/Kinematics and `persistence`.
- Not independently tested: `state_support_ratio` and structured `forward_samples`.
- Not applicable: identity fields.

Direct availability is not empirical validation, predictive sufficiency, or trading validity.

## 8. Non-design declaration

No Stage 3 rules are selected here. Before implementation or reserve access, a separate future design must freeze admitted fields, evidence treatment, deterministic decisions, commitment timing, positions, execution, costs, benchmarks, outcomes, scoring, failure criteria, implementation, and tests.

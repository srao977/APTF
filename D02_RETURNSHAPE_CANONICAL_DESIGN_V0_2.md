# D02 ReturnShape Canonical Design v0.2

## 1. Purpose

D02 constructs a loss-minimizing causal representation of frozen D01 forward state for D04. It describes the geometry D01 emitted; it does not assert that future markets will realize that geometry.

**Status:** HUMAN-APPROVED DESIGN; FREEZE CANDIDATE; NOT IMPLEMENTED.

## 2. Architecture

```text
Signals -> frozen D01 -> Q_t/FMO -> deterministic D02 ReturnShape
  -> D04(ReturnShape, EnvelopeContext) -> D03 -> committed action
```

D01 owns market inference. D02 owns representation. D04 owns capturability and envelope behavior. D03 owns decisions/control.

## 3. Input authority

D02 accepts exactly the frozen 19-field Q_t defined by:

- `D01_QT_OUTPUT_CONTRACT_V0_1.md`;
- `D01_QT_OUTPUT_SCHEMA_V0_1.json`.

No returned DMO diagnostic, runtime internal, Stage 2 observer, future value, outcome label, recommendation, or reserve value is admissible.

## 4. Canonical output

The canonical output has 17 fields:

| Group | Fields |
|---|---|
| Identity/provenance | `model_time`, `entity_id`, `source_model_version` |
| Forward path authority | `current_level`, `projection_interval`, `forward_half_life`, `forward_samples` |
| Geometry views | `terminal_displacement`, `maximum_absolute_displacement`, `path_direction`, `terminal_decay_factor` |
| D01-aligned shape state | `strength`, `coherence`, `persistence`, `uncertainty`, `reversal_propensity`, `state_support_ratio` |

Exact types, units, ranges, formulas, evidence lineage, and failure behavior are normative in `D02_RETURNSHAPE_CANONICAL_SCHEMA_V0_2.json`.

## 5. FMO geometry

Let the current D01 level be $L_t$ and ordered FMO samples be $(\tau_j,\hat L_j,\hat V_j,\hat U_j,\hat S_j,\hat P_j,\hat R_j)$.

D01 already defines:

$$
\hat L_t(\tau)=L_t+V_t\tau+\frac{1}{2}A_t\tau^2
$$

and:

$$
d_t(\tau)=2^{-\tau/H_{f,t}}.
$$

Available deterministic geometry includes:

- signed displacement $\Delta_j=\hat L_j-L_t$;
- absolute displacement $|\Delta_j|$;
- terminal displacement $\Delta_T$ at maximum $\tau$;
- maximum excursion $\max_j|\Delta_j|$;
- path orientation from the sign of $\Delta_T$;
- segment slopes $(\hat L_j-\hat L_{j-1})/(\tau_j-\tau_{j-1})$, using $(0,L_t)$ as the anchor;
- projected velocity $\hat V_j$;
- projected level range $\max_j\hat L_j-\min_j\hat L_j$;
- temporal extent `projection_interval`;
- coordinate-wise decay $d_t(\tau_j)$;
- projected strength, persistence, uncertainty, and reversal propensity at each $\tau_j$.

The schema preserves the samples rather than selecting all possible scalar aggregations.

## 6. Deterministic transformations

Four convenience views are canonical:

$$
\text{terminal_displacement}=\hat L_T-L_t,
$$

$$
\text{maximum_absolute_displacement}=\max_j|\hat L_j-L_t|,
$$

$$
\text{path_direction}=\begin{cases}
\text{UPWARD}, & \Delta_T>0\\
\text{DOWNWARD}, & \Delta_T<0\\
\text{FLAT}, & \Delta_T=0,
\end{cases}
$$

and:

$$
\text{terminal_decay_factor}=2^{-\text{projection_interval}/\text{forward_half_life}}.
$$

These are reversible/checkable views over retained source fields and introduce no independent prediction.

## 7. Representation choices

- `path_direction` describes path orientation, not LONG/SHORT advice.
- `projection_interval` replaces overclaimed expected-lifetime language.
- `reversal_propensity` is retained without renaming it probability/risk.
- `state_support_ratio` is retained in its natural unbounded ratio form.
- no generic magnitude, quality, support, or decay attractiveness score is emitted.
- no untyped metadata extension is allowed.

## 8. Evidence lineage

| Coordinate family | Stage 2 lineage |
|---|---|
| Strength | SUPPORTED within narrow association claim |
| Coherence | PARTIALLY_SUPPORTED / unresolved |
| Uncertainty and reversal propensity | INCONCLUSIVE |
| Forward interval and forward half-life | INCONCLUSIVE; interval range warning retained |
| State/kinematics and derived displacement/direction | UNSUPPORTED under frozen Stage 2 semantics |
| Persistence | UNSUPPORTED |
| State support ratio | NOT independently tested |
| Full FMO list | NOT tested as a structured whole; component lineage applies |

Lineage is metadata only. It does not gate, alter, or weight D02 output.

## 9. Statefulness

D02 scientific behavior is stateless: each output is a pure function of current Q_t. The canonical ReturnShape identity is exactly `(entity_id, model_time)`. D02 emits no separate `return_shape_id`, shape version, or synthetic sequence. D04 may order and supersede shapes using monotonic `model_time` for each entity.

## 10. Adaptation policy

D02 is non-adaptive. It has no learned parameters, recursive estimator, outcome feedback, calibration, or parameter update. All adaptive market behavior remains inside frozen D01.

## 11. Causality

Every output is a direct Q_t/FMO coordinate or deterministic function of those coordinates. D02 may not access later observations, realized geometry, Stage 2 observer values, outcomes, decisions, benchmark labels, P&L, or reserve information.

## 12. Lifecycle

D02 emits a representation at `model_time`; it does not emit `active`. D04 owns supersession/staleness. The human-approved lifecycle rule is:

- a newer shape for the same entity supersedes the earlier shape;
- absent a newer shape, the latest shape remains projection-valid while `evaluation_time <= model_time + projection_interval`;
- the shape becomes stale only when `evaluation_time > model_time + projection_interval`.

The endpoint is inclusive. On context-only D04 reevaluation, D04 may use only the latest non-superseded shape while it remains projection-valid. Exact stale-state transitions/events are deferred to D04 modernization design. This is lifecycle policy, not market science or statistical expected lifetime.

## 13. Failure behavior

D02 emits no valid shape when:

- Q_t violates the frozen schema or causal sequence;
- a required scalar is missing/nonfinite/out of contract;
- forward samples are empty, malformed, unordered, or inconsistent with the projection interval;
- a derived view is nonfinite or fails recomputation;
- unknown, observer, future, outcome, reserve, candidate, execution, or diagnostic input is supplied.

It does not fill invalid values with neutral, zero, average, stale, or imputed values.

## 14. Numerical behavior

- Preserve source floats without quantization.
- Require strictly increasing finite `tau` values.
- Use the maximum-`tau` sample as terminal.
- Require terminal `tau == projection_interval` under the frozen generator contract.
- Compute geometry in deterministic sample order.
- Reject nonfinite derived values.
- Use exact-zero geometry: `FLAT` if and only if terminal displacement equals zero. D02 introduces no epsilon, materiality, volatility, price, learned, or calibrated tolerance.

## 15. Replay/live equivalence

Given identical Q_t, D02 emits identical output regardless of whether D01 received live events or causal replay events. D02 has no replay mode, wall-clock dependency, random source, external service, future buffer, or outcome branch.

## 16. D04 interface

D04 receives canonical ReturnShape separately from `EnvelopeContext`. D04 may compute capturability views from natural coordinates but must not mutate D02 or infer alternate market state. D04 owns candidate formation/identity, projection staleness/supersession, execution feasibility, capturability, aperture, hysteresis, envelope state, and envelope events. Candidate identity cannot alter D02 geometry.

The D04 prototype's shape-component formula requires controlled redesign because removed legacy scores have no canonical meaning. Feasibility gating, aperture, hysteresis, state transitions, and event architecture remain D04 responsibilities.

## 17. Prohibited behavior

D02 must not:

- predict independently or claim projected-path correctness;
- adapt, tune, learn, or select formulas from historical outcomes;
- create `shape_quality`, candidate reward/risk, capturability, or decisions;
- import candidate, execution, portfolio, position, or order context;
- inspect Stage 2 observers, future outcomes, or reserve data;
- compress away `forward_samples` merely for legacy compatibility.

## 18. Unresolved issues

All six D02-boundary issues are resolved by human review and recorded in `D02_HUMAN_DESIGN_DECISIONS_V0_2.md`. D04-specific choices about magnitude/support consumption and detailed stale-state response are intentionally deferred to D04 modernization design; they do not leave the D02 contract open.

## 19. Implementation boundary

This design authorizes no source code, runner, replay, D04 change, D03 change, adapter, or experiment. Successful consistency/hash validation may freeze these design artifacts only. D02 implementation remains a separate future task.

## 20. Review decision

The canonical D02 contract is human-approved and ready for final consistency validation and design freeze.

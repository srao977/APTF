# D02 Human Design Decisions v0.2

## 1. Authority and status

**Status:** HUMAN-APPROVED D02 DESIGN AUTHORITY; FREEZE CANDIDATE

This record closes the six reviewed D02/D04 boundary questions without changing D02 scientific intent. It authorizes design freeze after all consistency, schema, hash, and immutability gates pass. It does not authorize implementation.

## 2. R1 — Exact-zero path direction

`path_direction` is `UPWARD` when terminal displacement is positive, `DOWNWARD` when negative, and `FLAT` when exactly zero. D02 uses no epsilon, materiality, volatility, price, learned, or calibrated tolerance. Economic significance belongs to D04 capturability.

## 3. R2 — Preserve magnitude geometry

D02 preserves `terminal_displacement`, `maximum_absolute_displacement`, and complete `forward_samples`. It emits no normalized `magnitude_score` and does not select the geometry most relevant to capturability. **D02 boundary resolved; D04 consumption design deferred.**

## 4. R3 — Preserve natural support representation

D02 preserves natural, unbounded `state_support_ratio` and complete projected support coordinates in `forward_samples`. It emits no bounded `forward_support` score. **D02 boundary resolved; D04 consumption design deferred.**

## 5. P1 — Canonical identity

Canonical ReturnShape identity is `(entity_id, model_time)`. D02 emits no separate `return_shape_id`, shape version, or synthetic sequence. D04 may use monotonic model time for same-entity ordering and supersession. A future additional sequence requires concrete ambiguity and explicit review.

## 6. L1 — Lifecycle and staleness

A newer same-entity ReturnShape immediately supersedes the older shape. Without a newer shape, the latest shape remains projection-valid through the inclusive endpoint:

```text
evaluation_time <= model_time + projection_interval
```

It is stale only when:

```text
evaluation_time > model_time + projection_interval
```

D04 owns lifecycle and detailed stale-state response. `projection_interval` remains projection extent, not statistical expected lifetime.

## 7. O1 — Candidate ownership

`candidate_id` is not D02 output. D04 evaluates capturability, forms/identifies the capturable candidate, and passes candidate/envelope information downstream to D03. Candidate identity cannot alter D02 geometry. `candidate_rr` remains removed; any future reward/risk construct belongs to explicit downstream decision/control design.

## 8. Confirmed design decisions

- `shape_quality` remains removed to avoid redundant weighted compression.
- `magnitude_score` remains removed; natural geometry is preserved.
- `candidate_rr` remains removed.
- `reversal_propensity` retains exact D01 semantics and is not a probability.
- `projection_interval` is FMO temporal extent and is not expected lifetime.
- `terminal_decay_factor` is remaining D01 forward influence/relevance at the endpoint, not confidence, correctness, survival, or degradation probability.
- D02 is deterministic, non-adaptive, non-stochastic, scientifically stateless, and non-predictive as an independent model.
- For identical Q_t, D02 emits identical ReturnShape in causal replay and future feed operation.

## 9. Prohibitions

This record introduces no implementation, historical replay, parameter tuning, trading rule, outcome feedback, reserve access, D04 source change, or D03 change.

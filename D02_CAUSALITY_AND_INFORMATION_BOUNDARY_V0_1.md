# D02 Causality and Information Boundary v0.1

## 1. Status

**Status:** CAUSAL BOUNDARY DEFINED; OUTPUT MATHEMATICS NOT FREEZE-READY

This document constrains every future D02 design and implementation. It does not authorize implementation or historical replay.

## 2. Authorized input boundary

At causal event time $t$, D02 may consume only:

```text
D02Input_t = Q_t + D02ContractConfiguration
```

`Q_t` is the frozen 19-field contract emitted only after `D01V02Model.step(...)` succeeds. Configuration must be fixed, versioned, non-future, non-adaptive within D02, and limited to representation/interface behavior authorized by a reviewed D02 design.

The authorized Q_t groups are:

- identity: `model_time`, `entity_id`, `model_version`;
- current state: the fourteen frozen current-state fields;
- forward state: `forward_interval`, `forward_samples` with seven causal projected coordinates per sample.

## 3. Point-in-time proof

1. D01 validates causal sequence order before emission.
2. D01 uses the current normalized observation and prior runtime state only.
3. FMO samples are mathematical projections from that causal state, not observations from future rows.
4. D02 receives the completed Q_t only after the D01 step succeeds.
5. A deterministic D02 function cannot acquire future information unless an unauthorized input or hidden state is added.
6. Therefore every authorized D02 output is measurable with respect to information available at $t$.

Formally, with causal history $\mathcal F_t$:

$$
Q_t \in \mathcal F_t,\qquad C_{D02}\in\mathcal F_0,
$$

and an authorized deterministic transformation $g$ would satisfy:

$$
\operatorname{ReturnShape}_t=g(Q_t,C_{D02})\in\mathcal F_t.
$$

No currently unresolved formula is authorized merely by this proof.

## 4. Prohibited inputs

D02 must never consume, directly or through metadata, cache, configuration, feature selection, or initialization:

- future raw observations before chronological reveal;
- realized future prices or returns;
- Stage 2 realized-observer fields;
- realized displacement, slope, curvature, path length, efficiency, deviation, progress, category, validity/censor state, ambiguity, or transition magnitude;
- outcome labels, benchmark decisions, vendor BUY/SELL/HOLD fields, or historical outcome decisions;
- future P&L or performance metrics;
- reserve rows, reserve values, reserve summaries, or reserve-derived constants;
- D01 diagnostic/internal fields excluded from Q_t;
- D04 EnvelopeContext values as market-shape substitutes;
- D03 position, order, or execution state as market-shape substitutes.

## 5. Information-flow separation

```text
Authorized observations through t
  -> D01
  -> Q_t
  -> D02 ReturnShape
  -> D04(ReturnShape, EnvelopeContext_t)
  -> D03
```

`EnvelopeContext_t` travels independently to D04. Candidate/position/execution identity belongs to the control boundary and must not be smuggled into market-shape scores. Outcomes become visible only to an evaluator after a D03 decision is committed.

## 6. State and time policy

Scientific D02 transformation state is prohibited. A future implementation may retain only minimal protocol state needed for a monotonically increasing `ReturnShape.version`, keyed by a stable shape ID. Such state:

- must not alter shape mathematics;
- must be deterministic under the same causal input sequence;
- must be initialized explicitly;
- must serialize/restore for replay equivalence;
- must not use wall-clock time or future queue contents.

Expiration under context-only reevaluation remains an unresolved design issue because D04 may reevaluate without a new Q_t. It cannot be solved by consulting a future observation.

## 7. Replay and live equivalence

Given the same Q_t sequence, initial protocol state, and fixed D02 configuration, D02 must emit byte-equivalent semantic values and identical IDs/versions whether Q_t originates from live causal ingestion or historical causal replay. The production transformation must not know that later records exist on disk.

## 8. Leakage audit result

| Audit | Result |
|---|---|
| Stage 2 observer leakage | NONE FOUND in proposed boundary |
| Future outcome leakage | NONE FOUND |
| Reserve leakage | NONE FOUND |
| D01 diagnostics promoted | NONE |
| EnvelopeContext forced into D02 | NONE |
| Independent D02 inference | PROHIBITED |

No historical replay was executed, no reserve file was accessed, and no outcome decision column was inspected during this reconciliation.

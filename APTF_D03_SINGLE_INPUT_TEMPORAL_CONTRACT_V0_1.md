# APTF D03 Single-Input Temporal Contract V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

Entry point: `d03.v01.evaluate_decision(D03Input)`.

This audit does not execute or construct D03 context; it traces the current integration constructor and frozen contract statically.

## Input times

- `D03Input.d04_evaluation.evaluation_time = t`.
- `D03Input.d04_evaluation.return_shape_model_time = t`.
- Integration `DecisionContext.context_time = obs.event_time = t`.
- `position_source_return_shape_model_time` is position lineage and may refer to an earlier causal shape; it is not necessarily current $t$.

D03 validates `context_time >= evaluation_time`. It does not require equality generally. Equality to original $t$ is guaranteed by this integration caller, not the generic schema.

## DecisionRecord times

| Field | Target/current caller value | Source | Category | Wall clock? |
|---|---:|---|---|---|
| `decision_time` | 1664525760.0 | `context.context_time` | F copied from A | NO |
| `source_d04_evaluation_time` | 1664525760.0 | D04 output | F/A | NO |
| `source_d04_return_shape_model_time` | 1664525760.0 | D04 output/D02 | E/A | NO |
| `candidate_source_return_shape_model_time` | null for no candidate target | candidate lineage when applicable | E/A lineage | NO |

## Identities

- `source_d04_fingerprint`: SHA256 of complete D04 evaluation.
- `input_fingerprint`: SHA256 of D04 evaluation + DecisionContext.
- `decision_id`: entity + exact context time + rule version + input fingerprint.

These commit the immediate D03 inputs but do not restore the source/D01 identity dropped before D02. They prove a D03 record corresponds to a particular D04/context payload, not cryptographically to the original CSV row.

No `received_at`, `emitted_at`, or processing duration exists.

## Answers

- Original $t$ preserved: YES under current caller, in three fields.
- DecisionRecord recover original $t$: YES numerically.
- Exact InputObservation(t) provenance: PARTIALLY, due upstream identity discontinuity.
- D03 processing latency computable: NO.

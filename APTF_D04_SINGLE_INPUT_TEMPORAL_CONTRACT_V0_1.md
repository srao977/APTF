# APTF D04 Single-Input Temporal Contract V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

Entry point: `TradingEnvelope.process(return_shape, context)`.

## Input times

The current integration caller constructs:

- `ReturnShape.model_time = t = 1664525760.0` from D02.
- `EnvelopeContext.evaluation_time = obs.event_time = t` from the original observation.

`evaluation_time` is Category F causal evaluation time. In this caller it is copied from Category A; it is not captured from a wall clock.

## Output times

| Object/field | Target value | Provenance | Category | Original $t$? |
|---|---:|---|---|---|
| `EnvelopeEvaluation.evaluation_time` | 1664525760.0 | context evaluation time | F copied from A | YES |
| `EnvelopeEvaluation.return_shape_model_time` | 1664525760.0 | ReturnShape model time | E copied from A | YES |
| candidate `source_return_shape_model_time` | N/A: no candidate for target | ReturnShape model time when created | E/A lineage | Would be YES |
| candidate `qualified_at` | N/A: no candidate | context evaluation time | F | Would equal $t$ in this caller |
| candidate ID | N/A | entity + source model time + qualified-at | G | Would encode $t$ twice here |
| event `timestamp` | $t$ when runtime event wrapper is used | context evaluation time | F | YES, not wall clock |

D04 has no evaluation identity field. AuditLogger records ReturnShape identity `(entity_id, model_time)` and caller scenario time, but no receive/emit processing timestamps.

No `received_at`, `emitted_at`, or processing duration exists. D04 benchmark `perf_counter` is aggregate helper telemetry, not per-input contract telemetry.

## Answers

- D04 knows original $t$: YES in two output fields.
- Evaluation provably comes from exact source object: PARTIALLY; it preserves time/entity and derived state but not D01/source parent ID.
- Candidate lineage for target: N/A because target evaluation is CLOSED/no candidate.
- D04 processing latency computable: NO.

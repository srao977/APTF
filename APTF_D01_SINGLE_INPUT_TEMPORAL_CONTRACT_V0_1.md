# APTF D01 Single-Input Temporal Contract V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

Target: exactly one real `InputObservation(t)` at `2022-09-30T08:16:00Z`, epoch `1664525760.0`. Prior D01 state is prerequisite context, not another audit target.

## Input

Entry point: `d01.v02.model.D01V02Model.step(observation: NormalizedObservation)`.

`NormalizedObservation` fields are `entity_id`, `event_time`, `receive_time`, `sequence_id`, price/volume/quote fields, session, source quality, and availability mask.

| Field | Target value | Category | Semantics |
|---|---:|---|---|
| `event_time` | 1664525760.0 | A: market/event time | Parsed from timezone-aware source UTC string; authoritative $t$ |
| `receive_time` | 1664525760.0 | A in this mapper, not B/C | Mapper explicitly copies `event_time` because source has no receive/event separation; not wall-clock ingest/receive telemetry |
| `sequence_id` | 16 | G-like local sequence, not timestamp | Zero-based CSV row index; causal ordering input |

The source UTC/local strings are timezone-aware. The runtime float is normalized Unix epoch seconds and carries no timezone object.

No source observation ID, object creation time, ingest wall-clock, D01 received-at, or input trace ID exists.

## Output

D01 emits `(DMOOutput, FMOOutput)`.

- Both `model_time=obs.event_time=1664525760.0` (Category E, analytically named but exactly inherited from A).
- FMO `interval_length` and sample `tau` values are elapsed forward coordinates (Category E), not timestamps.
- `observation_half_life` and `forward_half_life` are elapsed-time parameters (Category E).
- DMO `trace_id="SPY:17"` is Category G, created from entity and D01 state sequence after increment.
- DMO `state_hash` is Category G, a hash of selected state-vector/half-life values; it excludes source row identity and event time.
- `TraceRecord.model_time=t` and `TraceRecord.sequence=17` are internal D01 trace facts.

No receive wall-clock, emit wall-clock, or processing duration is recorded.

## Answers

- Original $t$ preserved: YES, in DMO/FMO `model_time`.
- D01 output provably originated from this exact source object: PARTIALLY. Time/entity/sequence-derived trace align, but no immutable source observation ID/hash is carried.
- D01 processing latency computable: NO.

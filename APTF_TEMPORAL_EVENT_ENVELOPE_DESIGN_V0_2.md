# APTF Temporal Event Envelope Design V0.2

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Approved architecture

`TemporalEventEnvelope(metadata, payload=exact frozen object)` surrounds but never changes D01, D02, D04, D03, or PositionTransitionPlan semantics.

## Final field contract

| Field | Type | Nullable | Producer | Meaning / serialization |
|---|---|---:|---|---|
| `schema_version` | string `0.2` | NO | runtime | envelope version |
| `event_id` | content-addressed ID | NO | wrapper | deterministic logical event identity |
| `observation_id` | content-addressed ID | NO | source only, inherited | original normalized observation |
| `execution_id` | UUIDv4 text | NO | each wrapper occurrence | unique runtime attempt |
| `parent_event_id` | event ID | E0 only | wrapper | immediate logical parent; null E0 |
| `logical_output_ordinal` | integer >=0 | NO | wrapper | collision-safe logical child ordinal; 0 for E0-E5 primary outputs |
| `source_stream_id` | string | NO | source, inherited | ordering/identity stream scope |
| `sequence_number` | integer >=0 | NO | source, inherited | APTF Source-Gateway sequence in `(stream,instrument)` scope |
| `instrument_id` | string | NO | source, inherited | normalized instrument |
| `market_event_time_utc` | aware UTC text | NO | source, inherited | immutable provider event time |
| `market_event_time_role` | bounded enum | NO | source, inherited | `PROVIDER_EVENT` for audited stream |
| `producer_component` | enum | NO | wrapper | SOURCE/D01/D02/D04/D03/controller |
| `producer_version` | string | NO | wrapper | frozen producer version |
| `runtime_instance_id` | UUIDv4 text | NO | process startup | runtime occurrence scope |
| `clock_domain_id` | UUIDv4 text | NO | process startup | monotonic domain |
| `received_at_utc` | RFC3339 UTC | NO | wrapper | wall-clock receive |
| `emitted_at_utc` | RFC3339 UTC | NO | wrapper | wall-clock emit/error |
| `received_monotonic_ns` | integer/null | distributed null | wrapper | process-local start sample |
| `emitted_monotonic_ns` | integer/null | distributed null | wrapper | process-local end sample |
| `processing_duration_ns` | integer >=0 | NO | wrapper | authoritative local elapsed duration |
| `telemetry_flags` | bounded unique array | NO | wrapper | currently `WALL_CLOCK_INVERSION` only |
| `status` | SUCCESS/ERROR | NO | wrapper | math call status; independent of UTC inversion |
| `payload_type` | string | NO | adapter | frozen output type |
| `payload_version` | string | NO | adapter | frozen schema/version |
| `payload_sha256` | SHA256/null | ERROR null | serializer | canonical semantic payload digest |
| `scientific_ids` | scalar map | NO | adapter | copied existing IDs, no redefinition |
| `payload` | JSON value | ERROR null | frozen component | exact semantic output serialization |
| `error` | typed object/null | SUCCESS null | wrapper | stable type/code + sanitized message |

All fields are immutable once envelope construction completes. Machine authority: `APTF_TEMPORAL_EVENT_ENVELOPE_SCHEMA_V0_2.json`.

## Source event E0

Source Gateway receives the real normalized row, captures genuine current processing timestamps, assigns stream sequence 16 after normalization, canonicalizes the normalized source payload, creates deterministic observation/logical event IDs and UUIDv4 execution ID, and emits E0. It does not reuse frozen `NormalizedObservation.receive_time` as telemetry.

## Wrapper pattern E1-E5

1. Validate inherited observation ID, stream, sequence, instrument, market time/role, parent event.
2. Generate UUIDv4 execution ID.
3. Sample aware UTC and `perf_counter_ns()` receive.
4. Call exact frozen component.
5. Sample monotonic emit then aware UTC emit.
6. Compute duration and optional UTC inversion flag.
7. Serialize exact payload and hash it.
8. Compute deterministic event ID excluding telemetry/execution ID.
9. Return immutable child envelope.

Payloads: E1 `{dmo,fmo}`, E2 ReturnShape, E3 EnvelopeEvaluation, E4 DecisionRecord, E5 complete PositionTransitionPlan. Detached verbs are never terminal publications.

## Error event

A frozen call failure creates an ERROR child with same observation/time/stream/sequence, new UUID execution ID, deterministic logical error event ID based on stable error type/code (message excluded), complete telemetry, null payload/hash, and no fabricated output.

## UTC inversion

`WALL_CLOCK_INVERSION` is telemetry-only. SUCCESS remains SUCCESS; UTC fields remain raw; monotonic duration remains authoritative.

## One-observation structure

```text
O fixed, stream fixed, sequence=16, event time=2022-09-30T08:16:00Z, role=PROVIDER_EVENT
E0 parent=null -> E1 parent=E0 -> E2 parent=E1 -> E3 parent=E2 -> E4 parent=E3 -> E5 parent=E4
```

Every E has a distinct deterministic logical ID and unique execution UUID. Placeholder times only appear in design examples; implementation proof measures actual local telemetry.

## Required invariants

T01 time/role immutable; T02 observation ID immutable; T03 logical IDs deterministic/distinct; T04 parent chain complete; T05 UTC order expected and inversion flagged without invalidating math; T06 duration >=0; T07 same-domain monotonic subtraction only; T08 model/control times never telemetry; T09 terminal verbs only in E5 plan envelope; T10 payload behavior unchanged; T11 child inherits stream/sequence/instrument; T12 execution ID unique and excluded from logical IDs; T13 payload hash excludes envelope; T14 distributed raw monotonic null; T15 error output never fabricated; T16 Event Hubs metadata cannot overwrite envelope ordering/time.

## Azure compatibility

JSON-compatible values/IDs/times/durations survive Event Hubs. Suggested partition key is `instrument_id` or stable `(source_stream_id,instrument_id)` mapping. Event Hubs sequence/enqueue/offset remain separate transport properties. No Azure code/dependency is part of V0.2.

## Overhead goal

O(1) local timestamp/UUID/hash-envelope operations, no network/database call merely to timestamp, no synchronous remote dependency in frozen call path.

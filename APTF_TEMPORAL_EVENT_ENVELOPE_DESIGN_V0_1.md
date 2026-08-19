# APTF Temporal Event Envelope Design V0.1

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Decision

Use one external immutable `TemporalEventEnvelope` around each frozen payload. The envelope is runtime/transport metadata; the payload remains the exact scientific/control object produced by the existing component.

```text
TemporalEventEnvelope(metadata, payload=frozen object)
```

No frozen payload schema or mathematics needs a telemetry field.

## Envelope fields

| Field | Type | Nullable | Immutable | Producer | Meaning | Clock domain | Serialization |
|---|---|---:|---:|---|---|---|---|
| `schema_version` | string | NO | YES | envelope library | Envelope contract version | none | ASCII semantic version |
| `event_id` | content-addressed string | NO | YES | producing wrapper | Logical event identity | none | `aptf:evt:v1:sha256:<hex>` |
| `observation_id` | content-addressed string | NO | YES | Source Gateway only; inherited thereafter | Original normalized observation identity | none | `aptf:obs:v1:sha256:<hex>` |
| `parent_event_id` | event ID | source only | YES | producing wrapper | Immediate causal parent | none | null for source, ID otherwise |
| `sequence_number` | nonnegative integer | NO | YES | source adapter; inherited | Instrument-stream ordering supplement | none | JSON integer |
| `instrument_id` | string | NO | YES | source adapter; inherited | Normalized entity/instrument | none | UTF-8 JSON string |
| `market_event_time_utc` | UTC timestamp | NO | YES | source adapter; inherited | Authoritative immutable $t$ | source UTC | RFC 3339 UTC `Z` |
| `producer_component` | enum string | NO | YES | wrapper | Component creating this event | none | enum string |
| `producer_version` | string | NO | YES | wrapper config | Frozen producer version | none | UTF-8 string |
| `runtime_instance_id` | opaque string | NO | YES | worker startup | Worker/process-lifetime identity | runtime | UTF-8 string |
| `clock_domain_id` | opaque string | NO | YES | worker startup | Process-local monotonic domain | local monotonic | UTF-8 string |
| `received_at_utc` | UTC timestamp | NO | YES | wrapper | Wall-clock receive boundary | UTC wall clock | RFC 3339 UTC `Z` |
| `emitted_at_utc` | UTC timestamp | NO | YES | wrapper | Wall-clock output/error boundary | UTC wall clock | RFC 3339 UTC `Z` |
| `received_monotonic_ns` | integer | transport profile YES | YES | wrapper | Local high-resolution start sample | process-local | JSON integer locally; null on Event Hubs |
| `emitted_monotonic_ns` | integer | transport profile YES | YES | wrapper | Local high-resolution end sample | process-local | JSON integer locally; null on Event Hubs |
| `processing_duration_ns` | nonnegative integer | NO | YES | wrapper | Same-domain elapsed processing | duration | JSON integer |
| `status` | SUCCESS/ERROR | NO | YES | wrapper | Mathematical call outcome | none | enum string |
| `payload_type` | string | NO | YES | wrapper | Frozen payload type/aggregate | none | qualified type name |
| `payload_version` | string | NO | YES | wrapper | Frozen payload/schema version | none | version string |
| `payload_sha256` | lowercase SHA256 | ERROR may be null | YES | serializer | Canonical serialized payload digest | none | hex string |
| `scientific_ids` | object | NO | YES | wrapper adapter | Existing IDs copied for indexing | none | scalar JSON map |
| `payload` | JSON value | ERROR may be null | YES | frozen component + serializer | Unchanged semantic payload representation | none | canonical JSON-compatible value |
| `error` | typed object | SUCCESS null | YES | wrapper | Failure type/code/safe message | none | JSON object |

The authoritative machine-readable design is `APTF_TEMPORAL_EVENT_ENVELOPE_SCHEMA_V0_1.json`.

## Source/ingest envelope

The Source Gateway creates `observation_id` after normalization and before D01. Its `received_at_utc` is genuine APTF ingest; `emitted_at_utc` is normalized-source-event readiness/publication. Standard fields are sufficient, so no duplicate `ingested_at_utc` or `ingest_monotonic_ns` fields are introduced.

The frozen `NormalizedObservation.receive_time` is not reused. Historical code currently copies it from event time, and its semantics remain untouched inside the payload.

## Boundary wrapper pattern

For each component:

```text
receive parent envelope
validate immutable metadata
sample received UTC + local monotonic
extract exact frozen payload input
call frozen component
sample emitted local monotonic + UTC
serialize exact output payload
create child envelope with same observation_id and market_event_time
set parent_event_id to parent event_id
compute duration and deterministic event_id
return/publish child envelope
```

D01 output payload is an aggregate containing the real DMO/FMO pair. D02 payload is the real ReturnShape. D04 payload is the real EnvelopeEvaluation. D03 payload is the real DecisionRecord. Terminal payload is the complete real PositionTransitionPlan including its ordered semantic verbs; a detached verb is never the published terminal event.

## Single-observation structural walkthrough

No values below are measured or generated in this design task.

```text
O = <OBSERVATION_ID_FROM_IMMUTABLE_SOURCE_FACTS>
t = 2022-09-30T08:16:00Z

E0 SOURCE_GATEWAY
  event_id=<E0> parent=null observation_id=O market_event_time=t
  received_at=<SOURCE_RECEIVED_AT> emitted_at=<SOURCE_EMITTED_AT>
  duration_ns=<SOURCE_DURATION_NS> payload=NormalizedObservation(t)

E1 D01
  event_id=<E1> parent=<E0> observation_id=O market_event_time=t
  received_at=<D01_RECEIVED_AT> emitted_at=<D01_EMITTED_AT>
  duration_ns=<D01_DURATION_NS> payload=(DMO,FMO)

E2 D02
  event_id=<E2> parent=<E1> observation_id=O market_event_time=t
  received_at=<D02_RECEIVED_AT> emitted_at=<D02_EMITTED_AT>
  duration_ns=<D02_DURATION_NS> payload=ReturnShape

E3 D04
  event_id=<E3> parent=<E2> observation_id=O market_event_time=t
  received_at=<D04_RECEIVED_AT> emitted_at=<D04_EMITTED_AT>
  duration_ns=<D04_DURATION_NS> payload=EnvelopeEvaluation

E4 D03
  event_id=<E4> parent=<E3> observation_id=O market_event_time=t
  received_at=<D03_RECEIVED_AT> emitted_at=<D03_EMITTED_AT>
  duration_ns=<D03_DURATION_NS> payload=DecisionRecord

E5 POSITION_TRANSITION_CONTROLLER
  event_id=<E5> parent=<E4> observation_id=O market_event_time=t
  received_at=<PC_RECEIVED_AT> emitted_at=<PC_EMITTED_AT>
  duration_ns=<PC_DURATION_NS> payload=PositionTransitionPlan + verbs
```

Original $t$ is inherited and never regenerated.

## Error events

A wrapper that receives a parent but fails before mathematical output emits an ERROR child envelope with the same observation ID/market time, a new deterministic error event ID, parent ID, complete timing, `payload=null`, and typed `error_type`, stable `error_code`, and sanitized message. Errors may share the same stream/schema or route to a separate Event Hub later; the common envelope remains identical. Scientific output is never fabricated.

## Azure/Event Hubs compatibility

The envelope is JSON-compatible, versioned, payload-versioned, identity-stable, and uses UTC strings plus JSON integer durations. Event Hub metadata such as `enqueued_time_utc`, partition, offset, and sequence number remains transport metadata and must not overwrite envelope fields.

Suggested partition key: `instrument_id`. Consumers use `event_id` for idempotence and `(instrument_id, sequence_number)` for source order, with parent IDs for causal order.

## Formal invariants

- T01 `market_event_time_utc` is immutable end-to-end.
- T02 `observation_id` is immutable end-to-end.
- T03 every logical derived event has a unique deterministic `event_id`.
- T04 every non-source event has exactly one `parent_event_id`.
- T05 within one worker UTC clock, `received_at_utc <= emitted_at_utc`; violation is a telemetry fault, never repaired with model time.
- T06 `processing_duration_ns >= 0`.
- T07 duration derives only from monotonic samples sharing `clock_domain_id`.
- T08 model/evaluation/context/decision times never substitute for processing telemetry.
- T09 terminal semantic verbs are published only inside the complete envelope/plan payload.
- T10 telemetry does not change frozen payload values or call ordering.
- T11 child and parent share `observation_id` and `market_event_time_utc`.
- T12 event IDs and observation IDs exclude processing timestamps.
- T13 payload hash is computed from canonical semantic serialization, excluding envelope telemetry.
- T14 raw monotonic counters are null in distributed transport profile.
- T15 ERROR events never contain fabricated scientific payloads.

## Performance design goal

Identity/timestamp capture and envelope construction are $O(1)$ per event, require no network/database operation in the mathematical call path, and have no synchronous remote dependency. Publishing may be asynchronous downstream of envelope creation.

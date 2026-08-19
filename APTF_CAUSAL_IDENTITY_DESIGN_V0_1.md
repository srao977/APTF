# APTF Causal Identity Design V0.1

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Observation identity

`observation_id` answers: which immutable normalized source observation caused this event?

Creation point: exactly once at the Source Gateway after provider normalization has produced the immutable observation payload and before D01 is called.

Decision: deterministic content-addressed identity, represented as:

```text
aptf:obs:v1:sha256:<64 lowercase hex>
```

Canonical preimage (JCS/canonical JSON) contains only immutable source facts:

- identity schema/version;
- source/provider and source dataset/feed/partition identity;
- normalized `instrument_id`;
- authoritative `market_event_time_utc`;
- source-provided sequence/trade/message ID when available;
- canonical normalized observation payload digest.

No processing/ingest/receive/emission timestamp enters the identity. Determinism supports historical reproducibility, idempotent retries, and duplicate detection. If a provider has no sequence ID, the canonical normalized payload digest disambiguates source facts; exact duplicate source messages intentionally produce the same observation ID.

## Event identity

`event_id` answers: which logical derived event is this?

Decision: deterministic content-addressed identity:

```text
aptf:evt:v1:sha256:<64 lowercase hex>
```

Canonical preimage excludes telemetry timestamps and contains:

- event identity version;
- `observation_id`;
- `parent_event_id`;
- producer component/version;
- logical event role (`SOURCE`, primary output, or error);
- payload type/version;
- canonical payload SHA256, or stable error code/type for failure.

Identical retries of the same logical event retain one event ID. A changed payload, stage, parent, version, or status yields a different ID.

## Parent chain

```text
E0 SOURCE_GATEWAY parent=null observation=O
E1 D01           parent=E0   observation=O
E2 D02           parent=E1   observation=O
E3 D04           parent=E2   observation=O
E4 D03           parent=E3   observation=O
E5 POSITION...   parent=E4   observation=O
```

`observation_id=O` never changes. Each logical event has one unique `event_id`. A non-source event must have exactly one parent for this linear primary-output chain.

## Existing identities

Frozen scientific/control IDs remain payload semantics:

- D01 `trace_id`, `state_hash`, `config_hash`;
- D02 `(entity_id, model_time)` identity;
- D04 `candidate_id`;
- D03 `decision_id`, fingerprints;
- controller `transition_id` and originating D03 IDs.

The envelope's `scientific_ids` index may copy them without redefining them. `trace_id` is not `observation_id`.

## Ordering

The generic envelope includes `sequence_number`, inherited unchanged from the source event for all descendants. It is instrument-stream scoped and supplements event time/observation ID because equal timestamps and transport reordering are possible.

Ordering key is conceptually `(instrument_id, sequence_number)`. Event lineage order is separately represented by parent IDs. Sequence assignment belongs to the source adapter/provider contract and must be monotonic within its declared partition/instrument scope.

## Invariants

- O01: observation ID is assigned once and immutable.
- O02: event IDs exclude processing telemetry.
- O03: each non-source primary event has exactly one parent.
- O04: parent and child share observation ID.
- O05: source event parent is null.
- O06: scientific IDs retain their frozen meanings.
- O07: deterministic duplicates retain IDs; conflicting payload under one ID is invalid.

# APTF Temporal Telemetry Design Decision Point V0.1

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Decision

**DESIGN A: TELEMETRY CAN BE IMPLEMENTED AS AN EXTERNAL EVENT ENVELOPE WITHOUT MODIFYING FROZEN MATHEMATICAL PAYLOAD CONTRACTS.**

Repository evidence shows all stages expose callable boundaries and return complete payload objects. Event time already survives numerically. Missing processing telemetry and causal identity can therefore be added by orchestration wrappers before/after calls, while D01-D04-D03/controller files remain byte-identical.

## Direct answers

1. Entirely outside frozen payloads: YES.
2. D01 byte-identical: YES.
3. D02 byte-identical: YES.
4. D04 byte-identical: YES.
5. D03 byte-identical: YES.
6. Position Controller mathematical behavior byte-identical: YES.
7. Create observation ID once in Source Gateway after normalized immutable payload exists and before D01.
8. Observation ID: deterministic content-addressed source-fact identity.
9. Event ID: deterministic content-addressed logical-event identity excluding telemetry timestamps.
10. Raw monotonic values: process-local only; publish null values and `processing_duration_ns` across Azure boundaries.
11. Canonical UTC: RFC 3339/ISO-8601 UTC string ending `Z`, millisecond-or-finer display, highest practical runtime precision.
12. Canonical duration: nonnegative JSON/Python integer nanoseconds.
13. Minimum runtime metadata: opaque `runtime_instance_id` and `clock_domain_id`.
14. Event Hubs compatibility: YES, through JSON serialization and an external future publisher; no envelope redesign required.
15. Implementation files: only the new `aptf_runtime` package/schema/tests listed in the implementation plan; existing files NONE.

## Residual design constraints

- “Unchanged envelope” means same schema/semantics. The distributed serialization profile nulls process-local raw monotonic fields while retaining duration and clock-domain metadata.
- Deterministic event IDs identify logical events, so retries intentionally reuse IDs.
- UTC cross-worker elapsed measurements are approximate operational telemetry, not monotonic/nanosecond-accuracy measurements.
- A source provider/adapter must supply a monotonic instrument-stream sequence scope; the generic envelope does not invent market ordering.
- Azure Event Hub enqueue time remains broker/transport metadata, not envelope market time.

## Stop

No implementation, timestamp capture, identity generation, schema deployment, test, Azure dependency, or freeze was created. Human review is required before implementation.

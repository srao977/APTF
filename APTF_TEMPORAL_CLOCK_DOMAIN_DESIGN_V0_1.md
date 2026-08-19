# APTF Temporal Clock Domain Design V0.1

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Two required clock classes

### UTC wall clock

Purpose: cross-process/container/host correlation, Azure transport correlation, audit, and human timeline.

Canonical external representation: RFC 3339 / ISO-8601 UTC string ending in `Z`, with at least milliseconds and the highest practical runtime precision retained. Example shape: `2026-08-18T15:49:48.237412Z`. Naive datetimes and local-zone telemetry are forbidden.

Fields: `received_at_utc`, `emitted_at_utc`. For the source producer, `received_at_utc` is genuine APTF ingest; no separate `ingested_at_utc` is needed. `market_event_time_utc` remains the provider/source event time and is never replaced by either processing field.

UTC differences across workers are operational estimates subject to host synchronization, clock adjustment, scheduling, serialization, and transport uncertainty. They are not nanosecond-accuracy claims.

### Process-local monotonic clock

Purpose: elapsed duration inside one process/clock domain.

Recommended Python primitive for a future implementation: `time.perf_counter_ns()`. Canonical unit: integer nanoseconds.

$$
processing\_duration\_ns=emitted\_monotonic\_ns-received\_monotonic\_ns
$$

Nanosecond resolution does not imply nanosecond accuracy.

## Distribution rule

Raw monotonic values are meaningful only inside `clock_domain_id`. They must never be subtracted across runtime instances, processes, containers, VMs, or hosts.

Local/internal envelope profile:

- raw `received_monotonic_ns` and `emitted_monotonic_ns` may be retained;
- `clock_domain_id` and `runtime_instance_id` are mandatory.

Azure/distributed transport profile:

- set raw monotonic fields to `null` (or remove only under a future schema profile that explicitly permits omission);
- publish `processing_duration_ns`;
- publish UTC receive/emit values and clock/runtime IDs;
- never treat raw monotonic counters as globally comparable.

## Transport timing

Cross-service transport must not be computed as `D02.received_monotonic_ns - D01.emitted_monotonic_ns` unless both events explicitly share the same `clock_domain_id`.

Approximate distributed transport timing may use:

$$
D02.received\_at\_utc-D01.emitted\_at\_utc
$$

with documented synchronization limitations. Future Azure Event Hubs `enqueued_time_utc` is transport metadata, not `market_event_time_utc`; it can support producer-to-enqueue and enqueue-to-consumer operational segments.

## Total measurements

Local same-process proof: one outer monotonic clock domain may measure `aptf_processing_duration_ns = PC_emit_ns - D01_receive_ns` (or source receive to terminal emit if the selected boundary is explicit).

Distributed Azure: use UTC/transport segment timestamps for approximate end-to-end elapsed time. Sum of worker-local `processing_duration_ns` is valid as processing work, but it excludes and cannot reconstruct transport/queue time.

## Minimum clock-domain metadata

- `runtime_instance_id`: opaque identity for one worker/process lifetime.
- `clock_domain_id`: opaque identity for the monotonic domain, normally unique per process start.

Host/container/process numeric details are optional deployment logs, not required envelope fields. The two opaque IDs are sufficient to prevent cross-domain subtraction and support correlation.

## Historical versus live

Historical replay keeps `market_event_time_utc` equal to historical $t$. Processing UTC and duration fields describe the current replay execution, not historical latency and not future Azure live latency.

Future live source age may be estimated as source `received_at_utc - market_event_time_utc` only when both UTC clocks are compatible and uncertainty is acknowledged.

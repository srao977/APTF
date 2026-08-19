# APTF Temporal Clock Domain Design V0.2

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Event-time semantics

For `SPY_1min_firstratedata` the repository proves only that provider source `timestamp` is converted from assumed America/New_York local time to normalized UTC and used for causal ordering. It does not establish BAR_OPEN or BAR_CLOSE. Therefore:

```text
market_event_time_utc = 2022-09-30T08:16:00Z
market_event_time_role = PROVIDER_EVENT
```

The role is explicit per event because the current source-stream authority does not otherwise make it unambiguous. Original event time/role are inherited unchanged E0-E5.

Historical complete-bar availability is unknown. Historical `received_at_utc` is current proof/replay processing time, not historical availability. Future live Source Gateway receive UTC records actual APTF receipt. No provider publication/bar-close fields are invented.

## UTC processing clock

Implementation primitive: `datetime.now(timezone.utc)` (or injected equivalent), always aware UTC. Serialize RFC 3339 with `Z`, preserving Python microseconds and displaying at least milliseconds.

`received_at_utc <= emitted_at_utc` is expected, not authoritative duration validation. If UTC inversion occurs:

- scientific status/output remains SUCCESS if mathematics succeeded;
- retain both unmodified UTC values;
- add `WALL_CLOCK_INVERSION` to `telemetry_flags`;
- monotonic `processing_duration_ns` remains authoritative;
- never repair using model/evaluation/decision time.

## Monotonic duration clock

Implementation primitive: `time.perf_counter_ns()` through an injectable Clock protocol.

```text
processing_duration_ns = emitted_monotonic_ns - received_monotonic_ns
```

Both samples must come from one Clock instance and `clock_domain_id`. Duration is Python/JSON integer >= 0. Nanosecond resolution does not imply nanosecond accuracy.

The implementation API returns a stage sample pair from one clock object; envelope construction does not accept arbitrary mixed-domain samples without matching domain identity.

## Raw monotonic transport

Local profile carries raw counters. Distributed JSON/Event Hubs profile sets both raw fields to null and retains `processing_duration_ns`, `clock_domain_id`, and `runtime_instance_id`. Raw values are never globally comparable.

Cross-process monotonic subtraction is prohibited. Approximate cross-worker segments may use UTC values with explicit clock-skew limitations. Future Event Hubs `enqueued_time_utc`, partition, offset, and broker sequence remain transport metadata.

## Total latency

Same process: an outer monotonic sample pair can measure source/D01 receive to E5 emit in one domain.

Distributed: UTC/transport timestamps estimate end-to-end time. Sum of local durations measures component work only and excludes transport/queueing.

## Clock metadata

Minimum: UUIDv4 `runtime_instance_id` and UUIDv4 `clock_domain_id`. Host/container/process details remain deployment logs, avoiding envelope overdesign.

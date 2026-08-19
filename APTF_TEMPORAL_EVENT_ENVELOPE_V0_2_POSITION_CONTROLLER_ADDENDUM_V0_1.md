# APTF Temporal Event Envelope V0.2 Position Controller Addendum V0.1

Status: CURRENT SEMANTIC ADDENDUM
Date: 2026-08-18

## Scope

This additive clarification preserves all frozen Temporal Event Envelope V0.2 artifacts byte-identically. The original temporal design and implementation contain no field named `actual_position` and make no broker-position claim. No envelope, identity, clock, payload, schema, or version change is required.

## E5 Interpretation

E5 remains:

```text
producer_component = POSITION_TRANSITION_CONTROLLER
payload_type = PositionTransitionPlan
market_event_time_utc = t
```

Externally, E5 is the complete timestamped `POSITION CONTROLLER DECISION` event for observation t. The unchanged payload contains the internal transition class, source/controller state field, D03 position field, ordered semantic verbs, authorization, status, and D03 lineage.

The externally meaningful terminal pair is:

```text
D03 POSITION
POSITION CONTROLLER DECISION
```

Any payload field inherited from frozen controller terminology, including `source_position`, is internal transition-state provenance. It does not establish broker/account/executed position.

## Preserved Temporal Contract

The following remain unchanged:

- `market_event_time_utc` and role inheritance E0-E5;
- `observation_id`, deterministic `event_id`, unique `execution_id`, and parent lineage;
- aware UTC receive/emission timestamps;
- same-domain monotonic nanosecond duration;
- complete `PositionTransitionPlan` terminal payload;
- canonical payload hashing and error semantics;
- schema version 0.2 and all 28 fields.

The nanosecond telemetry implementation, including `time.perf_counter_ns()` sampling and `processing_duration_ns`, is unchanged.

`PositionControllerDecision(t)` therefore needs no external "Actual Position" concept to be a complete causal analytical event.

## Broker Boundary

Broker/execution position is outside the current APTF analytical Position Controller and temporal-envelope contract. No broker field, timestamp, reconciliation behavior, dependency, or integration is added.

# APTF Single-Observation Timestamp Implementation Plan V0.1

Status: DESIGN PLAN ONLY. NOT FROZEN IMPLEMENTATION AUTHORITY. NOT EXECUTED.

## Preferred package boundary

Add an independent package `aptf_runtime`. It imports and calls frozen components but is not imported by them. Frozen core files and package metadata remain byte-identical.

## Exact files expected to be added

```text
aptf_runtime/pyproject.toml
aptf_runtime/src/aptf_runtime/__init__.py
aptf_runtime/src/aptf_runtime/temporal_envelope.py
aptf_runtime/src/aptf_runtime/clock.py
aptf_runtime/src/aptf_runtime/identity.py
aptf_runtime/src/aptf_runtime/canonical_json.py
aptf_runtime/src/aptf_runtime/payload_serialization.py
aptf_runtime/src/aptf_runtime/stage_wrappers.py
aptf_runtime/src/aptf_runtime/single_observation_pipeline.py
aptf_runtime/schemas/temporal_event_envelope_v0_1.json
aptf_runtime/tests/test_temporal_envelope_schema.py
aptf_runtime/tests/test_clock_domain_rules.py
aptf_runtime/tests/test_causal_identity.py
aptf_runtime/tests/test_error_envelope.py
aptf_runtime/tests/test_single_observation_temporal_lineage.py
aptf_runtime/tests/test_frozen_payload_non_drift.py
```

## Existing files expected to change

NONE. A new CLI/diagnostic entry point belongs inside `aptf_runtime`; the existing replay harness remains untouched. If later production deployment requires registration in a repository-wide launcher that does not currently exist, that should be a separately reviewed non-frozen integration change.

## Frozen files expected byte-identical

- all D01 source/config/schema/freeze files;
- all D02 source/config/schema/freeze files;
- all D04 source/config/schema/freeze files;
- all D03 source/config/schema/freeze files;
- `position_transition_controller/position_transition_controller.py` and its frozen authorities;
- existing replay harnesses and outputs.

## Wrapper responsibilities

- `clock.py`: UTC-aware clock and monotonic-ns clock protocols/adapters; no use by frozen cores.
- `identity.py`: canonical deterministic observation/event IDs.
- `temporal_envelope.py`: immutable envelope/error types and invariant validation.
- `canonical_json.py`: JCS-compatible stable encoding/hashing.
- `payload_serialization.py`: side-effect-free adapters for dataclasses, enums, Pydantic models, DMO/FMO pair, and PositionTransitionPlan.
- `stage_wrappers.py`: receive/call/emit instrumentation around D01, D02, D04, D03, controller.
- `single_observation_pipeline.py`: linear E0-E5 orchestration and optional asynchronous publisher interface.

The payload object passed into each frozen call is the exact object extracted from its parent envelope; wrappers do not reconstruct scientific values except where the pre-existing integration contract already requires composing component inputs such as D04/D03 context.

## Future one-observation proof

Use exactly the authoritative observation at `2022-09-30T08:16:00Z`. Prior causal state may be established by a sealed fixture/snapshot or separately verified setup, but no second target is asserted.

The proof must verify:

1. one target observation only;
2. market event time remains exact at E0-E5;
3. one observation ID remains constant;
4. E0-E5 event IDs are distinct and deterministic;
5. parent chain is complete;
6. every component has UTC receive/emit and local monotonic samples;
7. every duration is nonnegative and equals same-domain subtraction;
8. cross-process monotonic subtraction is rejected;
9. payloads are field-for-field/canonical-hash identical to pre-telemetry baseline outputs;
10. terminal verbs exist only inside E5 plan envelope;
11. source/historical time differs semantically from current proof processing time;
12. no Azure dependency is required.

No implementation proof is run in this design phase.

## Non-drift validation commands for future phase

- hash all protected files before and after;
- run focused wrapper tests;
- run existing frozen component regression suites unchanged;
- compare canonical payload hashes with and without wrappers for the one target;
- assert no wrapper module appears in frozen component dependency imports;
- scan for event/model time substitution in telemetry fields.

## Azure boundary

Define a publisher protocol in `aptf_runtime`, with no Azure SDK dependency. A later adapter can serialize the same envelope to Event Hubs and attach partition/enqueue metadata externally. This preserves the envelope unchanged.

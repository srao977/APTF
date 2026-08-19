# APTF Temporal Event Envelope Implementation V0.2

Status: IMPLEMENTED / LOCAL RUNTIME CONTRACT
Date: 2026-08-18

## Scope

The implementation is isolated under `aptf_runtime`. It wraps exact frozen component calls and does not modify D01, D02, D04, D03, the Position Transition Controller, their schemas/configuration, existing harnesses, or historical outputs.

Implemented modules:

- `canonical_json.py`: APTF-CJSON-V1 semantic normalization and SHA256.
- `identity.py`: deterministic observation/logical-event identities and UUIDv4 runtime identities.
- `clock.py`: aware UTC correlation and same-domain `perf_counter_ns()` duration.
- `temporal_envelope.py`: immutable V0.2 envelope, inheritance validation, local/distributed serialization.
- `payload_serialization.py`: exact frozen-payload adapters and existing scientific-ID extraction.
- `stage_wrappers.py`: E0 source and E1-E5 success/error wrappers.
- `single_observation_pipeline.py`: one-target real SPY proof orchestration.

Machine schema: `aptf_runtime/schemas/temporal_event_envelope_v0_2.json`, byte-identical to the frozen V0.2 schema authority.

## Runtime Contract

Each occurrence creates a unique UUIDv4 `execution_id` before timing. Receive uses aware UTC plus a process-local monotonic sample. Emit samples monotonic first and UTC second. `processing_duration_ns` is the same-clock-domain subtraction. A UTC inversion retains the raw UTC values, adds `WALL_CLOCK_INVERSION`, and does not change successful mathematical output.

Logical `event_id` excludes execution and telemetry data. It includes observation identity, parent logical event, producer/version, logical ordinal, status, payload type/version/hash, and stable error type/code. Error messages are excluded. `observation_id` is created once from source identity and inherited E1-E5.

Local envelopes carry monotonic samples. Distributed serialization sets both raw monotonic values to null while retaining duration and clock/runtime domain identifiers. Nested payload and scientific-ID values are immutable after envelope construction.

## Frozen Invocation

The target pipeline calls, without modifying:

1. `D01V02Model.step`
2. `build_return_shape`
3. `TradingEnvelope.process`
4. `evaluate_decision`
5. `PositionTransitionController.derive_transition_plan`

Sixteen genuine prior normalized rows establish separate baseline and wrapped causal states. Only the real normalized SPY row at `2022-09-30T08:16:00Z` is the proof target. No later row is read. No mock or synthetic market observation is used.

## Result

Implementation checks, payload/state non-drift, 30/30 protected hashes, unchanged component regressions, focused runtime tests, terminal plan semantics, and static Azure compatibility all pass. No Azure package or runtime operation was introduced.

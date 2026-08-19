# APTF Temporal Telemetry Design Decision Point V0.2

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Decision

**DESIGN A: TELEMETRY CAN BE IMPLEMENTED AS AN EXTERNAL EVENT ENVELOPE WITHOUT MODIFYING FROZEN MATHEMATICAL PAYLOAD CONTRACTS.**

## Corrected decisions

- logical `event_id` and runtime UUIDv4 `execution_id` are separate;
- UTC inversion is a `WALL_CLOCK_INVERSION` flag, not mathematical failure;
- `source_stream_id` is required to scope APTF Source-Gateway `sequence_number`;
- target sequence is normalized sorted ordinal 16; source row 17 remains payload lineage;
- observation/event/payload hash recipes use explicit APTF-CJSON-V1 ordered preimages;
- source timestamp role is `PROVIDER_EVENT`, because repository authority does not establish bar open/close;
- raw monotonic counters are process-local and null in distributed transport;
- terminal event payload is complete PositionTransitionPlan.

## Core impact

D01, D02, D04, D03, controller, all existing package metadata, configs, schemas, harnesses, and outputs remain byte-identical. Only the new `aptf_runtime` package and new V0.2 evidence/freeze artifacts are authorized.

## Implementation gate

Implementation may begin only after Draft 2020-12 schema validation, complete artifact hash manifest, and creation of `APTF_TEMPORAL_EVENT_ENVELOPE_DESIGN_FREEZE_V0_2.json` with status `FROZEN_DESIGN`.

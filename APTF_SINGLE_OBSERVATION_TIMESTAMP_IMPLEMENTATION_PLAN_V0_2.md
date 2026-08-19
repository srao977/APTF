# APTF Single-Observation Timestamp Implementation Plan V0.2

Status: DESIGN PLAN ONLY. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Files to add

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
aptf_runtime/schemas/temporal_event_envelope_v0_2.json
aptf_runtime/tests/conftest.py
aptf_runtime/tests/test_temporal_envelope_schema.py
aptf_runtime/tests/test_clock_domain_rules.py
aptf_runtime/tests/test_causal_identity.py
aptf_runtime/tests/test_error_envelope.py
aptf_runtime/tests/test_payload_canonical_hashing.py
aptf_runtime/tests/test_terminal_plan_envelope.py
aptf_runtime/tests/test_single_observation_temporal_lineage.py
aptf_runtime/tests/test_frozen_payload_non_drift.py
```

Existing files to modify: NONE. Frozen cores, schemas, configs, harnesses, and outputs remain byte-identical.

## Responsibilities

- `clock.py`: aware UTC + monotonic clock protocol/SystemClock; same-domain sample API.
- `canonical_json.py`: APTF-CJSON-V1 normalization/serialization.
- `identity.py`: payload hash, observation/event recipes, UUIDv4 execution/runtime/clock IDs.
- `temporal_envelope.py`: immutable envelope/error/status/flag models and local/distributed serialization.
- `payload_serialization.py`: exact adapters for source row, DMO/FMO pair, dataclasses, Pydantic, enums, controller plan.
- `stage_wrappers.py`: generic stage measurement plus D01-E5 typed call adapters.
- `single_observation_pipeline.py`: source E0 and E1-E5 orchestration with fixed-context D04 and explicit D03/controller context only for the proof.

## One-observation proof

Use only the real target `2022-09-30T08:16:00Z`. Genuine preceding rows establish causal D01/D04 state but are setup, not target envelopes or proof table rows. The target creates only E0-E5.

For target source:

- role `PROVIDER_EVENT`;
- source stream ID frozen in design;
- sequence 16 from normalized sorted ordinal, not source row number 17;
- no future target/read beyond 08:16.

The proof compares wrapper payloads to unwrapped baseline outputs produced from separately initialized equivalent frozen component instances and the same target/setup. It proves canonical hash equality and field equality.

## Tests

Cover Draft schema, immutability, deterministic observation/event IDs, distinct source identity collision resistance, UUID execution uniqueness, sequence/stream semantics, UTC enforcement, same-domain duration, cross-domain rejection, UTC inversion flag, ERROR envelope, canonical payload hashing, terminal plan containment, one-observation lineage, and protected/payload non-drift.

Run focused package tests, then existing frozen regressions. No Azure SDK or resource operation.

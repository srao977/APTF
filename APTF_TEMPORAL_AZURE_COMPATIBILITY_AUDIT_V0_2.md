# APTF Temporal Azure Compatibility Audit V0.2

Status: STATIC REVIEW PASS
Date: 2026-08-18

No Azure implementation, SDK installation, resource operation, credential creation, deployment, broker integration, or live-data connection was performed.

The distributed envelope is JSON-compatible under the frozen Draft 2020-12 schema. `as_dict(distributed=True)` sets process-local monotonic receive/emit counters to null and retains:

- `processing_duration_ns`
- aware RFC3339 UTC receive/emit timestamps
- `observation_id`
- deterministic logical `event_id`
- unique `execution_id`
- `parent_event_id`
- `source_stream_id`
- `sequence_number`
- `runtime_instance_id` and `clock_domain_id`
- payload and canonical payload hash

Schema validation passes for both local and distributed profiles. Raw monotonic values are never globally compared. Event Hubs enqueue time, partition, offset, and broker sequence are future transport metadata and cannot overwrite envelope event time, source sequence, or identity.

A static scan of `aptf_runtime` found no Azure/Event Hubs import or dependency. `pyproject.toml` contains only the existing runtime dependency on Pydantic and optional test dependencies on pytest/jsonschema.

Conclusion: compatible as a future Event Hubs message contract, with transport design and implementation explicitly deferred.

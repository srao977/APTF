# APTF Temporal Telemetry Non-Drift Plan V0.2

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Protected boundary

`aptf_runtime` imports/calls frozen packages; frozen packages never import it. No existing file changes are authorized.

Protected behavior: D01 state/math/times/IDs; D02 geometry/identity; D04 context/math/hysteresis/candidates; D03 policy/fingerprints; controller verbs/authorization/identity; all schemas/configs/harnesses/outputs.

## Required checks

1. Capture pre/post SHA256 inventory of authorities, implementation files, configs, schemas, harnesses, and historical outputs.
2. For one target, compare unwrapped and wrapped E1-E5 payloads field-for-field.
3. Compare APTF-CJSON-V1 payload hashes.
4. Compare D01/D04 state snapshots after equivalent setup/target processing.
5. Verify scientific IDs unchanged and absent from envelope identity preimages except as payload hash content.
6. Verify exception type preserved locally and ERROR envelope adds no scientific payload.
7. Run existing component regressions unchanged.
8. Scan frozen imports for `aptf_runtime` (must be zero).
9. Verify no Azure package/dependency.
10. Verify no second target or full replay output.

## UTC anomaly non-drift

UTC inversion adds only `WALL_CLOCK_INVERSION`; it cannot alter SUCCESS, payload, payload hash, logical event ID, or monotonic duration.

## Retry non-drift

Retry of same logical payload/parent retains observation/event/payload IDs and creates a new execution UUID/timing. Payload must remain equal.

## Performance constraint

O(1) metadata per event; no remote call/database write in mathematical call path. No latency/accuracy benchmark claim in this task.

## Freeze rule

Implementation freeze is allowed only after all G01-G22 pass and protected hashes match. Existing freezes are never modified.

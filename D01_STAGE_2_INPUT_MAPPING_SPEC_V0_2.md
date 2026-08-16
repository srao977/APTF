# D01 Stage 2 Input Mapping Specification v0.2

**AUTHORITATIVE SOURCE:**  
`D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`

**IN CASE OF CONFLICT, THE FROZEN DESIGN V0.2 CONTROLS.**

This document is a canonical implementation-facing extract of approved Design v0.2. It does not create independent scientific authority.

## 6. Frozen Historical Input Mapping

The replay adapter uses the minimum raw causal input required by frozen D01.

| Historical field | D01 input | Transformation | Causal? | Frozen-contract authority | Status | Reason |
|---|---|---|---|---|---|---|
| constant `SPY` | `entity_id` | literal string | Yes | entity-local topology/observation contract | INCLUDED | One frozen D01 trajectory |
| `event_timestamp_utc` | `event_time` | UTC epoch seconds | Yes | causal timestamp contract | INCLUDED | Canonical ordering and elapsed time |
| `event_timestamp_utc` | `receive_time` | same epoch seconds; historical availability proxy | Yes | receive-time field exists; source lacks receipt timestamp | INCLUDED | Deterministic replay proxy, not latency evidence |
| canonical sorted row ordinal | `sequence_id` | contiguous one-based integer | Yes | monotonic sequence contract | INCLUDED | Deterministic causal ordering |
| `close` | `price` | numeric identity | Yes | required price input | INCLUDED | Minimum raw price observation |
| `volume` | `volume` | numeric identity | Yes | required volume input | INCLUDED | Frozen volume mechanism |
| `session_type` | `session` | identity label | Yes | optional session field | INCLUDED | Traceability; current frozen math does not consume direction from it |
| `data_valid` | `source_quality` | `true -> 1.0`; invalid required row not admitted | Yes | source-quality and no-fabrication contract | INCLUDED | Avoid invented graded quality |
| parseability metadata | `availability_mask.price/volume` | true iff required value available | Yes | availability-mask contract | INCLUDED | Missing is not zero |
| absent quote fields | bid/ask/sizes and mask | `None`; availability false | Yes | optional quote contract | INCLUDED AS MISSING | No fabrication |
| `open`, `high`, `low` | none | none | Yes | not required by frozen minimum interface | EXCLUDED | Avoid expanding frozen input |
| returns/ranges/change columns | none | none | Some causal, but not required | no frozen requirement | EXCLUDED | No engineered predictor input |
| minute/source/quality text fields | trace metadata only | none | Yes | traceability only | EXCLUDED FROM D01 | Audit context, not model input |

If required close or volume is unavailable, no D01 observation is fabricated. The row is recorded as unavailable and the next accepted event preserves actual elapsed time. No interpolation or forward fill is permitted.
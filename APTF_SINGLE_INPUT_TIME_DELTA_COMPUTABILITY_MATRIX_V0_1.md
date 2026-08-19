# APTF Single-Input Time-Delta Computability Matrix V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

No processing timers were added or run. `model_time`, `evaluation_time`, `context_time`, and `decision_time` are causal event/control coordinates in this caller, not measured component wall-clock times.

| Delta | Required start | Required end | Start exists? | End exists? | Same clock domain? | Computable? | Notes |
|---|---|---|---|---|---|---|---|
| ingest -> D01 receive | `T_ingest` | `T_D01_receive` | NO | NO | N/A | NOT COMPUTABLE | D01 `receive_time=t` is historical event-time proxy, not either field |
| D01 receive -> emit | `T_D01_receive` | `T_D01_emit` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D01 emit -> D02 receive | `T_D01_emit` | `T_D02_receive` | NO | NO | N/A | NOT COMPUTABLE | direct synchronous call does not record boundaries |
| D02 receive -> emit | `T_D02_receive` | `T_D02_emit` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D02 emit -> D04 receive | `T_D02_emit` | `T_D04_receive` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D04 receive -> emit | `T_D04_receive` | `T_D04_emit` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D04 emit -> D03 receive | `T_D04_emit` | `T_D03_receive` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D03 receive -> emit | `T_D03_receive` | `T_D03_emit` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D03 emit -> PC receive | `T_D03_emit` | `T_PC_receive` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| PC receive -> emit | `T_PC_receive` | `T_PC_emit` | NO | NO | N/A | NOT COMPUTABLE | no per-call telemetry |
| D01 receive -> PC emit | `T_D01_receive` | `T_PC_emit` | NO | NO | N/A | NOT COMPUTABLE | total APTF latency absent |
| ingest -> PC emit | `T_ingest` | `T_PC_emit` | NO | NO | N/A | NOT COMPUTABLE | source-to-output latency absent |

D04's standalone benchmark `perf_counter` measures aggregate helper execution around a loop; it is not stored in any single-input component contract and cannot supply these fields.

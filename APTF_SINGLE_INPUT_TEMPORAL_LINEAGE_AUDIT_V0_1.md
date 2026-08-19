# APTF Single-Input Temporal Lineage Audit V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Scope and authority

Exactly one target observation is audited:

```text
InputObservation(t)
t = 2022-09-30T08:16:00Z = 1664525760.0 epoch seconds
open/high/low/close = 366.00/366.00/366.00/366.00
volume = 616
source_row_number = 17
```

Prior causal state is treated only as a processing prerequisite. No second target, replay, benchmark, or backtest was run.

| Component | Version | Authority | SHA256 | Result |
|---|---|---|---|---|
| D01 | v0.2 / pre-Stage-3 freeze v0.1 | `D01_PRE_STAGE_3_ARCHITECTURE_FREEZE_V0_1.json` | `b6ed942e41ec1c72350cf9247597e5819a942dbe9d04770c23e243204165b235` | PASS |
| D02 | v0.2 | `D02_RETURNSHAPE_IMPLEMENTATION_V0_2_FREEZE.json` | `c8029c4b9608547bbf7960f05e4f8613480c4fb2bf8594d94482516b954f7e72` | PASS |
| D04 | v0.2.1 | `D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json` | `f72a86b3085bd11d8626f06f1fe3faedde60570365488176011239382a46f1af` | PASS |
| D03 | v0.1 | `D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json` | `6a93291ffe555a3fff1239a9a4f88c0a1546b6c46a02b60586614b60a3c91ad6` | PASS |
| Position Controller | v0.1 | `position_transition_controller/APTF_POSITION_TRANSITION_CONTROLLER_IMPLEMENTATION_V0_1_FREEZE.json` | `7c4f7ddc616a28090d3698634d67e4a6d71d4ef58744e9dee6c9cc5b06714bc2` | PASS |

Relevant design/config authorities include the D01 Q_t contract, D02 canonical design/schema, D04 modernization/candidate contracts and default YAML, D03 design/table/input inventory, and Position Transition Plan schema/controller design.

## Primary one-input lineage table

This is the sole primary lineage table. “Available” means the object contains $t$ or the current constructor provably copies $t$ into the named field. No field in `RECEIVED_AT`/`EMITTED_AT` is inferred from model/control time.

| Stage | Object type | Original $t$ available? | Field carrying $t$ | Local model/evaluation time | RECEIVED_AT | EMITTED_AT | Causal/trace ID | Parent ID | Lineage to InputObservation(t) provable? |
|---|---|---|---|---|---|---|---|---|---|
| InputObservation(t) | source CSV record | YES | `event_timestamp_utc` | none | none; availability absent | none | `source_row_number=17` only | none | YES at source |
| D01 input | `NormalizedObservation` | YES | `event_time=1664525760.0` | `receive_time=t` is a source proxy, not processing time | NONE | NONE | `sequence_id=16`; no trace ID yet | source ID not carried | PARTIAL |
| D01 output | `(DMOOutput,FMOOutput)` | YES | both `model_time=t` | model time $t$; interval/taus/half-lives are elapsed analytical coordinates | NONE | NONE | DMO `trace_id=SPY:17`, `state_hash`; FMO none | no source observation ID | PARTIAL |
| D02 output | `ReturnShape` | YES | `model_time=t` | projection interval 67.3155665570578; half-life 15.0; sample taus | NONE | NONE | canonical `(SPY,t)` only | D01 trace/hash dropped | PARTIAL; first ID discontinuity |
| D04 input | `(ReturnShape,EnvelopeContext)` | YES | shape `model_time=t`; context `evaluation_time=t` | D02 model time and caller evaluation time | NONE | NONE | ReturnShape `(SPY,t)` | no immutable D01 parent | PARTIAL |
| D04 output | `EnvelopeEvaluation` | YES | `evaluation_time=t`, `return_shape_model_time=t` | F/E times both equal $t$ in current caller | NONE | NONE | no evaluation ID; candidate ID N/A for CLOSED target | ReturnShape time/entity only | PARTIAL |
| D03 input | `D03Input(EnvelopeEvaluation,DecisionContext)` | YES | D04 two fields + `context_time=t` | context/evaluation/model coordinates | NONE | NONE | no D03 ID until evaluation | D04 object embedded, no D04 ID | PARTIAL |
| D03 output | `DecisionRecord` | YES | `decision_time=t`, `source_d04_evaluation_time=t`, `source_d04_return_shape_model_time=t` | all causal/control coordinates, not wall clock | NONE | NONE | `decision_id`, `input_fingerprint`, `source_d04_fingerprint` | immediate D04/context payload hashed | PARTIAL |
| Position Controller input | D03 dict + actual snapshot + supplied hash | YES | D03 `decision_time=t` and source times in complete dict | D03 causal time | NONE | NONE | D03 ID/hash, actual identity/version | D03 record | PARTIAL |
| Position Controller output | `PositionTransitionPlan` | YES | `decision_time=t` | copied D03 decision time | NONE | NONE | `transition_id`, originating D03 ID/hash | D03 parent preserved | PARTIAL; detached verb loses fields |

## Existing temporal-field semantics

| Field | Component | Value for InputObservation(t) | Created where | Category | Original $t$? | Wall-clock processing time? | Inherited? | Survives downstream? |
|---|---|---:|---|---|---|---|---|---|
| `event_timestamp_utc` | source | 2022-09-30T08:16:00Z | normalized source | A | YES | NO | source | parsed into D01 |
| `event_timestamp_local` | source | 2022-09-30T04:16:00-04:00 | source | A | YES, alternate zone | NO | source | dropped by mapper |
| `timezone` | source | America/New_York | source | A metadata | supports $t$ | NO | source | dropped |
| `event_time` | D01 input | 1664525760.0 | source mapper | A | YES | NO | parsed UTC | becomes model time |
| `receive_time` | D01 input | 1664525760.0 | mapper copies event time | A proxy, not B/C | duplicate of $t$ | NO | derived from event time | dropped by D01 output |
| DMO/FMO `model_time` | D01 output | 1664525760.0 | D01 assigns observation event time | E inheriting A | YES | NO | YES | D02 receives |
| `observation_half_life` | D01 DMO | 15.0 | D01 state update | E duration | NO | NO | analytical | copied only where selected; not t |
| `forward_half_life` | D01/D02 | 15.0 | D01 state | E duration | NO | NO | YES | ReturnShape |
| FMO `interval_length` | D01 FMO | 67.3155665570578 | D01 forward logic | E duration | NO | NO | analytical | D02 projection interval |
| FMO/sample `tau` | D01/D02 | offsets ending 67.3155665570578 | D01 forward samples | E offsets | NO | NO | YES | ReturnShape samples |
| ReturnShape `model_time` | D02 | 1664525760.0 | direct DMO copy | E inheriting A | YES | NO | YES | D04/source lineage |
| `projection_interval` | D02 | 67.3155665570578 | FMO interval copy | E duration | NO | NO | YES | D04 lifecycle |
| `terminal_decay_factor` | D02 | derived | interval/half-life formula | E dimensionless decay | NO | NO | derived | D04 diagnostic |
| `evaluation_time` | D04 context/output | 1664525760.0 | current caller copies observation event time | F inheriting A | YES | NO | YES | D03 D04 object/source field |
| `return_shape_model_time` | D04 output | 1664525760.0 | ReturnShape copy | E inheriting A | YES | NO | YES | D03 source field |
| `qualified_at` | D04 candidate | N/A: no candidate | context evaluation time when candidate created | F | would equal $t$ here | NO | caller time | candidate/D03 lineage when present |
| candidate `source_return_shape_model_time` | D04 candidate | N/A | ReturnShape model time | E inheriting A | would be YES | NO | YES | D03 when candidate-causing |
| event `timestamp` | D04 runtime event | $t$ when emitted | context evaluation time | F inheriting A | YES | NO | YES | event bus only |
| `context_time` | D03 context | 1664525760.0 | current caller copies observation event time | F inheriting A | YES | NO | YES | decision time |
| `position_source_return_shape_model_time` | D03 context | null for FLAT target state in relevant ordinary context | external position lineage | E historical lineage | not current $t$ necessarily | NO | external | fingerprint only |
| `decision_time` | D03 record / PC plan | 1664525760.0 | D03 copies context time; PC copies D03 | F inheriting A | YES | NO | YES | terminal plan |
| `source_d04_evaluation_time` | D03 record | 1664525760.0 | D04 evaluation copy | F inheriting A | YES | NO | YES | complete D03 input to PC, dropped from plan |
| `source_d04_return_shape_model_time` | D03 record | 1664525760.0 | D04 source time copy | E inheriting A | YES | NO | YES | complete D03 input to PC, dropped from plan |
| `candidate_source_return_shape_model_time` | D03 record | null for no candidate | target lineage | E | N/A | NO | candidate | plan does not retain separately |

## Processing-time inventory for this one input

| Required processing timestamp | Exists? | Evidence |
|---|---|---|
| `T_ingest` | NO | source has event timestamps only; D01 receive proxy equals event time |
| `T_D01_receive`, `T_D01_emit` | NO / NO | no fields or clock capture in `step` |
| `T_D02_receive`, `T_D02_emit` | NO / NO | no fields or clock capture in builder |
| `T_D04_receive`, `T_D04_emit` | NO / NO | no fields or clock capture in `process` |
| `T_D03_receive`, `T_D03_emit` | NO / NO | no fields or clock capture in evaluator |
| `T_PC_receive`, `T_PC_emit` | NO / NO | no fields or clock capture in controller |

## First discontinuities

| Concern | First discontinuity | Exact evidence |
|---|---|---|
| Original event time $t$ | NONE in current integration | copied through model/evaluation/context/decision/plan time fields |
| Immutable causal identity | D01 -> D02 output | D01 trace/state/source sequence not represented in ReturnShape |
| Receive-time telemetry | source mapper -> D01 entry | no actual ingest or D01 receive clock; `receive_time=t` is explicit proxy |
| Emit-time telemetry | D01 output | output has model time but no wall-clock emitted-at |

## Direct answers

1. Original $t$ field: source `event_timestamp_utc`; runtime `NormalizedObservation.event_time`.
2. D01 preserves $t$: YES.
3. D02 preserves $t$: YES.
4. D04 preserves $t$: YES under current caller.
5. D03 preserves $t$: YES under current caller.
6. Controller plan preserves/recover $t$: YES through `decision_time`.
7. Terminal verb exact source proof: PARTIALLY.
8. Full immutable causal ID: NO.
9. Component latency computable: NO.
10. Total APTF latency computable: NO.
11. First losses: event time NONE; identity D01->D02; receive source->D01; emit D01 output.

## Result

**RESULT B: FOR ONE InputObservation(t), EVENT-TIME LINEAGE IS COMPLETE BUT PROCESSING-TIME TELEMETRY IS INCOMPLETE.**

# APTF Temporal Telemetry Decision Point V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Classification

**RESULT B: FOR ONE InputObservation(t), EVENT-TIME LINEAGE IS COMPLETE BUT PROCESSING-TIME TELEMETRY IS INCOMPLETE.**

## Evidence

The current integration copies the single source event time through:

```text
source event_timestamp_utc
 -> NormalizedObservation.event_time
 -> DMOOutput/FMOOutput.model_time
 -> ReturnShape.model_time
 -> EnvelopeEvaluation.return_shape_model_time and evaluation_time
 -> DecisionRecord.source times and decision_time
 -> PositionTransitionPlan.decision_time
```

All target values are `2022-09-30T08:16:00Z` / epoch `1664525760.0`. Downstream names are model/evaluation/control fields, not newly sampled processing times.

No component records per-input receive wall-clock, emit wall-clock, or duration. Market ingest/availability time is also absent: historical `receive_time` is copied from event time.

## Discontinuities

- Original event time: NONE under the current integration caller.
- Immutable causal identity: D01 -> D02 output.
- Receive-time telemetry: first absent at source mapper/D01 entry; no `T_ingest` or actual `T_D01_receive`.
- Emit-time telemetry: first absent at D01 output; no `T_D01_emit`.

## Direct answers

1. Original $t$: source `event_timestamp_utc`, runtime `NormalizedObservation.event_time`.
2. D01 preserves $t$: YES, `model_time`.
3. D02 preserves $t$: YES, `ReturnShape.model_time`.
4. D04 preserves $t$: YES, `evaluation_time` and `return_shape_model_time` under current caller.
5. D03 preserves $t$: YES, `decision_time` and both source times under current caller.
6. Controller plan preserves/recover $t$: YES, `decision_time`.
7. Terminal verb proven from exact InputObservation(t): PARTIALLY; traceable in plan/output container, not detached verb or immutable source ID.
8. One immutable end-to-end causal ID: NO.
9. Actual component processing latency: NO.
10. Total APTF processing latency: NO.
11. First losses: event time NONE; identity D01->D02; receive telemetry source->D01; emit telemetry D01 output.

No implementation recommendation is made.

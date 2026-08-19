# APTF Causal Pipeline Integration Path Audit v0.1

## Declared versus actual path

The harness docstring claims row-by-row D01 -> D02 -> D04 -> D03 processing. The executable path is instead:

```text
csv.DictReader row
  -> CausalReplayHarness.process_row_to_d03
  -> hard-coded row_index < 100 gate
  -> hard-coded close/volume heuristic
  -> fabricated seven-field dictionary
  -> PositionTransitionController.derive_transition_plan
  -> emit only when plan.action_authorized
```

No import or call to `NormalizedObservation`, `D01V02Model`, `build_return_shape`, `TradingEnvelope`, `EnvelopeContext`, `D03Input`, `DecisionContext`, or `evaluate_decision` exists in the harness.

## Required frozen path and exact entry points

| Boundary | Frozen symbol | Input | Output | Relevant failure/gate |
|---|---|---|---|---|
| mapping | `d01.v02.observations.NormalizedObservation` | causal timestamp, sequence, close/volume mapping | typed observation | malformed/unavailable required fields |
| D01 | `D01V02Model.step` | NormalizedObservation | DMOOutput + FMOOutput | causal sequence or numerical/schema failure |
| D02 | `build_return_shape` | DMOOutput + FMOOutput | immutable ReturnShape | type, identity, finite/range/sample validation |
| D04 | `TradingEnvelope.process` | ReturnShape + EnvelopeContext | EnvelopeEvaluation | entity/time failure or safety-closed factual evaluation |
| D03 | `evaluate_decision` | D03Input(EnvelopeEvaluation, DecisionContext) | immutable 21-field DecisionRecord | invalid input rejected; valid NO_CHANGE/BLOCKED still committed |
| controller | `derive_transition_plan` | complete committed DecisionRecord/hash + ActualPosition | PositionTransitionPlan | stale/malformed/inconsistent input rejection |

## Integration findings

- D01 invocations: 0.
- D02 invocations: 0.
- D04 invocations: 0.
- Real D03 invocations: 0.
- The mock desired position is LONG iff `close > 400.0 AND volume > 1000`, otherwise FLAT.
- Decision time is the row index, not causal event time.
- Decision identity and hash are fabricated constants/strings.
- The dictionary omits 14 of the frozen D03 DecisionRecord's 21 fields.
- No D01/D02/D04 lineage can exist for the single BUY.

**FULL FROZEN PIPELINE ACTUALLY EXECUTED: NO.**

## Partition finding

The frozen primary partition ends exclusively at `2023-03-30T08:00:00Z` with 106,603 rows. `main.py` searches for `2023-03-31`, selecting 107,451 rows through `2023-03-30T23:49:00Z`. The derived output therefore contains 848 rows at or after the frozen reserve start. The prior attestation that the second sample was untouched is false.

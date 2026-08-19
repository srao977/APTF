# APTF Test 002 Two-Observation Latency and Continuity Result V0.1

Status: PASS
Date: 2026-08-18

## Targets

| Observation | Physical row | Data observation | Index | Source row | Market time | OHLCV |
|---|---:|---:|---:|---:|---|---|
| t1 | 10 | 9 | 8 | 9 | 2022-09-30T08:08:00Z | 365.68 / 365.70 / 365.50 / 365.50 / 4288 |
| t2 | 11 | 10 | 9 | 10 | 2022-09-30T08:09:00Z | 365.54 / 365.54 / 365.49 / 365.49 / 758 |

Source order is consecutive. Market observation interval is 60 seconds. This is separate from local processing latency. Exactly two targets were processed; the last data index read was 9 and no physical row after 11 was consumed.

## Functional Results

| Observation | Market time | D01 summary | D02 direction | D04 state | Capturability | Candidate | D03 Position | Position Controller Decision |
|---|---|---|---|---|---:|---|---|---|
| t1 | 08:08:00Z | level -0.6571388532831072; strength 0.8777636556469071; uncertainty 0.3799587892055599; reversal 0.785306864585095 | UPWARD; displacement 0.01978985584654247 | CLOSED | 0.22050421416872243 | null | FLAT | NO_ACTION |
| t2 | 08:09:00Z | level -0.6487986245281485; strength 0.6443499381248182; uncertainty 0.42387487667499785; reversal 0.5972582524083497 | UPWARD; displacement 0.026416809218216097 | CLOSED | 0.17666062360338286 | null | FLAT | NO_ACTION |

Both D03 records used `TARGET:R31|TRANSITION:T20|OVERLAYS:NONE`. Both plans are `NO_CHANGE_FLAT`, `[NO_ACTION]`, `NON_EXECUTABLE_NO_CHANGE`, `action_authorized=false`. These are code results, not profitability interpretations.

## Direct Latency Boundary

Start: immediately before `create_source_event` begins E0 for the target.

Stop: immediately after the complete E5 `StageResult` and `PositionTransitionPlan` envelope return to the caller.

Both samples use `time.perf_counter_ns()` through one `SystemClock`, clock domain `2e5f52dd-b1a5-421f-8c57-5128cd9efc11`. Direct latency is independently sampled, not calculated from UTC, market time, or stage sums.

## Latency Reconciliation

| Observation | Market time | Direct ns | Math components ns | All measured stages ns | Delta math ns | Delta all ns | Direct us | Direct ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| t1 | 08:08:00Z | 1547600 | 164700 | 176300 | 1382900 | 1371300 | 1547.6 | 1.5476 |
| t2 | 08:09:00Z | 1711000 | 215100 | 221900 | 1495900 | 1489100 | 1711.0 | 1.7110 |

### Stage Durations

| Observation | E0 ns | D01 ns | D02 ns | D04 ns | D03 ns | Controller ns |
|---|---:|---:|---:|---:|---:|---:|
| t1 | 11600 | 46600 | 28300 | 24300 | 57500 | 8000 |
| t2 | 6800 | 46800 | 32300 | 46500 | 77500 | 12000 |

All canonical values are unrounded integer nanoseconds. Unit conversions use us = ns/1000 and ms = ns/1000000. These clocks provide nanosecond resolution; no nanosecond accuracy claim is made.

## Overhead Accounting

Measured separately: each E0-E5 call interval; each outer E0-entry to E5-return interval; inter-observation runtime gap.

Uninstrumented inside the direct boundary: execution UUID generation before each stage timer; payload normalization after successful stage timers; canonical serialization and SHA256; event-ID generation; envelope construction/validation; parent-child handoff and Python call overhead; D03Input construction and controller argument preparation between stage timers.

Not present: network, database, queue, pub/sub, async overlap, market-time sleep, Azure, or broker input. No numeric subdivision of uninstrumented overhead is claimed. Outer timer sampling itself adds small diagnostic overhead; state capture and report generation were outside each target direct boundary.

## Observation Spacing And Order

```text
E0(t1) -> D01(t1) -> D02(t1) -> D04(t1) -> D03(t1) -> E5(t1)
then
E0(t2) -> D01(t2) -> D02(t2) -> D04(t2) -> D03(t2) -> E5(t2)
```

- Market event interval: 60 seconds.
- Local inter-observation runtime gap: 610600 ns = 610.6 us = 0.6106 ms.
- Artificial wait: NO.
- Concurrency or overlap: NONE.

## State Continuity

### D01

Stateful: YES, `D01V02Model.state / RuntimeState`.

Before t1: sequence 8, model time 1664525220, reference 366.0157352105078, scale 0.7590324720175738, volume reference 588.5134348690233, previous level/velocity -0.6004159601978543/-0.0035612763243195837.

After t1 and exactly before t2: sequence 9, model time 1664525280, reference 365.9899484499824, scale 0.7455782709158161, volume reference 773.4877631255721, previous level/velocity -0.6571388532831072/-0.0009453815512633182.

Classification: DIRECT T1 STATE EFFECT plus PRIOR HISTORY STATE EFFECT. Reset: NO.

### D02

Stateful: NO. Pure transformation for each DMO/FMO pair. Classification: STATELESS. Reset: N/A.

### D04

Stateful: YES, `TradingEnvelope` and `HysteresisController`.

Before t1: CLOSED, aperture 0.2776088557247953, model time 1664525220, no candidate, counters 0/0.

After t1 and exactly before t2: CLOSED, aperture 0.2490565349467589, model time 1664525280, no candidate, counters 0/0.

After t2: CLOSED, aperture 0.21285857927507087, model time 1664525340, no candidate, counters 0/0.

Classification: DIRECT T1 STATE EFFECT for aperture and model time; state/candidate/counters remained continuous. Reset: NO.

### D03

Stateful: NO. Each call consumes current D04 evaluation and DecisionContext. Classification: STATELESS. Reset: N/A.

### Position Controller

Controller algorithm stateful: NO. Harness-maintained internal transition state: YES.

- D03 POSITION(t1): FLAT.
- INTERNAL CONTROLLER STATE BEFORE t1: FLAT/version 1/identity INITIAL.
- POSITION CONTROLLER DECISION(t1): NO_ACTION.
- INTERNAL CONTROLLER STATE AFTER t1: FLAT/version 1/identity INITIAL.
- D03 POSITION(t2): FLAT.
- INTERNAL CONTROLLER STATE BEFORE t2: FLAT/version 1/identity INITIAL.
- POSITION CONTROLLER DECISION(t2): NO_ACTION.
- INTERNAL CONTROLLER STATE AFTER t2: FLAT/version 1/identity INITIAL.

After-t1 state exactly equals before-t2 state. Classification: STATEFUL BUT T1 DID NOT ALTER RELEVANT STATE because the NO_ACTION plan was non-executable. This is TEST/REPLAY INITIAL CONTROL STATE carried by the harness, not broker state and not synthetic market data. Reset: NO.

## Identity And Lineage

- t1 observation ID: `aptf:obs:v1:sha256:b509f4eab70253e21966fc6747eeec80329585c71e96a22b58cfa7f7dc21e696`.
- t2 observation ID: `aptf:obs:v1:sha256:3ad98ae11f9f797e81ea3cb6b3c28f4bb6bf0d59460425776e0d5a8f9316a0b9`.
- IDs distinct: PASS.
- t1 ID preserved E0-E5: PASS.
- t2 ID preserved E0-E5: PASS.
- Independent parent chains: PASS.
- Cross-observation parent links: NONE.

Mathematical state continuity does not merge event lineages. E0(t2) is the t2 lineage root.

## Test 001 Non-Drift

T1 agrees field-for-field with Test 001 for complete D01 DMO/FMO, D02 ReturnShape, D04 EnvelopeEvaluation, D03 POSITION FLAT, and Position Controller Decision NO_ACTION. Timing, UTC processing values, and execution IDs were not required to match and differ by design.

T2 has no prior golden result. Its basis is successful frozen execution, valid inherited state, unchanged authorities, no future leakage, and no tuning; no plausibility claim is substituted for evidence.

## Timing Validations

T01-T12: PASS. Direct and stage values are nonnegative integers; component/all-stage sums and both deltas are arithmetically exact; direct samples share one monotonic domain; no UTC/market-time latency subtraction occurred; no nanosecond accuracy claim is made.

## Continuity Validations

C01-C10: PASS. Processing was sequential; no reset occurred; IDs are distinct and preserved; parent chains do not cross; inherited and t1-induced state are identified; semantic-contract terminology is used; no broker semantics were introduced.

## Functional Validations

F01-F12: PASS. Both source rows are authoritative real observations; no row after 11 was consumed; all five real frozen components executed twice; no tuning or synthetic output occurred; authorities are unchanged; t1 matches Test 001; t2 is recorded without post-hoc interpretation.

## Frozen Authorities

Post-test hash audit: 67/67 bound references PASS.

- D01: UNCHANGED
- D02: UNCHANGED
- D04: UNCHANGED
- D03: UNCHANGED
- Position Controller: UNCHANGED
- Temporal Runtime V0.2: UNCHANGED
- Position Controller Semantic Contract V0.1: UNCHANGED
- Schemas/configs/wrappers/replay authorities: UNCHANGED
- Test 001 evidence: UNCHANGED

## Acceptance Gates

| Gate | Result | Evidence |
|---|---|---|
| G01 both rows confirmed | PASS | physical rows 10/11, indices 8/9 |
| G02 exactly two targets | PASS | target_count=2 |
| G03 no future leakage | PASS | last index 9, future rows 0 |
| G04 pre-test hashes valid | PASS | 30/30 protected, 37/37 freeze refs |
| G05 post-test hashes unchanged | PASS | 67/67 combined bindings |
| G06 sequential processing | PASS | fixed 12-event order |
| G07 no unauthorized reset | PASS | same live instances and snapshot equalities |
| G08 distinct observation IDs | PASS | two content identities |
| G09 t1 lineage | PASS | E0-E5 complete |
| G10 t2 lineage | PASS | E0-E5 complete |
| G11 t1 independent direct latency | PASS | outer monotonic pair |
| G12 t2 independent direct latency | PASS | outer monotonic pair |
| G13 t1 stage durations valid | PASS | six nonnegative integers |
| G14 t2 stage durations valid | PASS | six nonnegative integers |
| G15 component sums correct | PASS | exact arithmetic |
| G16 reconciliation deltas correct | PASS | exact raw differences |
| G17 overhead inspected | PASS | measured/uninstrumented/not-present classes |
| G18 all component continuity audited | PASS | D01/D02/D04/D03/controller |
| G19 t1->t2 state effect identified | PASS | direct D01 and D04 effects |
| G20 semantic contract honored | PASS | D03 POSITION / CONTROLLER DECISION / INTERNAL STATE |
| G21 t1 Test 001 non-drift | PASS | five deterministic comparisons |
| G22 t2 frozen execution | PASS | complete real E0-E5 result |
| G23 no mock market observation | PASS | authoritative CSV only |
| G24 no tuning | PASS | frozen configuration |
| G25 no broker data | PASS | internal replay/control state identified |
| G26 no Azure | PASS | no dependency or execution |
| G27 no 60-second delay | PASS | measured 610600 ns local gap |
| G28 no profitability/future analysis | PASS | no row 12 or future outcome |

**G01-G28: 28/28 PASS**

## Final Status

**PASS**

Next action: human review of direct end-to-end latency, component-sum reconciliation, t1-to-t2 state continuity, and both mathematical results. Do not increase observation count before review.

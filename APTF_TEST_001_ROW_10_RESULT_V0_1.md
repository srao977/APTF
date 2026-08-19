# APTF Test 001 Row 10 Result V0.1

Status: PASS
Date: 2026-08-18

## Target Confirmation

- Authoritative CSV: `data/market/normalized/SPY_1min_normalized_v0_1.csv`
- Header: physical row 1
- Target: physical row 10
- Data observation number: 9
- Zero-based data index / envelope sequence: 8
- Existing source row number: 9
- Timestamp: `2022-09-30T08:08:00Z`
- OHLCV: `365.68 / 365.7 / 365.5 / 365.5 / 4288.0`
- Target confirmed: YES
- Last data index read: 8
- Future rows read: 0

## Frozen Authorities

| Authority | Pre-test | Post-test |
|---|---|---|
| D01 | PASS | PASS |
| D02 | PASS | PASS |
| D04 | PASS | PASS |
| D03 | PASS | PASS |
| Position Transition Controller | PASS | PASS |
| Temporal Runtime V0.2 | PASS | PASS |

The broader protected inventory remained 30/30 identical and every Temporal Runtime freeze reference remained 20/20 identical. Temporal freeze SHA256 remained `4e23eae07adc848614f71842c97c49271a1d22db6624d3d85e427a92ff02296a`.

## Functional / Mathematical Verdict

PASS. The real target traversed exact frozen D01, D02, D04, D03, and Position Transition Controller calls.

- D01: target close 365.5 and volume 4288.0 plus prior RuntimeState produced level -0.6571388532831072, strength 0.8777636556469071, coherence 0.4855782805501968, persistence 0.5179117484872026, uncertainty 0.3799587892055599, reversal propensity 0.785306864585095, and eight FMO samples.
- D02: terminal displacement +0.01978985584654247, maximum absolute displacement 0.01978985584654247, direction UPWARD.
- D04: capturability 0.22050421416872243, prior/new state CLOSED/CLOSED, safety CLEAR, no candidate.
- D03: desired position FLAT through `TARGET:R31|TRANSITION:T20|OVERLAYS:NONE`; reasons `ENVELOPE_CLOSED` and `POSITION_ALREADY_ALIGNED`.
- Controller: actual FLAT, desired FLAT, transition `NO_CHANGE_FLAT`, verbs `[NO_ACTION]`, plan `NON_EXECUTABLE_NO_CHANGE`, authorization false.

The UPWARD ReturnShape did not become desired LONG because D04 was CLOSED and emitted no qualified candidate; D03 therefore selected R31 before candidate-direction rules.

## Position Provenance

The target current/actual position was `{state: FLAT, version: 1, identity: INITIAL}`. It came from the unchanged integration harness: explicit pre-row-1 LONG replay initial condition plus one authorized semantic-success advancement during the eight warm-up rows. It did not come from a broker feed. The controller is stateless and did not manufacture this current position.

## Temporal / Runtime Verdict

PASS. One observation ID `aptf:obs:v1:sha256:b509f4eab70253e21966fc6747eeec80329585c71e96a22b58cfa7f7dc21e696` was preserved E0-E5; market time was preserved; immediate parent lineage was complete; all six UTC pairs were captured; all same-domain nanosecond durations were nonnegative.

Measured durations: E0 12500 ns, D01 45800 ns, D02 32000 ns, D04 26700 ns, D03 55000 ns, controller 8200 ns. These measurements are not mathematical-performance claims.

## Volume

Volume was present and consumed by D01 through volume-reference/influence, coherence evidence, and strength effective mass. No downstream component consumed source volume directly. No volume trading heuristic was introduced.

## Transition Semantics Verification

The frozen controller matrix exactly matches all nine mappings listed in the request: FLAT/FLAT NO_ACTION; FLAT/LONG BUY; FLAT/SHORT SELL_SHORT; LONG/FLAT SELL; LONG/LONG HOLD; LONG/SHORT SELL then SELL_SHORT; SHORT/FLAT BUY_TO_COVER; SHORT/LONG BUY_TO_COVER then BUY; SHORT/SHORT HOLD. Authorization and plan status remain separate from the base verb list.

## Test Gates

| Gate | Result | Evidence |
|---|---|---|
| G01 row 10 resolved mechanically | PASS | streamed header plus nine data rows |
| G02 exactly one target | PASS | target_count=1 |
| G03 no future row consumed | PASS | last index 8, future rows 0 |
| G04 prior rows only causal warm-up | PASS | indices 0-7, outputs not analyzed as targets |
| G05 frozen authorities verified before | PASS | 30/30 and 20/20 |
| G06 frozen authorities unchanged after | PASS | 30/30 and 20/20 |
| G07 temporal freeze unchanged | PASS | exact freeze SHA256 unchanged |
| G08 real D01 | PASS | `D01V02Model.step` |
| G09 real D02 | PASS | `build_return_shape` |
| G10 real D04 | PASS | `TradingEnvelope.process` |
| G11 real D03 | PASS | `evaluate_decision` |
| G12 real controller | PASS | `derive_transition_plan` |
| G13 D01->D02 mapped | PASS | mathematical trace |
| G14 D02->D04 mapped | PASS | mathematical trace |
| G15 D04->D03 mapped | PASS | mathematical trace |
| G16 D03->controller mapped | PASS | mathematical trace |
| G17 desired position identified | PASS | FLAT / R31 |
| G18 actual-position source identified | PASS | harness replay state, not broker |
| G19 semantic action identified | PASS | NO_ACTION, unauthorized no-change plan |
| G20 backward causal trace | PASS | decision causal artifact |
| G21 observation ID preserved | PASS | one ID E0-E5 |
| G22 temporal telemetry valid | PASS | six UTC/monotonic records |
| G23 no tuning | PASS | frozen values used unchanged |
| G24 no mock/synthetic market data | PASS | authoritative FirstRateData normalized rows |
| G25 no Azure | PASS | no dependency or execution |
| G26 no profitability/future interpretation | PASS | no row 11/future price read |

**G01-G26: 26/26 PASS**

## Final Result

- Desired position: **FLAT**
- Semantic action: **NO_ACTION**
- Test status: **PASS**
- Next action: **HUMAN REVIEW OF TEST 001**

No physical row 11 was run. No parameter, frozen component, runtime, schema, configuration, historical output, replay output, or freeze manifest was modified.

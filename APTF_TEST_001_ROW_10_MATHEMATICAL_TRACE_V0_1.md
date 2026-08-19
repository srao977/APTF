# APTF Test 001 Row 10 Mathematical Trace V0.1

Status: PASS / TEST EVIDENCE ONLY
Target: physical CSV row 10, data index 8, `2022-09-30T08:08:00Z`

Complete machine values are preserved in `APTF_TEST_001_ROW_10_COMPONENT_TRACE_V0_1.json`. This report separates mathematical inputs from envelope telemetry and reports code causality without financial interpretation.

## E0 Source Observation

### Market / Scientific Source

The complete normalized CSV record contains all 22 fields shown in the input JSON. The real integration maps only the following object into frozen D01:

| D01 observation field | Actual value | Source | Direct / derived | Prior state contributes? | Actual use in `step` |
|---|---:|---|---|---|---|
| `entity_id` | `SPY` | Harness constructor | configured, not row-derived | no | D01 model state already owns entity; observation value is not separately branched on |
| `event_time` | `1664525280.0` | UTC timestamp | parsed epoch seconds | causal comparison uses prior event | sequence validation, `dt` |
| `receive_time` | `1664525280.0` | event time | harness copies event time | no | normalized but not used in D01 mathematics |
| `sequence_id` | `8` | zero-based data index | derived | compared with prior sequence | causal validation |
| `price` | `365.5` | CSV `close` | direct mapping | yes | reference/scale and kinematics |
| `volume` | `4288.0` | CSV `volume` | direct mapping | yes | volume-reference update; volume evidence/effective mass |
| `bid`, `ask`, `bid_size`, `ask_size` | null | unavailable | direct null defaults | no | not used by current D01 step |
| `session` | `PREMARKET` | CSV `session_type` | direct mapping | no | carried in observation; not read by current mathematics |
| `source_quality` | `1.0` | CSV `data_valid=true` | harness maps true to 1.0 | no | clipped to `data_quality`; perturbation/uncertainty input |
| `availability_mask` | price/volume true; bid/ask false after defaults | harness plus `with_defaults()` | derived | no | normalized, not otherwise read by current step |

CSV open/high/low (`365.68/365.7/365.5`) remain in E0 but are not mapped into `NormalizedObservation`; D01 price is close `365.5`. CSV returns/ranges/session metadata are likewise not direct D01 mathematical inputs.

### Temporal Envelope Metadata

`source_stream_id=aptf:source:v1:FirstRateData:SPY_1min_firstratedata:normalized_v0_1:sha256:73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`, sequence 8, instrument SPY, role `PROVIDER_EVENT`, and observation ID `aptf:obs:v1:sha256:b509f4eab70253e21966fc6747eeec80329585c71e96a22b58cfa7f7dc21e696` are runtime metadata. Frozen D01 receives the observation object above, not these envelope fields.

## D01 Input State

`D01V02Model.step` reads target observation plus mutable `RuntimeState` accumulated from data indices 0-7. Immediately before target t:

| State value actually read | Actual value | Role in code |
|---|---:|---|
| sequence | 8 | first-observation branch selection |
| last event time | 1664525220.0 | gives `dt=60.0` seconds |
| last observation | index 7 observation | causal event/sequence validation |
| adaptive reference | 366.0157352105078 | reference update |
| adaptive scale | 0.7590324720175738 | scale update/normalization |
| volume reference | 588.5134348690233 | volume influence update |
| previous level | -0.6004159601978543 | velocity/innovation |
| previous velocity | -0.0035612763243195837 | acceleration/perturbation/persistence |
| parameter state `ref_alpha` | 0.05095261450848489 | bounded adaptive update |
| prior persistence | 0.49739241038059606 | recursive persistence |
| prior uncertainty | 0.3967330512875907 | strength input |
| observation/forward half-life | 17.775628547068138 each | recursive half-life update |
| counters | clipping 0; bound hits 0; innovation extremes 0; data gaps 7 | health/accounting paths |

Other prior state-vector values are captured in the machine trace. The target result is therefore dependent on target plus prior causal state, not the row alone.

## D01 Output

### DMO

| Property | Actual value | Type / authority meaning | Direct / derived | D02 consumer |
|---|---|---|---|---|
| model_time | 1664525280.0 | float UTC event seconds | copied from target | copied |
| entity_id | SPY | configured identifier | configured | copied |
| model_version | 0.2 | implementation version | configured | validated/copied |
| state_level | -0.6571388532831072 | normalized displacement | derived target + state | current_level |
| state_velocity | -0.0009453815512633182 | normalized displacement/s | derived target + state | not top-level copied; FMO velocities carry projection |
| state_acceleration | 4.3598246210338045e-05 | normalized displacement/s2 | derived | not top-level copied |
| state_curvature | 4.359818776174796e-05 | normalized kinematic curvature | derived | no |
| strength | 0.8777636556469071 | [0,1] strength score | derived, volume can influence | copied |
| coherence | 0.4855782805501968 | [0,1] evidence agreement ratio | derived, includes volume channel | copied |
| persistence | 0.5179117484872026 | [0,1] recursive score | derived + prior state | copied |
| perturbation_magnitude | 0.019860213546167346 | normalized innovation | derived | no |
| perturbation_class | CONTRADICTING | frozen perturbation enum | derived | no |
| uncertainty | 0.3799587892055599 | [0,1] uncertainty score | derived | copied |
| reversal_propensity | 0.785306864585095 | [0,1] reversal score | derived | copied |
| state_support_ratio | 0.39012915911128365 | strength*persistence/(uncertainty+reversal), epsilon protected | derived | copied |
| observation_half_life | 15.0 | seconds | recursively derived/clamped | no |
| forward_half_life | 15.0 | seconds | recursively derived/clamped | copied and formula input |
| parameter_state | `{'ref_alpha': 0.05108942475062641}` | emitted diagnostic; excluded from canonical Q_t | derived | no |
| parameter_update_magnitude | `{'ref_alpha': 0.00013681024214151627}` | emitted diagnostic | derived | no |
| data_quality | 1.0 | normalized source quality | derived from `data_valid` | no |
| model_health | DEGRADED_DATA | model health diagnostic | derived | no |
| dmo_schema_version | 0.2.0 | schema identifier | configured | no |
| fmo_schema_version | 0.2.0 | schema identifier | configured | no |
| config_hash | `30DE0D125752D222FED57D80581C73939C4C0BA9ABD5F6FDAA9CFCB9970BF8DD` | D01 configuration identity | configured | no |
| state_hash | `FDDDBC0F774A0C67B723D273629BECD128E6DBC5398FD00B8B458530DAA7F9C1` | D01 state identity | derived | no |
| trace_id | SPY:9 | entity plus post-step sequence | derived | no |

Where the Q_t authority does not define a stronger financial interpretation, none is inferred. The nine diagnostic fields are explicitly outside canonical Q_t.

### FMO

`model_time=1664525280.0`, `entity_id=SPY`, `interval_length=58.805642197812524` seconds. Each sample is a structured projection, not a future observation.

| tau | level | velocity | uncertainty | strength | persistence | reversal propensity |
|---:|---:|---:|---:|---:|---:|---:|
| 1.3926982200548028 | -0.658413202726016 | -0.0008864567003801471 | 0.3893081652544837 | 0.8230533723221005 | 0.48563073717545263 | 0.7915397819510442 |
| 4.849656879880872 | -0.6612109321047579 | -0.0007555809103576271 | 0.4100737159225124 | 0.7015384012161677 | 0.41393258614359707 | 0.8053834823963967 |
| 10.061790698047371 | -0.6644441493795055 | -0.0005938549793462715 | 0.4357341380232886 | 0.5513798284920343 | 0.32533369229604603 | 0.8224904304635808 |
| 16.887486114292866 | -0.666887140499668 | -0.00043320932676848233 | 0.46122315656238283 | 0.4022242678805201 | 0.23732661123734597 | 0.8394831094896437 |
| 25.234983688396127 | -0.667113763760807 | -0.0002945605989781781 | 0.4832220089207286 | 0.2734923141065323 | 0.16137018397319478 | 0.8541490110618741 |
| 35.037190239811366 | -0.6635016605663079 | -0.00018726535630199425 | 0.5002461261990071 | 0.17387130466424297 | 0.10259024833289869 | 0.8654984225807265 |
| 46.241668136145385 | -0.6542419854858573 | -0.00011158312302003839 | 0.512254330692868 | 0.10360220150232982 | 0.06112898042884944 | 0.8735038922433004 |
| 58.805642197812524 | -0.6373489974365647 | -6.243905314288154e-05 | 0.5200518284034197 | 0.05797313420024822 | 0.03420620927487088 | 0.8787022240503348 |

Nested meanings are defined by Q_t authority: tau is the elastic sample coordinate; level is projected normalized displacement; velocity is decayed current velocity; uncertainty increases with decay loss; strength/persistence decay; reversal propensity increases with decay loss.

### D01 Telemetry

E1 event `aptf:evt:v1:sha256:1bed3437d89a99bf77b9ef10297b7ed3fbaf86ee486dcf860c9fcf10819263ae`, parent E0 `...a4927b85...`, received `2026-08-18T17:17:08.450009Z`, emitted `2026-08-18T17:17:08.450056Z`, duration 45800 ns. Telemetry did not enter D01 mathematics.

## D01 -> D02 Contract

| D01 output property | Value at t | Passed? | D02 field/use | Adapter | Information lost? |
|---|---|---|---|---|---|
| model_time (DMO/FMO) | 1664525280.0 | yes | model_time | equality validate, copy | no |
| entity_id (DMO/FMO) | SPY | yes | entity_id | equality validate, copy | no |
| model_version | 0.2 | yes | source_model_version | validate then copy | no |
| state_level | -0.6571388532831072 | yes | current_level | copy | no |
| state_velocity/acceleration/curvature | measured above | input objects cross, but not top-level output | only projected FMO samples survive | no direct top-level mapping | yes at ReturnShape top level |
| strength/coherence/persistence/uncertainty/reversal | measured above | yes | same-named fields | copy | no |
| state_support_ratio | 0.39012915911128365 | yes | same name | copy | no |
| forward_half_life | 15.0 | yes | same name and decay formula | copy | no |
| observation_half_life | 15.0 | no | none | omitted | yes |
| perturbation magnitude/class | 0.0198602 / CONTRADICTING | no | none | omitted | yes |
| FMO interval_length | 58.805642197812524 | yes | projection_interval | copy | no |
| all 8 FMO samples, all 7 fields | table above | yes | forward_samples | ordered field-for-field dataclass copy | no |
| terminal sample + current level | -0.6373489974 / -0.6571388533 | yes | terminal_displacement | subtract | source values retained elsewhere |
| all sample levels + current level | table above | yes | maximum_absolute_displacement | max absolute difference | source samples retained |
| interval + forward half-life | 58.8056422 / 15.0 | yes | terminal_decay_factor | $2^{-I/H}$ | no |
| nine DMO diagnostics | values above | no | none | omitted | yes by authority |

Nature of boundary: D02 consumes the actual frozen `DMOOutput` and `FMOOutput` types directly. There is no pseudo-Q adapter, telemetry input, state, randomness, or I/O.

## D02 Output: ReturnShape

| Property | Actual value | Type / documented meaning | Direct / derived | D04 use |
|---|---|---|---|---|
| model_time | 1664525280.0 | float causal model time | copied | lineage/new-shape/projection |
| entity_id | SPY | string identity | copied | binding/output |
| source_model_version | 0.2 | string D01 version | copied | output lineage |
| current_level | -0.6571388532831072 | normalized displacement | copied | geometry validation/calculation |
| projection_interval | 58.805642197812524 | seconds | copied | staleness/projection validity |
| forward_half_life | 15.0 | seconds | copied | not directly read by D04 formulas |
| forward_samples | eight rows above | immutable projections | copied | sign/geometry validation uses levels |
| terminal_displacement | 0.01978985584654247 | terminal level minus current | derived | geometry/sign validation and quality |
| maximum_absolute_displacement | 0.01978985584654247 | max absolute path displacement | derived | geometry validation/quality |
| path_direction | UPWARD | exact displacement sign | derived | validated; copied only if candidate qualifies |
| terminal_decay_factor | 0.06604640534760162 | $2^{-I/H}$ | derived | not directly read by D04 |
| strength | 0.8777636556469071 | D01 score | copied | structural quality |
| coherence | 0.4855782805501968 | D01 agreement ratio | copied | structural quality |
| persistence | 0.5179117484872026 | D01 recursive score | copied | structural quality |
| uncertainty | 0.3799587892055599 | D01 uncertainty | copied | risk quality/reason code |
| reversal_propensity | 0.785306864585095 | D01 reversal score | copied | risk quality/reason code |
| state_support_ratio | 0.39012915911128365 | D01 support ratio | copied | not directly read by D04 |

D02 is pure and reads no prior internal state.

### D02 Telemetry

E2 event `aptf:evt:v1:sha256:44aa341620badc4c175702c5e323e28bcca2ec5f3841d7e3e0258888da72c13a`, parent E1, received `2026-08-18T17:17:08.450499Z`, emitted `2026-08-18T17:17:08.450532Z`, duration 32000 ns.

## D02 -> D04 Contract

The entire immutable ReturnShape crosses unchanged. D04 does not use envelope telemetry.

| ReturnShape group | Value | Passed? | D04 field/use | Transformation | Lost? |
|---|---|---|---|---|---|
| identity/time/version | SPY / 1664525280 / 0.2 | yes | binding, lifecycle, output lineage | validate/copy | no |
| current level + sample levels | values above | yes | recompute geometry validity | subtraction/max | no |
| displacement/max/direction | 0.0197898558 / 0.0197898558 / UPWARD | yes | validate; geometry=1.0; candidate direction if qualified | exact formulas | no |
| projection interval | 58.8056422 | yes | projection-valid cutoff | model_time + interval | no |
| strength/coherence/persistence | 0.8777637 / 0.4855783 / 0.5179117 | yes | structural quality | cube root of product | compressed into score, originals remain in input only |
| uncertainty/reversal | 0.3799588 / 0.7853069 | yes | risk quality and reason codes | square-root complement product | compressed into score |
| forward half-life/terminal decay/state support | 15 / 0.0660464 / 0.3901292 | yes in object | no active D04 branch/formula | none | not propagated to D04 output |
| nested sample non-level fields | table above | yes in object | ReturnShape validation already enforces ranges; D04 geometry uses levels | none | not propagated to D04 output |

## D04 Input

### A. D02-derived

Complete ReturnShape above.

### B. Existing Integration Configuration

| Property | Actual | Fixed/variable | Repository role |
|---|---:|---|---|
| gate dimensions | liquidity, spread, latency, execution, capital, portfolio, position, risk, broker, data integrity | fixed ordered tuple | minimum feasibility gate |
| gate warning threshold | 0.5 | fixed | low-gate reason threshold |
| critical data-integrity threshold | 0.0 | fixed by frozen real harness | hard/safety eligibility; differs from YAML 0.2 but was not changed for this test |
| open/close thresholds | 0.75 / 0.55 | fixed | hysteresis state transitions |
| open/close persistence | 3 / 2 observations | fixed | hysteresis confirmation |
| aperture alpha | 0.5 | fixed | aperture update smoothing |

### C. Context and Prior State

All context values: evaluation time 1664525280.0; market eligible true; data integrity 1.0; clock-event quality 1.0; capital/portfolio/position capacities 1.0; liquidity/spread/latency/execution/risk/broker qualities 1.0. The ten gate dimensions produce minimum gate 1.0. `clock_event_quality` is present in context but is not in the frozen ten-field gate or another D04 branch.

Prior D04 state from indices 0-7: CLOSED, aperture 0.2776088557247953, entity SPY, model time 1664525220.0, no candidate, both hysteresis counters zero. Thus D04 is target + prior-state + configuration dependent.

## D04 Output: EnvelopeEvaluation

| Property | Actual value | Meaning/code derivation | D03 target-active? |
|---|---|---|---|
| evaluation_time | 1664525280.0 | context causal time | validation/source record |
| entity_id | SPY | ReturnShape identity | validation/source record |
| return_shape_model_time | 1664525280.0 | D02 lineage | source record |
| source_model_version | 0.2 | D02 lineage | no target branch |
| hard_eligibility | 1 | valid projection, eligible market, integrity > 0 | not directly |
| geometry_quality | 1.0 | abs(terminal)/maximum | not directly |
| structural_quality | 0.6043625386410295 | cube root(strength*coherence*persistence) | not directly |
| risk_quality | 0.36485420599454843 | sqrt((1-uncertainty)*(1-reversal)) | not directly |
| base_capturability_score | 0.22050421416872243 | geometry*structural*risk | not directly |
| feasibility_gate_score | 1.0 | minimum ten context dimensions | not directly |
| capturability_score | 0.22050421416872243 | hard*base*gate | upstream state effect only |
| previous_envelope_state | CLOSED | prior D04 state | no target branch |
| new_envelope_state | CLOSED | hysteresis at score below open threshold | **yes: R31** |
| aperture_before | 0.2776088557247953 | prior aperture | no |
| aperture_after | 0.2490565349467589 | aperture model update | no |
| projection_valid | true | evaluation <= model+interval | yes: R30 guard |
| stale | false | inverse projection validity | yes: R30 guard |
| safety_state | CLEAR | no safety reason | yes: R30 guard |
| safety_reason | null | no safety closure | supporting detail only if R30 |
| candidate_envelope | null | candidates exist only in OPEN state | yes: later R34-R41, not reached after R31 |
| gate_dimension_values | all ten = 1.0 | copied context gate inputs | no direct D03 branch |
| reason_codes | `['REVERSAL_PROPENSITY_HIGH']` | reversal > 0.5 | no direct D03 branch |
| events | superseded, accepted, capturability evaluated, aperture updated | lifecycle event record | no direct D03 branch |

No CandidateEnvelope participated because D04 remained CLOSED.

### D04 Telemetry

E3 event `aptf:evt:v1:sha256:71218ec92bd3a2797a1ff6fc212a34642f6825a6c0c5c08ea7cc7e96c68f23c2`, parent E2, received `2026-08-18T17:17:08.450869Z`, emitted `2026-08-18T17:17:08.450897Z`, duration 26700 ns.

## D04 -> D03 Contract

The complete 23-field EnvelopeEvaluation crosses and participates in D03 fingerprints. Actual target-selection reads are limited to time/entity validation and ordered policy branches.

| D04 property/group | Actual | Passed? | D03 use | Transformation / information loss |
|---|---|---|---|---|
| evaluation/entity/model time | target/SPY/target | yes | input invariants and source fields | copied |
| safety state/stale/projection valid | CLEAR/false/true | yes | R30 guard | direct booleans/enums |
| new envelope state | CLOSED | yes | R31 first active target branch | direct enum |
| candidate | null | yes | R34-R41 only if OPEN | no adapter; branches not reached |
| safety reason | null | yes | R30 supporting detail | no |
| all scores, hard eligibility, prior state, apertures, gates, reasons, events, version | measured above | yes | fingerprint and immutable record, not target-selected directly | not copied individually into DecisionRecord |

LONG/SHORT can be selected only after higher-priority controls and safety pass, state is OPEN, candidate exists and is QUALIFIED, then candidate direction UPWARD activates R40 LONG or DOWNWARD activates R41 SHORT. Here CLOSED activates R31 before candidate logic.

## D03 Input

### D04-derived

Complete EnvelopeEvaluation above.

### Decision Context

| Field | Actual | Source | Exact role |
|---|---|---|---|
| context_time/entity | 1664525280 / SPY | target/harness | D03 invariants and identity |
| actual_position_state | FLAT | harness replay ledger state | transition T20 after target rule |
| position candidate/time | null/null | required for FLAT | context validation |
| pending target/id | NONE/null | harness fixed control context | no pending/retarget branch |
| execution_available | true | harness fixed control context | no A00 block |
| system_enabled/trading_enabled | true/true | harness fixed control context | R20/R21 not active |
| emergency_flatten | false | harness fixed control context | R10 not active |
| control_state_valid | true | harness fixed control context | required or reject |

D03 has no hidden policy state and no mutable prior state. Configuration/version strings are frozen constants in code.

## D03 Output: DecisionRecord

| Property | Actual value | Meaning / source |
|---|---|---|
| decision_id | `D03D|SPY|1664525280|D03_RULES_V0_1_DESIGN|3a099b...c64d` | deterministic decision identity |
| decision_time | 1664525280.0 | context time |
| entity_id | SPY | context entity |
| d03_model_version | D03_CONTROL_V0_1_DESIGN | frozen constant |
| decision_rule_version | D03_RULES_V0_1_DESIGN | frozen constant |
| schema_version | D03_DECISION_SCHEMA_V0_1 | frozen constant |
| source_d04_fingerprint | `701cfb...034c` | canonical D04 evaluation fingerprint |
| input_fingerprint | `3a099b...c64d` | canonical D04+context fingerprint |
| source D04 evaluation/model times | 1664525280.0 / 1664525280.0 | copied lineage |
| source D04 envelope/safety | CLOSED / CLEAR | copied lineage |
| candidate id/source time | null / null | R31 has no candidate lineage |
| prior_position_state | FLAT | context actual position |
| **desired_position_state** | **FLAT** | **R31 because new_envelope_state=CLOSED** |
| transition_intent | NO_CHANGE | T20 because actual FLAT equals desired FLAT |
| action_authorized | false | NO_CHANGE is not an authorized transition intent |
| decision_rule_id | `TARGET:R31|TRANSITION:T20|OVERLAYS:NONE` | exact selected path |
| primary_reason_code | ENVELOPE_CLOSED | R31 reason |
| supporting_reason_codes | `[POSITION_ALREADY_ALIGNED]` | T20 reason |

### D03 Telemetry

E4 event `aptf:evt:v1:sha256:7e08cd9ab07bbd9d5cc4f1060bbd0374dd8d99d4ed1b550c63f3826d10f405ce`, parent E3, received `2026-08-18T17:17:08.451071Z`, emitted `2026-08-18T17:17:08.451127Z`, duration 55000 ns.

## D03 -> Position Controller Contract

The full DecisionRecord dict crosses. Controller also receives the actual-position snapshot and, following existing harness behavior, `input_fingerprint` as the decision-hash argument.

| D03 property | Value | Passed? | Controller use |
|---|---|---|---|
| decision_id/time/entity | measured above | yes | validate/copy/transition identity |
| prior_position_state | FLAT | yes | stale-position check against actual snapshot |
| desired_position_state | FLAT | yes | transition-matrix key/output |
| transition_intent | NO_CHANGE | yes | authorization overlay and plan status |
| action_authorized | false | yes | execution authorization |
| input_fingerprint | `3a099b...c64d` | yes separately | `d03_decision_hash` argument under frozen harness behavior |
| all remaining DecisionRecord fields | measured above | present in dict | not directly read by controller validation/planning |

## Position Controller Input State

Actual snapshot: `{state: FLAT, version: 1, identity: INITIAL}`. It was produced by the frozen integration harness, not a broker feed and not hidden controller memory. The harness began with explicit LONG version 0 before data index 0 and performed one authorized semantic-success advancement during indices 0-7, leaving FLAT version 1 at target t. The controller itself is stateless.

The frozen transition matrix mechanically matches all nine conceptual mappings in the prompt with one wording correction: outputs are ordered verb lists and authorization is separate. For this target, `(FLAT, FLAT) -> NO_CHANGE_FLAT -> [NO_ACTION]`.

## PositionTransitionPlan

| Property | Actual value | Meaning/source |
|---|---|---|
| transition_id | `APTFPTP|9e3ae647458b8a283b67395abd2ff19a` | deterministic plan identity |
| entity_id | SPY | decision |
| decision_time | 1664525280.0 | decision |
| originating_d03_decision_id | full D03 ID above | lineage |
| originating_d03_decision_hash | `3a099b...c64d` | harness hash argument |
| source_position | FLAT | actual snapshot |
| desired_position | FLAT | D03 |
| transition_class | NO_CHANGE_FLAT | matrix lookup |
| ordered_execution_verbs | `[NO_ACTION]` | matrix lookup |
| action_authorized | false | NO_CHANGE overlay |
| plan_status | NON_EXECUTABLE_NO_CHANGE | no-change status |

E5 event `aptf:evt:v1:sha256:f4e75c7d667d91fc6fd0aefb055a681f6119ef6c4770237316d9f51711edfc8b`, execution `bc6d2781-7045-4e48-90e3-71244ff95af5`, parent E4, received `2026-08-18T17:17:08.451249Z`, emitted `2026-08-18T17:17:08.451258Z`, duration 8200 ns.

## End-to-End Actual Causal Chain

```text
MARKET(t): close=365.5, volume=4288, event=08:08, plus prior indices 0-7
  -> D01: level=-0.6571388533, strength=0.8777636556,
           coherence=0.4855782806, persistence=0.5179117485,
           uncertainty=0.3799587892, reversal=0.7853068646,
           terminal projected level=-0.6373489974
  -> D02: terminal displacement=+0.01978985585,
           direction=UPWARD, max displacement=0.01978985585
  -> D04: capturability=0.2205042142, state CLOSED,
           safety CLEAR, candidate=null
  -> D03: R31 -> desired FLAT; T20 -> NO_CHANGE
  -> Controller: actual FLAT + desired FLAT
                 -> NO_CHANGE_FLAT / [NO_ACTION]
                 -> action_authorized=false
```

## Dependency Classification

| Stage | Classification | Evidence |
|---|---|---|
| D01 | target + prior causal state; configuration dependent | recursive reference/scale, volume reference, kinematics, persistence, half-lives, parameters |
| D02 | directly dependent on target D01 output | pure/stateless deterministic builder; inherits D01 state dependence |
| D04 | target + prior D04 state; configuration/context dependent | hysteresis/aperture/current state plus thresholds and context |
| D03 | D04-derived and control-state dependent | stateless ordered policy over evaluation plus DecisionContext |
| Controller | control-state dependent | stateless matrix over D03 desired and harness actual snapshot |

## Volume Facts

Volume is present (4288.0) and consumed by D01. Frozen D01 updates its prior volume reference and uses resulting volume influence in coherence evidence and strength effective mass. No explicit volume field survives into DMO/FMO, ReturnShape, EnvelopeEvaluation, DecisionRecord, or PositionTransitionPlan; downstream components do not consume source volume directly. No volume trading heuristic was introduced.

# APTF Test 002A Differential Causal Map V0.1

Status: READ-ONLY DIAGNOSTIC EVIDENCE

## Primary End-to-End Differential Table

| Stage | Property | t1 | t2 | Delta | Changed? | Next-stage effect | Terminal relevance |
|---|---|---:|---:|---:|---|---|---|
| SOURCE | volume | 4288 | 758 | -3530 (-82.32276119402985%) | YES | D01 adaptive volume reference/influence | indirect; no volume rule |
| SOURCE | close / D01 price | 365.50 | 365.49 | -0.01 | YES | D01 reference, scale, kinematics | mixed with state and volume |
| D01 | volume reference after observation | 773.4877631255721 | 772.7133749692935 | -0.7743881562786148 | YES | persistent t1 value is t2 prior reference | affects t2 volume normalization |
| D01 | volume influence | 2.714886782096659 | 1.3467811574269102 | -1.3681056246697488 | YES | coherence and strength | one of several causal inputs |
| D01 | state level | -0.6571388532831072 | -0.6487986245281485 | +0.008340228754958656 | YES | D02 current level/path geometry | continuous difference retained |
| D01 | coherence | 0.4855782805501968 | 0.18477216178217787 | -0.30080611876801894 | YES | D02 copy; D04 structural quality | lowers t2 structural term |
| D01 | strength | 0.8777636556469071 | 0.6443499381248182 | -0.23341371752208884 | YES | D02 copy; D04 structural quality | lowers t2 structural term |
| D01 | persistence | 0.5179117484872026 | 0.41432939878976205 | -0.10358234969744051 | YES | D02 copy; D04 structural quality | lowers t2 structural term |
| D01 | uncertainty | 0.3799587892055599 | 0.42387487667499785 | +0.043916087469437926 | YES | D02 copy; D04 risk quality | lowers risk ceteris paribus |
| D01 | reversal propensity | 0.785306864585095 | 0.5972582524083497 | -0.1880486121767453 | YES | D02 copy; D04 risk/reason | raises t2 risk quality |
| D01/FMO | projection interval | 58.805642197812524 | 46.92093219652183 | -11.884710001290692 | YES | D02 projection interval | both remain projection-valid |
| D02 | terminal displacement | 0.01978985584654247 | 0.026416809218216097 | +0.006626953371673627 | YES | geometry/sign | geometry quality 1.0 for both |
| D02 | path direction | UPWARD | UPWARD | categorical none | NO | copied only if D04 creates candidate | no candidate created |
| D04 | structural quality | 0.6043625386410295 | 0.3667482303751486 | -0.23761430826588092 | YES | capturability product | continuous distinction retained |
| D04 | risk quality | 0.36485420599454843 | 0.48169454948065005 | +0.11684034348610162 | YES | capturability product | partially offsets structural decline |
| D04 | capturability | 0.22050421416872243 | 0.17666062360338286 | -0.04384359056533957 | YES | hysteresis open qualification | both fail 0.75 threshold |
| D04 | open-threshold margin | -0.5294957858312775 | -0.5733393763966171 | -0.04384359056533957 | YES | `open_qual=false` | decisive CLOSED gate |
| D04 | new envelope state | CLOSED | CLOSED | categorical none | NO | D03 R31 | fixes D03 POSITION FLAT |
| D04 | candidate envelope | null | null | none | NO | R34-R41 unavailable | D02 UPWARD not exposed as candidate |
| D03 | first applicable rule | R31 | R31 | none | NO | desired FLAT | categorical bottleneck consumed |
| D03 | D03 POSITION | FLAT | FLAT | none | NO | controller matrix | same matrix key |
| Controller | internal state | FLAT | FLAT | none | NO | `(FLAT, FLAT)` | no-change transition |
| Controller | Position Controller Decision | NO_ACTION | NO_ACTION | none | NO | terminal analytical event | same terminal category |

## Actual-Value Causal Map

```text
SOURCE
  market time: 08:08 -> 08:09 (+60 s)
  close:       365.50 -> 365.49 (-0.01)
  volume:      4288 -> 758 (-3530; -82.32276119402985%)
  quality:     1.0 -> 1.0

  volume path:
    prior reference 588.5134348690233
      + t1 volume 4288
      -> t1 reference 773.4877631255721
      -> exact t2 prior reference
      + t2 volume 758
      -> t2 reference 772.7133749692935

    volume influence:
      2.714886782096659 -> 1.3467811574269102

    downward arrow

D01
  level:                -0.6571388532831072 -> -0.6487986245281485
  velocity:             -0.0009453815512633182 -> 0.00013900381255947696
  acceleration:          0.000043598246210338045 -> 0.000018073089394034406
  coherence:             0.4855782805501968 -> 0.18477216178217787
  strength:              0.8777636556469071 -> 0.6443499381248182
  persistence:           0.5179117484872026 -> 0.41432939878976205
  uncertainty:           0.3799587892055599 -> 0.42387487667499785
  reversal propensity:   0.785306864585095 -> 0.5972582524083497
  state support ratio:   0.39012915911128365 -> 0.26144791004198753
  projection interval:  58.805642197812524 -> 46.92093219652183

    downward arrow

D02
  terminal displacement:
    0.01978985584654247 -> 0.026416809218216097
  maximum displacement:
    0.01978985584654247 -> 0.026416809218216097
  path direction:
    UPWARD -> UPWARD
  continuous geometry differs; sign category is the same

    downward arrow

D04
  geometry quality:     1.0 -> 1.0
  structural quality:   0.6043625386410295 -> 0.3667482303751486
  risk quality:         0.36485420599454843 -> 0.48169454948065005
  hard eligibility:     1 -> 1
  feasibility gate:     1.0 -> 1.0
  capturability:
    0.22050421416872243 -> 0.17666062360338286
  aperture before:
    0.2776088557247953 -> 0.2490565349467589
  open qualification:
    0.22050421416872243 >= 0.75 = false
    0.17666062360338286 >= 0.75 = false
  decisive gate:
    CLOSED hysteresis open threshold 0.75
  state:
    CLOSED -> CLOSED
  candidate:
    null -> null

    downward arrow

D03
  R10/R20/R21/R30: not applicable for either
  first applicable rule: R31 -> R31
  input category: CLOSED -> CLOSED
  D03 POSITION: FLAT -> FLAT
  raw capturability is present in the input/fingerprint but not read by R31

    downward arrow

POSITION CONTROLLER
  internal controller state: FLAT -> FLAT
  matrix key: (FLAT, FLAT) -> (FLAT, FLAT)
  POSITION CONTROLLER DECISION: NO_ACTION -> NO_ACTION
```

## Required Bottleneck Statement

**DECISION INFORMATION BOTTLENECK:**
D04 CLOSED/open hysteresis boundary, consumed by D03 R31.

**WHY:**
The distinct continuous capturability values 0.22050421416872243 and 0.17666062360338286 both fail the exact `capturability_score >= 0.75` open qualification. D04 therefore emits `new_envelope_state=CLOSED` and no candidate for both. D03's first applicable rule is then R31, which branches on CLOSED and returns FLAT without branching on raw capturability or D02 UPWARD direction.

**UPSTREAM DIFFERENCES STILL PRESENT:**
YES: volume influence, D01 state/strength/coherence/persistence/uncertainty/reversal, FMO geometry, D02 displacement, D04 structural quality, risk quality, capturability, and aperture all differ.

**DOWNSTREAM DISTINCTION LOST AT:**
D04's categorical `new_envelope_state=CLOSED`; D03 R31 consumes that category and fixes the target position to FLAT.

This bottleneck is a description of frozen categorical semantics, not a defect finding or tuning recommendation.

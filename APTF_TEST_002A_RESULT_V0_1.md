# APTF Test 002A Volume Differential Causal Audit Result V0.1

Status: PASS
Date: 2026-08-18

## Evidence Integrity

No pipeline component was executed, no market CSV was read, and no observation was created. Analysis used stored Test 002 evidence plus read-only frozen source. Quoted values and D01/D04 continuity matched stored evidence with no discrepancies. Pre-audit protected bindings: 67/67 PASS. Seven Test 002 evidence hashes were recorded for post-audit comparison.

## Source Differential

| Property | t1 | t2 | Signed delta | Absolute delta | Percent change |
|---|---:|---:|---:|---:|---:|
| market event epoch seconds | 1664525280 | 1664525340 | +60 | 60 | N/A |
| open | 365.68 | 365.54 | -0.14 | 0.14 | -0.03828483920367161% |
| high | 365.70 | 365.54 | -0.16 | 0.16 | -0.04375170905112611% |
| low | 365.50 | 365.49 | -0.01 | 0.01 | -0.002735978112172614% |
| close / D01 price | 365.50 | 365.49 | -0.01 | 0.01 | -0.002735978112172614% |
| volume | 4288 | 758 | -3530 | 3530 | -82.32276119402985% |
| source quality | 1.0 | 1.0 | 0 | 0 | 0% |
| sequence ID | 8 | 9 | +1 | 1 | N/A |

Volume calculation:

```text
volume_delta = 758 - 4288 = -3530
volume_ratio = 758 / 4288 = 0.1767723880597015
volume_percent_change = (-3530 / 4288) * 100
                      = -82.32276119402985%
```

No financial interpretation is attached.

## Volume Entry Into D01

```text
source volume
  -> NormalizedObservation.volume
  -> D01V02Model.step
  -> update_volume_influence(volume, prior volume_reference, config, epsilon)

ref = 0.95 * prior_reference + 0.05 * volume
relative = log1p(volume / max(ref, 1e-8))
absolute = log1p(max(volume, 0)) / 10
volume_influence = clamp(relative + absolute, 0, 3)

volume_influence
  -> coherence evidence['volume'], weight 0.7
  -> strength effective_mass, coefficient 0.8
```

D01 uses raw volume in both the adaptive reference and absolute logarithmic term; normalizes it relative to the updated adaptive reference; forms a ratio; applies nonlinear logarithms; adds relative and absolute terms; and clamps the result. It does not compare current raw volume directly with prior raw volume. It persists `volume_reference` across observations.

T1 updated reference `588.5134348690233 -> 773.4877631255721`. That exact t1 result was t2's prior reference. T2 then updated it to `772.7133749692935`.

Reconstructed volume influences are 2.714886782096659 and 1.3467811574269102. Neither hit the clamp. They reconstruct stored coherence and strength exactly within floating representation.

## D01 Differential And Attribution

Key changes:

| Property | t1 | t2 | Delta | Volume relation | Other causal inputs |
|---|---:|---:|---:|---|---|
| level | -0.6571388532831072 | -0.6487986245281485 | +0.008340228754958656 | none current | price/reference/scale/prior state |
| velocity | -0.0009453815512633182 | 0.00013900381255947696 | +0.0010843853638227952 | none current | price/kinematics/prior state |
| coherence | 0.4855782805501968 | 0.18477216178217787 | -0.30080611876801894 | direct composite input | level/velocity/acceleration/weights |
| strength | 0.8777636556469071 | 0.6443499381248182 | -0.23341371752208884 | direct and via coherence | kinematics/prior uncertainty/config |
| persistence | 0.5179117484872026 | 0.41432939878976205 | -0.10358234969744051 | no direct current input | prior persistence/kinematics/perturbation |
| uncertainty | 0.3799587892055599 | 0.42387487667499785 | +0.043916087469437926 | indirect via coherence | innovation/perturbation/quality/instability |
| reversal propensity | 0.785306864585095 | 0.5972582524083497 | -0.1880486121767453 | indirect via uncertainty | kinematics/perturbation/persistence/level |
| support ratio | 0.39012915911128365 | 0.26144791004198753 | -0.12868124906929612 | indirect via strength/uncertainty | persistence/reversal |
| projection interval | 58.805642197812524 | 46.92093219652183 | -11.884710001290692 | indirect | persistence/strength/uncertainty/perturbation/config |

All 21 relevant D01/FMO rows and exact D01->D02 mappings are in the JSON artifact. Exact isolated volume attribution is impossible from these observations: price, kinematics, perturbation class (`CONTRADICTING -> REVERSING`), and prior state also changed. No counterfactual was run.

## D01 -> D02

D02 validates and copies identity/time, current level, interval, half-life, all eight FMO samples, strength, coherence, persistence, uncertainty, reversal, and support ratio. It derives:

```text
terminal_displacement = terminal_sample.level - current_level
maximum_absolute_displacement = max(abs(sample.level - current_level))
path_direction = sign(terminal_displacement)
terminal_decay_factor = 2 ** (-projection_interval / forward_half_life)
```

Perturbation, observation half-life, top-level velocity/acceleration/curvature, and diagnostics are omitted from ReturnShape. No weighting or normalization is added by D02.

## D02 Differential

| Property | t1 | t2 | Delta |
|---|---:|---:|---:|
| terminal displacement | 0.01978985584654247 | 0.026416809218216097 | +0.006626953371673627 |
| maximum absolute displacement | 0.01978985584654247 | 0.026416809218216097 | +0.006626953371673627 |
| projection interval | 58.805642197812524 | 46.92093219652183 | -11.884710001290692 |
| terminal decay factor | 0.06604640534760162 | 0.11438246869903425 | +0.04833606335143263 |
| strength | 0.8777636556469071 | 0.6443499381248182 | -0.23341371752208884 |
| coherence | 0.4855782805501968 | 0.18477216178217787 | -0.30080611876801894 |
| persistence | 0.5179117484872026 | 0.41432939878976205 | -0.10358234969744051 |
| uncertainty | 0.3799587892055599 | 0.42387487667499785 | +0.043916087469437926 |
| reversal propensity | 0.785306864585095 | 0.5972582524083497 | -0.1880486121767453 |
| path direction | UPWARD | UPWARD | unchanged category |

D02's first categorical compression is exact sign at zero. Both different positive displacements are above zero, so both map to UPWARD. This is not the terminal decision bottleneck because D04 still consumes continuous score fields and produces distinct capturability values.

## Capturability Reconstruction

Frozen formulas:

$$
Q_G = \frac{|\mathrm{terminal\ displacement}|}{\mathrm{maximum\ absolute\ displacement}}
$$

$$
Q_S = (\mathrm{strength}\cdot\mathrm{coherence}\cdot\mathrm{persistence})^{1/3}
$$

$$
Q_R = \sqrt{(1-\mathrm{uncertainty})(1-\mathrm{reversal\ propensity})}
$$

$$
B=Q_GQ_SQ_R,\quad G=\min(\mathrm{ten\ context\ gates}),\quad C=HBG
$$

T1:

```text
Q_G = abs(0.01978985584654247) / 0.01978985584654247 = 1.0
Q_S = (0.8777636556469071 * 0.4855782805501968 * 0.5179117484872026)^(1/3)
    = 0.6043625386410295
Q_R = sqrt((1-0.3799587892055599) * (1-0.785306864585095))
    = 0.36485420599454843
H = 1; G = 1.0
C = 1 * 1.0 * 0.6043625386410295 * 0.36485420599454843 * 1.0
  = 0.22050421416872243
absolute error vs stored = 0.0
```

T2:

```text
Q_G = abs(0.026416809218216097) / 0.026416809218216097 = 1.0
Q_S = (0.6443499381248182 * 0.18477216178217787 * 0.41432939878976205)^(1/3)
    = 0.3667482303751486
Q_R = sqrt((1-0.42387487667499785) * (1-0.5972582524083497))
    = 0.48169454948065005
H = 1; G = 1.0
C = 1 * 1.0 * 0.3667482303751486 * 0.48169454948065005 * 1.0
  = 0.17666062360338286
absolute error vs stored = 0.0
```

Capturability delta is -0.04384359056533957, or -19.883334534274223%. Geometry, gate, and hard eligibility were unchanged. Structural quality fell 39.3165%; risk quality rose 32.0238%. Because the formula is multiplicative, no forced additive attribution is made: structural ratio 0.6068348167307311 times risk ratio 1.3202384447442752 gives final ratio 0.8011666546572578.

## Aperture And D04 Continuity

Aperture is a persistent smoothed state variable, not the opening threshold. It does not enter capturability and capturability is not compared against aperture. After hysteresis selects state:

```text
aperture_after = clamp(0.5 * capturability + 0.5 * aperture_before)
```

T1: `0.2776088557247953 -> 0.2490565349467589`.
T2 starts at exactly `0.2490565349467589` and updates to `0.21285857927507087`.

T1 therefore affected t2 aperture smoothing, but not t2 capturability or open qualification.

## CLOSED/Open Gate And Candidate

From CLOSED:

```text
open_qual = capturability_score >= 0.75
if open_qual:
    open counter = 1
    state = OPENING
else:
    reset counters
    state = CLOSED
```

OPEN requires three qualifying observations through the OPENING persistence path. Candidate construction occurs only when the resulting state is OPEN and no current candidate exists.

| Gate | t1 | t2 |
|---|---:|---:|
| capturability | 0.22050421416872243 | 0.17666062360338286 |
| threshold | 0.75 | 0.75 |
| signed margin | -0.5294957858312775 | -0.5733393763966171 |
| qualifies | false | false |
| resulting state | CLOSED | CLOSED |
| candidate | null | null |

The decisive CLOSED condition for each is failure of `capturability >= 0.75`. `REVERSAL_PROPENSITY_HIGH` appears for both because reversal > 0.5; it is a reason code, not the state-transition condition that kept either observation CLOSED.

## D04 -> D03

D03 receives the complete 23-field evaluation, so changed raw capturability and aperture values remain in its input/fingerprint. Its ordered target resolver reads safety/staleness/projection first, then state:

- R10 emergency: false.
- R20 system disabled: false.
- R21 trading disabled: false.
- R30 safety/stale/invalid projection: false.
- R31 `new_envelope_state == CLOSED`: true for t1 and t2.

R31 returns D03 POSITION FLAT. It does not branch on raw capturability, aperture, reason codes, events, or D02 UPWARD direction. Candidate rules R34-R41 are not reached.

The controller then receives internal state FLAT and D03 POSITION FLAT for both, yielding NO_ACTION.

## Internal Response Versus Decision

1. Did APTF mathematically respond differently? **YES.**
2. Did D01 respond differently? **YES.**
3. Did D02 continuous output respond differently? **YES.**
4. Did D02 categorical direction respond differently? **NO.**
5. Did D04 capturability respond differently? **YES.**
6. Did D04 categorical state respond differently? **NO.**
7. Did D03 POSITION respond differently? **NO.**
8. Did Position Controller Decision respond differently? **NO.**

Same terminal decision does not mean same internal response.

## Decision Information Bottleneck

**DECISION INFORMATION BOTTLENECK:** D04 CLOSED/open hysteresis boundary, consumed by D03 R31.

**WHY:** Distinct capturability values both fail `capturability_score >= 0.75`; D04 emits the same `new_envelope_state=CLOSED` and no candidate. D03 R31 uses CLOSED and does not branch on raw capturability or D02 direction.

**UPSTREAM DIFFERENCES STILL PRESENT:** YES: volume influence, D01 state/scores, D02 displacement/interval and continuous fields, D04 structural/risk/capturability/aperture.

**DOWNSTREAM DISTINCTION LOST AT:** D04 `new_envelope_state=CLOSED`; D03 R31 fixes D03 POSITION FLAT.

## Volume Causality Conclusion

These two observations do **not** prove isolated volume causality on the final decision. Price, adaptive/kinematic state, perturbation class, prior persistence/uncertainty, and volume all changed, and no controlled counterfactual exists.

They do prove that volume entered real frozen D01 mathematics, updated persistent `volume_reference`, and influenced coherence and strength calculations. T1's updated reference was exactly consumed at t2. The share of any downstream observed delta caused by volume alone remains `CANNOT ISOLATE FROM STORED EVIDENCE`.

## Acceptance Gates

G01-G35: **35/35 PASS**.

- Stored Test 002 evidence verified before analysis.
- Complete source, D01, D02, D04, and D03 differentials produced.
- Volume path/state and D01/D04 continuity verified.
- Both capturability values reconstructed with zero error.
- Opening margins, reason codes, candidate-null path, R31, and bottleneck identified.
- No counterfactual, pipeline execution, market-row read, model/parameter change, trading heuristic, broker/Azure action, or profitability analysis occurred.
- Post-audit hash verification: **74/74 PASS** (67 bound mathematical/temporal/semantic/Test 001 references plus all seven pre-recorded Test 002 evidence hashes).

## Test Status

**PASS**

Next action: human review of D01 volume transformation, D01->D02 retention, continuous versus categorical D02 response, capturability, D04 gate, and D04->D03 bottleneck. No parameter change is proposed.

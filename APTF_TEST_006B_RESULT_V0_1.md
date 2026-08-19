# APTF Test 006B One-Way Reserve Validation Result V0.1

Status: **PASS**  
Acceptance: **120/120 PASS**

The exact frozen Test 006A Emitter processed all 101,221 reserve observations once: 15 initialization records and 101,206 actionable immutable emissions. BUY 14249, SELL 9779, HOLD 77178. Decision stream: **NON-DEGENERATE**.

Percentages: BUY `14.079204790229829%`, SELL `9.662470604509615%`, HOLD `76.25832460526055%`.

## Decision Dynamics

Total state changes between adjacent actionable decisions: `34,710`.

| Previous / Next | BUY | SELL | HOLD |
|---|---:|---:|---:|
| BUY | 3901 | 0 | 10348 |
| SELL | 0 | 2772 | 7007 |
| HOLD | 10348 | 7007 | 59822 |

Longest runs: BUY 8 observations / 420 source seconds; SELL 11 / 660 seconds; HOLD 44 / 204,780 seconds.

Direct BUY->SELL / SELL->BUY transitions: 0 / 0. HOLD-routed BUY->HOLD->SELL / SELL->HOLD->BUY reversals: 2051 / 2051.

Reserve Q_G/Q_S/Q_R/C ranges: {'minimum': 5.650984944039355e-05, 'maximum': 1.0} / {'minimum': 0.009344788745680531, 'maximum': 0.9215367319746877} / {'minimum': 0.0029624659141543924, 'maximum': 0.711335851223812} / {'minimum': 7.476458871570953e-06, 'maximum': 0.6185298431164367}. Historical C=0.75 gate was not used.

Primary human-readable output: `APTF_TEST_006B_OBSERVATIONS_WITH_EMITTED_POSITION_V0_1.csv`, with 101221 rows. The first 15 are INITIALIZING; all actionable rows contain BUY/SELL/HOLD. Runtime source-field mismatches: 0. CSV/emission decision mismatches: 0.

The CSV starts with all 22 original source columns in original order, followed only by emitter evidence fields. It contains no outcome, profit, correctness, or hindsight columns and was never used as Emitter input.

## Test 006A Comparison

| Decision | Development | Reserve | Difference, percentage points |
|---|---:|---:|---:|
| BUY | 13.2994923857868% | 14.079204790229829% | +0.7797124044430284 |
| SELL | 10.355329949238579% | 9.662470604509615% | -0.6928593447289639 |
| HOLD | 76.34517766497461% | 76.25832460526055% | -0.0868530597140591 |

Development versus reserve ranges respectively:

- Q_G: `0.024858610539630066–1.0` versus `0.00005650984944039355–1.0`.
- Q_S: `0.05711019382389611–0.9163818371091381` versus `0.009344788745680531–0.9215367319746877`.
- Q_R: `0.0039399589230584816–0.712611720830071` versus `0.0029624659141543924–0.711335851223812`.
- C: `0.0023286748222917037–0.6530244378797647` versus `0.000007476458871570953–0.6185298431164367`.

No retrospective similarity bands were imposed.

## Causality And Adaptation

- Rolling-context violations: 0.
- State-continuity violations: 0.
- Future-access violations: 0.
- Feedback-causality violations: 0 across 202,412 feedback events.
- Unexplained adaptations: 0 across 373,482 adaptive updates.
- Rule changes, resets, rewinds, and second passes: 0.
- Initialization/actionable nanosecond lifecycles: 15 / 101,206.
- Source span: `2023-03-30T08:00:00Z` through `2023-09-29T23:48:00Z`.

Frozen authority, source, Test 006A evidence, historical D04, and Test 005R identities are recorded in the post-execution integrity artifact. No rule, parameter, feedback, context, broker, or outcome logic changed.

Generalization result: the frozen mechanism remained operational, causal, state-continuous, and non-degenerate on unseen reserve data. This supports mechanism generalization only; it does not establish profitability or predictive accuracy.

## Generalization Findings

1. Every post-initialization reserve observation produced exactly one decision: **YES, 101,206/101,206**.
2. BUY observed: **YES, 14,249**.
3. SELL observed: **YES, 9,779**.
4. HOLD observed: **YES, 77,178**.
5. Decision stream non-degenerate: **YES**.
6. Adaptive values evolved under unchanged rules: **YES**.
7. Rolling aperture remained continuous: **YES**.
8. Fifteen-observation boundary resets: **0**.
9. Future observation influence: **0 violations**.
10. Test 006A rules remained unchanged: **YES, 26/26 frozen files**.
11. Reserve behavior differed modestly in proportions, reported above without retuning.
12. Q/C ranges differed, reported above.
13. Reversals continued to route through HOLD: BUY→HOLD→SELL `2051`; SELL→HOLD→BUY `2051`.
14. Direct BUY→SELL or SELL→BUY transitions: **0 / 0**.
15. Evidence **SUPPORTS** operational/causal generalization of the frozen Emitter to unseen data. It does not establish trading success.
16. The invariant original observation → frozen Emitter → final emitted position held for all 101,221 rows, with the first 15 explicitly INITIALIZING.
17. The primary CSV is a complete chronological original-observation plus emitted-position projection for every reserve observation.

Next action: **STOP**. Do not retune or run the reserve again.

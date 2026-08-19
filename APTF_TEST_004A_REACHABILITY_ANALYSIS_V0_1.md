# APTF Test 004A Backward Reachability Analysis V0.1

Status: PASS / MATHEMATICAL EVIDENCE ONLY
Primary result: RESULT B

## Exact Boundary

For each stored cycle:

$$
0.75=H\frac{|D|}{M}(s c p)^{1/3}\sqrt{(1-u)(1-r)}G,
$$

with the exact $M=0$ geometry branch, $H\in\{0,1\}$, and corrected $G$ over active known gates. Test 004 has $H=G=1$ in every cycle.

## Per-Cycle Boundary

| Cycle | Row | C actual | Shortfall | Target/actual | % target | QG actual/required | QS actual/required | QR actual/required |
|---:|---:|---:|---:|---:|---:|---|---|---|
| 1 | 10 | 0.22050421416872243 | 0.5294957858312775 | 3.401295539078111 | 29.40056188916299 | 1 / 3.401295539078111 | 0.6043625386410295 / 2.0556156066656563 | 0.36485420599454843 / 1.2409769832631439 |
| 2 | 11 | 0.17666062360338286 | 0.5733393763966171 | 4.2454282380651485 | 23.554749813784383 | 1 / 4.2454282380651485 | 0.3667482303751486 / 1.5570032934950782 | 0.48169454948065005 / 2.0449996424872214 |
| 3 | 12 | 0.25462532958949513 | 0.49537467041050487 | 2.945504287453035 | 33.95004394526602 | 1 / 2.945504287453035 | 0.5043730622546775 / 1.485633017346969 | 0.5048353067296146 / 1.4869945604297479 |
| 4 | 13 | 0.08848558708732783 | 0.6615144129126722 | 8.475956646587123 | 11.798078278310378 | 0.6832134425301885 / 5.79088751925142 | 0.2808653989173412 / 2.3806029447497816 | 0.46112417816135437 / 3.908468542788756 |
| 5 | 14 | 0.28034113293008417 | 0.46965886706991583 | 2.6753120106247366 | 37.37881772401122 | 1 / 2.6753120106247366 | 0.5555355673592773 / 1.486230975685502 | 0.5046321953114142 / 1.3500485730645544 |

Every one-factor required value exceeds 1. H and G are already at their maxima. Therefore no single-factor correction can reach 0.75 while all others remain actual.

## Structural Boundary

Required structural products $Q_S^3$ are 8.686117878610707, 3.774579645807116, 3.2789487474578998, 13.491520556633716, and 3.2829096126000543. Every value exceeds the legal product maximum 1. Holding two actual structural coordinates fixed produces required strength/coherence/persistence values above 1 in every cycle. Equal-contribution witnesses likewise require x=Q_S_required>1. Q_S-only and one-coordinate structural paths are impossible.

## Risk Boundary

Required complement products $Q_R^2$ are 1.5400238729888933, 4.182023537772864, 2.211152822747659, 15.276126349969264, and 1.8226311496336394. Every value exceeds legal maximum 1. Conditional required uncertainty and reversal values are negative in every cycle. Q_R-only and one-coordinate risk paths are impossible.

## Geometry Boundary

Q_G is $|D|/M$ with $|D|\le M$. Required Q_G values are 3.401295539078111, 4.2454282380651485, 2.945504287453035, 5.79088751925142, and 2.6753120106247366. At actual M these require $|D|>M$ in every cycle, violating ReturnShape geometry. Q_G-only is impossible.

## Unit-Bound Best Cases

| Cycle | C if QG=1 | C if QS=1 | C if QR=1 | QG+QS=1 | QG+QR=1 | QS+QR=1 | all quality=1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.22050421416872243 | 0.36485420599454843 | 0.6043625386410295 | 0.36485420599454843 | 0.6043625386410295 | 1.0 | 1.0 |
| 2 | 0.17666062360338286 | 0.48169454948065005 | 0.3667482303751486 | 0.48169454948065005 | 0.3667482303751486 | 1.0 | 1.0 |
| 3 | 0.25462532958949513 | 0.5048353067296146 | 0.5043730622546775 | 0.5048353067296146 | 0.5043730622546775 | 1.0 | 1.0 |
| 4 | 0.1295138262497199 | 0.3150462371955229 | 0.19189101608193135 | 0.46112417816135437 | 0.2808653989173412 | 0.6832134425301885 | 1.0 |
| 5 | 0.28034113293008417 | 0.5046321953114142 | 0.5555355673592773 | 0.5046321953114142 | 0.5555355673592773 | 1.0 | 1.0 |

Cycles 1,2,3,5 reach the unit-bound target only when Q_S and Q_R jointly become 1. Cycle 4 needs Q_G as well. These are legal-domain ceilings, not proven upstream states.

## Coupling And Reachability

Strength depends on coherence, volume influence, kinematics, and prior uncertainty. Coherence depends on the same level/velocity/acceleration/volume evidence. Persistence is recursive and kinematic. Uncertainty depends on coherence/innovation/perturbation. Reversal depends on uncertainty/persistence/kinematics. D and M share one FMO path. Therefore factors are not freely independent.

Declared unit-bound maximum is 1.0. Maximum proven reachable under frozen D01/D02 equations is **NOT DERIVABLE FROM CURRENT FROZEN AUTHORITY**. Consequently 0.75 is not proven unreachable, but actual joint upstream reachability is not proven either.

## Opening Persistence

Current authority requires three consecutive C>=0.75 evaluations from CLOSED to reach OPEN. Test 004 threshold hits: 0. Longest qualifying run: 0. OPENING counter-1 occurrences: 0. OPENING counter-2 occurrences: 0. OPEN occurrences: 0.

## Classification

**RESULT B: THRESHOLD ALGEBRAICALLY REACHABLE, BUT THE FIVE TEST-004 OBSERVATIONS REQUIRE LARGE JOINT DEPARTURES FROM THEIR ACTUAL UPSTREAM STATE.**

This result does not tune or recommend a threshold and does not prove actual D01/D02 joint reachability.

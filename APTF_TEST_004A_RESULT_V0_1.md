# APTF Test 004A Five-Cycle Backward Opening-Boundary Result V0.1

Status: PASS
Primary result: **RESULT B**
Date: 2026-08-18

## Discipline And Authority

Mathematical analysis only. Pipeline executions: 0. New market rows read: 0. Stored rows represented: 10-14. Row 15 unread. No code/config/test/data changes, counterfactual pipeline run, synthetic market value, tuning, scan, profitability, broker, or Azure activity.

Test 004 evidence: 12/12 files identified and hashed. Corrected authority: 10/10 artifact bindings and 9/9 implementation bindings verified before analysis.

Authoritative formula:

$$C=H Q_G Q_S Q_R G$$

$$Q_G=0\ (M=0),\ \text{else }|D|/M;\quad Q_S=(scp)^{1/3};\quad Q_R=\sqrt{(1-u)(1-r)}.$$

Test 004 uses H=1 and corrected G=min(data_integrity)=1 for every cycle.

## Actual Distance And Required Q Factors

| Cycle | C | Shortfall | Target/actual | % target | QG actual/required | QS actual/required | QR actual/required |
|---:|---:|---:|---:|---:|---|---|---|
| 1 | 0.22050421416872243 | 0.5294957858312775 | 3.401295539078111 | 29.40056188916299 | 1 / 3.401295539078111 | 0.6043625386410295 / 2.0556156066656563 | 0.36485420599454843 / 1.2409769832631439 |
| 2 | 0.17666062360338286 | 0.5733393763966171 | 4.2454282380651485 | 23.554749813784383 | 1 / 4.2454282380651485 | 0.3667482303751486 / 1.5570032934950782 | 0.48169454948065005 / 2.0449996424872214 |
| 3 | 0.25462532958949513 | 0.49537467041050487 | 2.945504287453035 | 33.95004394526602 | 1 / 2.945504287453035 | 0.5043730622546775 / 1.485633017346969 | 0.5048353067296146 / 1.4869945604297479 |
| 4 | 0.08848558708732783 | 0.6615144129126722 | 8.475956646587123 | 11.798078278310378 | 0.6832134425301885 / 5.79088751925142 | 0.2808653989173412 / 2.3806029447497816 | 0.46112417816135437 / 3.908468542788756 |
| 5 | 0.28034113293008417 | 0.46965886706991583 | 2.6753120106247366 | 37.37881772401122 | 1 / 2.6753120106247366 | 0.5555355673592773 / 1.486230975685502 | 0.5046321953114142 / 1.3500485730645544 |

No Q_G-only, Q_S-only, Q_R-only, G-only, or H-only path is legal for any cycle.

## Structural Boundary

| Cycle | Actual s*c*p | Required product | Ratio | Feasible within unit bounds |
|---:|---:|---:|---:|---|
| 1 | 0.22074588189713787 | 8.686117878610707 | 39.3489464173027 | NO |
| 2 | 0.04932920097716235 | 3.774579645807116 | 76.51815904244245 | NO |
| 3 | 0.1283085658302477 | 3.2789487474578998 | 25.555181964982378 | NO |
| 4 | 0.022156171562309476 | 13.491520556633716 | 608.9283303612139 | NO |
| 5 | 0.17144925713708212 | 3.2829096126000543 | 19.14799554934908 | NO |

Holding the other two structural coordinates actual, all required strength, coherence, and persistence values exceed 1. Equal-contribution x=Q_S_required also exceeds 1.

## Risk Boundary

| Cycle | Actual complement product | Required product | Ratio | Feasible within unit bounds |
|---:|---:|---:|---:|---|
| 1 | 0.13311859163191236 | 1.5400238729888933 | 11.568811344152662 | NO |
| 2 | 0.23202963899936643 | 4.182023537772864 | 18.023660924560946 | NO |
| 3 | 0.25485868692078406 | 2.211152822747659 | 8.675995507404211 | NO |
| 4 | 0.2126355076849845 | 15.276126349969264 | 71.84184107482443 | NO |
| 5 | 0.25465365254481737 | 1.8226311496336394 | 7.157294354192969 | NO |

All equal-contribution uncertainty witnesses and conditional uncertainty/reversal solutions are negative, outside `[0,1]`, when other factors remain actual.

## Best-Case Classification

No single factor at unit maximum reaches 0.75. Setting Q_S=Q_R=1 reaches C=1 for cycles 1,2,3,5 because Q_G=1. Cycle 4 reaches only C=0.6832134425301885 under Q_S=Q_R=1 and also requires Q_G improvement. All-quality unit-bound ceiling is 1 for every cycle.

These values establish algebraic unit-bound feasibility only. They do not establish joint D01/D02 reachability.

## Coupling And Proven Reachability

Q_G, strength, coherence, persistence, uncertainty, and reversal share adaptive reference/scale, kinematics, volume influence, innovation/perturbation, and recursive state. Coherence enters strength; coherence affects uncertainty; uncertainty affects reversal; D and M share one FMO path. Independent adjustment is not authorized.

Declared unit-bound maximum: 1.0. Proven reachable maximum: **NOT DERIVABLE**. Whether 0.75 is below a proven reachable maximum: **NOT DETERMINABLE**. Threshold mathematically proven unreachable: **NO / NOT PROVEN**.

## Opening Persistence

Three consecutive C>=0.75 evaluations are required from CLOSED to reach OPEN. Actual Test 004 threshold hits: 0. Longest qualifying run: 0. OPENING counter-1: 0. OPENING counter-2: 0. OPEN: 0.

## Primary Result

**RESULT B: THRESHOLD ALGEBRAICALLY REACHABLE, BUT THE FIVE TEST-004 OBSERVATIONS REQUIRE LARGE JOINT DEPARTURES FROM THEIR ACTUAL UPSTREAM STATE.**

The five cycles were 0.46965886706991583 to 0.6615144129126722 below target and required multiplicative improvements of 2.6753120106247366 to 8.475956646587123. No single factor can close any gap legally. Four cycles can meet the unit-bound target only with Q_S and Q_R jointly at 1; cycle 4 also requires Q_G. Whether frozen upstream dynamics can generate these combinations simultaneously remains unknown. Therefore 0.75 is not proven unreachable, and no replacement threshold is proposed.

## Acceptance

G01-G60: **60/60 PASS**.

Post-analysis non-drift audit: Test 004 artifacts 12/12 unchanged by analysis; corrected authority bindings 10/10; corrected implementation bindings 9/9; protected source/D01/D02/D04-config/D03/controller/temporal core 7/7 present and untouched. Pipeline executions: 0. Market rows read: 0. Row 15 read: NO. No new system freeze is created.

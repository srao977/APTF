# APTF D04-D03 Responsibility Classification V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## D04 classifications

| Property family | Responsibility classification | Required upstream of current D03 target? | How |
|---|---|---|---|
| `ReturnShape.path_direction` | ANALYTICAL DIRECTION | YES for ordinary LONG/SHORT/analytical FLAT | copied into qualified candidate |
| terminal/max displacement | ANALYTICAL DIRECTION + ANALYTICAL CAPTURABILITY | YES indirectly | sign creates direction; absolute ratio enters $Q_G$ |
| strength/coherence/persistence | ANALYTICAL CAPTURABILITY | YES indirectly | $Q_S -> B -> C -> state/candidate$ |
| uncertainty/reversal propensity | ANALYTICAL CAPTURABILITY | YES indirectly | $Q_R -> B -> C -> state/candidate$ |
| $Q_G,Q_S,Q_R,B$ | ANALYTICAL CAPTURABILITY | YES indirectly | candidate permitting/suppressing |
| projection time/validity | DATA VALIDITY | YES | $H$/safety; D03 R30 |
| market eligibility/data integrity | DATA VALIDITY + EXTERNAL ACTIONABILITY | YES | $H/G$/safety |
| liquidity/spread/latency/execution/broker | EXECUTION FEASIBILITY | YES in current architecture | $G -> C -> candidate$ |
| capital/portfolio/position/risk capacity | RISK/CAPACITY | YES in current architecture | $G -> C -> candidate$ |
| `clock_event_quality` | OTHER diagnostic | NO target effect | no score/state branch |
| open/close thresholds and counters | HYSTERESIS/CONTROL | YES | decide OPEN/OPENING/CLOSING/CLOSED |
| aperture | HYSTERESIS/CONTROL diagnostic smoothing | NO target effect | emitted but no state/candidate/D03 branch |
| candidate existence/status | CANDIDATE TRANSPORT | YES | direct D03 target facts |
| candidate identity/source/qualification time | CANDIDATE TRANSPORT/lineage | NO target value; YES lineage | fingerprint/audit |
| reason codes/events/gate diagnostics | OTHER audit | NO target effect | not branched by D03 |

## D03 classifications

| Property | Responsibility | Effect on desired |
|---|---|---|
| emergency/system/trading controls | HYSTERESIS/CONTROL (D03 control) | override/preserve target |
| actual position | execution/position state | affects desired only under disabled preservation; otherwise transition only |
| pending target/decision | transition control | no target effect |
| execution availability | authorization | no target effect; blocks transition |
| D04 safety/state/candidate | factual decision boundary | ordinary target selection |

## Aperture conclusion

`aperture_after` is emitted to D03 as part of the full immutable object/fingerprint, but `_resolve_target_rule` never reads it. Aperture does not directly or indirectly affect candidate qualification in the current implementation because hysteresis runs from $C$ before aperture and candidate creation checks only resulting envelope state.

## Direct answers

1. LONG versus SHORT ordinary sign: qualified candidate `path_direction`.
2. $B$ determines permission to reach a candidate, not sign.
3. $H/G$ do not determine sign.
4. External fields cannot reverse sign.
5. They can withhold/invalidate candidate.
6. D03 cannot produce ordinary analytical LONG/SHORT without qualified candidate; disabled preservation can output LONG/SHORT from actual state.
7. Analytical FLAT exists through QUALIFIED candidate direction FLAT.
8. Actual position affects ordinary transition, and affects desired only under disabled preservation.
9. Pending/execution states do not alter desired; they prevent/delay transition.
10. Minimal analytical sign information: D02 `path_direction`; current frozen ordinary target additionally needs D04 valid OPEN + QUALIFIED candidate and D03 enabled/no-emergency controls.

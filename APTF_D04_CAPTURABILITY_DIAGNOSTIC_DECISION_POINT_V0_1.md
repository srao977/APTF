# APTF D04 Capturability Diagnostic Decision Point V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Required target summary

| Property | Target A | Target B |
|---|---:|---:|
| timestamp | 2022-09-30T08:16:00Z | 2022-09-30T08:17:00Z |
| D02 `path_direction` | UPWARD | UPWARD |
| $C$ | 0.4814590392445292 | 0.3605075262704571 |
| $G$ | 1.0 | 1.0 |
| aperture after | 0.3965569449721373 | 0.37853223562129723 |
| open threshold | 0.75 | 0.75 |
| close threshold | 0.55 | 0.55 |
| prior envelope state | CLOSED | CLOSED |
| persistence counters before | open 0 / close 0 | open 0 / close 0 |
| candidate condition | false: post-state not OPEN | false: post-state not OPEN |
| candidate created | NO | NO |
| candidate qualified | NOT REACHED | NOT REACHED |
| final envelope state | CLOSED | CLOSED |

## Required C-input summary

| C input | Source | Target A | Target B | Changed? | Effect on C | Semantic classification |
|---|---|---:|---:|---|---|---|
| $D$ | D02 terminal displacement | 0.489964861958388 | 0.3183024678069359 | YES | Ratio unchanged because $D=M$ | D02 RETURN-SHAPE DESCRIPTION |
| $M$ | D02 max displacement | 0.489964861958388 | 0.3183024678069359 | YES | Ratio unchanged | D02 RETURN-SHAPE DESCRIPTION |
| $s$ | D01 strength | 0.8043937518637954 | 0.8976642163450754 | YES | Raises structural factor all else equal | D01 ANALYTICAL STATE |
| $c$ | D01 coherence | 0.9999999907876206 | 0.9999931783150069 | YES | Slightly lowers structural factor | D01 ANALYTICAL STATE |
| $p$ | D01 persistence | 0.6840391573948615 | 0.6672308993184185 | YES | Lowers structural factor | D01 ANALYTICAL STATE |
| $u$ | D01 uncertainty | 0.296755743816712 | 0.2727585484077373 | YES | Raises risk-quality factor all else equal | D01 ANALYTICAL STATE |
| $r$ | D01 reversal propensity | 0.5091154115712131 | 0.7484880373502629 | YES | Lowers risk-quality factor | D01 ANALYTICAL STATE |
| $Q_G$ | D04 geometry transform | 1.0 | 1.0 | NO | Neutral | D04 ANALYTICAL/CAPTURABILITY STATE |
| $Q_S$ | D04 structure transform | 0.8194388482618388 | 0.8429381315925792 | YES | Increased | D04 ANALYTICAL/CAPTURABILITY STATE |
| $Q_R$ | D04 degradation transform | 0.5875472468333434 | 0.4276796988520893 | YES | Decreased | D04 ANALYTICAL/CAPTURABILITY STATE |
| projection-valid inputs | observation/D02 | true | true | NO | $H$ remains 1 | MARKET OBSERVATION + D02 |
| market eligible | D04 context | true | true | NO | $H$ remains 1 | D04 EXTERNAL CONTEXT |
| data integrity | row-derived context | 1.0 | 1.0 | NO | $H,G$ remain 1 | MARKET OBSERVATION |
| valid inputs | D04 validation | true | true | NO | $H$ remains 1 | D04 ANALYTICAL/CAPTURABILITY STATE |
| nine non-data gate fields | fixed D04 context | all 1.0 | all 1.0 | NO | $G$ remains 1 | D04 EXTERNAL/EXECUTION CONTEXT |
| frozen critical threshold | D04 config | 0.2 | 0.2 | NO | Integrity indicator remains 1 | OTHER |

## Exact reconstruction result

Both runtime values match direct Python floating-point evaluation exactly:

- A: `1 * (1 * 0.8194388482618388 * 0.5875472468333434) * 1 = 0.4814590392445292`.
- B: `1 * (1 * 0.8429381315925792 * 0.4276796988520893) * 1 = 0.3605075262704571`.

$$
\Delta C=-0.12095151297407208.
$$

The multiplicative cause is $Q_S$ ratio `1.0286772873663315` combined with $Q_R$ ratio `0.7279069064779394`, giving net ratio `0.7487813020109447`. $H$, $G$, and $Q_G$ are unchanged at one.

## Direction result

`path_direction` does not enter $C$. $Q_G$ discards sign with `abs(D)`. Therefore:

- two UPWARD observations can have different $C$: YES;
- UPWARD and DOWNWARD can have the same $C$: YES, when absolute geometry and all other inputs match.

## Threshold result

`0.75` is a frozen configuration threshold on normalized capturability, not a 75% probability. Authority records that it was inherited and not validated for the redesigned score at design time; no empirical probability rationale is provided. `0.55` is the asymmetric close threshold. Counters `3/2` count consecutive qualifying D04 evaluations.

## Capturability classification

**D. MIXTURE OF ANALYTICAL CAPTURABILITY AND EXECUTION/ACTIONABILITY.**

$B$ is analytical path capturability. $H$ and $G$ add causal eligibility, integrity, execution, capital, portfolio, risk, and broker feasibility. Final $C$ combines them before candidate creation.

## Architectural finding

**FINDING D: D04 C MIXES ANALYTICAL CAPTURABILITY AND EXTERNAL EXECUTION/ACTIONABILITY CONCERNS.**

The current frozen contract intentionally uses this mixed score before D03 desired-position determination. D03 receives direction only through a qualified candidate and has no independent pre-gate desired-position field.

## Non-change declaration

No implementation, configuration, threshold, model, schema, D03 context, ActualPosition, Position Controller, broker simulation, tuning, full replay, or freeze change occurred.

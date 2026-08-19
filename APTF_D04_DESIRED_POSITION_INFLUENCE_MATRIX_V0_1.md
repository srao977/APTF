# APTF D04 Desired-Position Influence Matrix V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Formula and control properties

| Property/parameter | Source | Responsibility | Affects C? | Affects candidate creation/qualification? | Affects sign? | Can prevent LONG/SHORT? | Can cause D03 non-direction/FLAT path? | Read directly by D03? |
|---|---|---|---|---|---|---|---|---|
| `path_direction` | D02 | ANALYTICAL DIRECTION / CANDIDATE TRANSPORT | NO | transported only after qualification | YES | Not by value; sign selects target | FLAT sign -> analytical FLAT | candidate copy YES |
| `terminal_displacement`, `maximum_absolute_displacement` | D02 | ANALYTICAL CAPTURABILITY; sign validation | via $Q_G$ | YES | terminal sign creates D02 direction; $Q_G$ discards sign | YES through $C$ | YES via suppression; zero geometry | NO raw |
| strength/coherence/persistence | D01/D02 | ANALYTICAL CAPTURABILITY | via $Q_S$ | YES | NO | YES | YES via suppression | NO raw |
| uncertainty/reversal propensity | D01/D02 | ANALYTICAL CAPTURABILITY | via $Q_R$ | YES | NO | YES | YES via suppression | NO raw |
| $Q_G$ | D04 | ANALYTICAL CAPTURABILITY | YES | YES | NO | YES | YES via suppression | NO target branch |
| $Q_S$ | D04 | ANALYTICAL CAPTURABILITY | YES | YES | NO | YES | YES via suppression | NO |
| $Q_R$ | D04 | ANALYTICAL CAPTURABILITY | YES | YES | NO | YES | YES via suppression | NO |
| $B=Q_GQ_SQ_R$ | D04 | ANALYTICAL CAPTURABILITY | YES | YES | NO | YES | YES via suppression | NO |
| $H$ | D04 | DATA VALIDITY / ELIGIBILITY | YES | YES/hard safety | NO | YES | YES via safety/closure | NO value; D03 reads safety/projection facts |
| $G$ | D04 | EXTERNAL ACTIONABILITY / EXECUTION / CAPACITY | YES | YES | NO | YES | YES via suppression | NO |
| $C=HBG$ | D04 | MIXED CAPTURABILITY/ACTIONABILITY | final | drives hysteresis | NO | YES | YES via state/candidate | NO score branch |
| `open_threshold=0.75` | config | HYSTERESIS/CONTROL | NO | YES | NO | YES | YES via CLOSED/OPENING | NO |
| `close_threshold=0.55` | config | HYSTERESIS/CONTROL | NO | YES/invalidation lifecycle | NO | YES after prior OPEN | YES via CLOSING/CLOSED | NO |
| open persistence `3` | config/state | HYSTERESIS/CONTROL | NO | delays OPEN/candidate | NO | YES | YES via OPENING | NO |
| close persistence `2` | config/state | HYSTERESIS/CONTROL | NO | delays closure/invalidation | NO | can retain candidate temporarily | eventually CLOSING/CLOSED | NO |
| aperture alpha/value | config/state | HYSTERESIS/CONTROL diagnostic smoothing | NO | NO in implementation | NO | NO | NO | NO target branch |
| candidate creation rule | D04 | CANDIDATE TRANSPORT | NO | requires post-state OPEN and no current candidate | copies sign | YES if not reached | YES | candidate fact YES |
| supersession/staleness/safety | D04 | DATA VALIDITY / CANDIDATE LIFECYCLE | through $H$/safety | invalidates/withholds | NO | YES | YES | resolved facts YES |

## EnvelopeContext leaves

| Fields | Classification | Enter | Determine sign? | Withhold candidate? | D03 reads directly? |
|---|---|---|---|---|---|
| `evaluation_time` | DATA VALIDITY | projection validity / $H$ | NO | YES | only resolved evaluation time/lifecycle |
| `market_eligible` | EXTERNAL ACTIONABILITY / DATA VALIDITY | $H$ / safety | NO | YES | NO raw |
| `data_integrity` | DATA VALIDITY | $H$ and $G$ | NO | YES | NO raw |
| `clock_event_quality` | OTHER diagnostic | no score | NO | NO | NO |
| liquidity/spread/latency/execution/broker | EXECUTION FEASIBILITY | $G$ | NO | YES | NO |
| capital/portfolio/position/risk capacity | RISK/CAPACITY | $G$ | NO | YES | NO |

When permissive, external gate fields become neutral ($G=1$) but remain part of the formal formula. They never determine LONG versus SHORT.

## Category result

### Category A: direction-determining

- D02 `path_direction` only (created from signed terminal displacement and transported by D04 candidate).

### Category B: direction-permitting/suppressing

- all analytical $B$ leaves/transforms;
- $H/G/C$ and their active context leaves;
- open/close thresholds and persistence state;
- safety, staleness, supersession, envelope/candidate lifecycle;
- candidate existence/status.

### Category C: irrelevant to D03 desired target

- `clock_event_quality` under current implementation;
- aperture before/after and aperture alpha;
- D04 score diagnostics/reason/event fields after state/candidate are resolved;
- identity/provenance fields except for validation/lineage, not target choice.

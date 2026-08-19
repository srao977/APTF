# APTF Historical versus Live Context Classification V0.1

Status: DIAGNOSTIC / DESIGN REVIEW ONLY. NOT FROZEN AUTHORITY.

## Scope

This classifies the 13 frozen `EnvelopeContext` fields against the existing SPY normalized OHLCV dataset. It does not fabricate values or define a new replay policy.

## Field classification

| D04 field | Frozen semantic owner/use | Historical classification for existing dataset | Legitimately available now? | Notes |
|---|---|---|---|---|
| `evaluation_time` | Projection validity and event time | HISTORICALLY OBSERVABLE | YES | Use causal source timestamp |
| `market_eligible` | Hard eligibility $H$ | UNKNOWN / REQUIRES DESIGN DECISION | NO | Session labels exist, but frozen authority defines no historical mapping for eligibility, halts, permissions, or event exclusions |
| `data_integrity` | Hard eligibility $H$ and minimum gate $G$ | CAUSALLY DERIVABLE FROM EXISTING HISTORICAL DATA, WITH LIMITED SOURCE EVIDENCE | PARTIALLY | Existing `data_valid`/quality flags can support a defined mapping; the frozen context does not itself define that mapper |
| `clock_event_quality` | Diagnostic synchronization quality; not score-active | UNKNOWN / REQUIRES DESIGN DECISION | NO | Existing timestamps do not establish feed synchronization/event quality semantics |
| `liquidity_quality` | Minimum gate $G$ | UNKNOWN / REQUIRES DESIGN DECISION | NO | One-minute OHLCV lacks bid/ask depth and displayed/estimated liquidity evidence |
| `spread_quality` | Minimum gate $G$ | UNKNOWN / REQUIRES DESIGN DECISION | NO | Existing dataset has no bid/ask spread |
| `latency_quality` | Minimum gate $G$ | LIVE EXECUTION ENVIRONMENT ONLY | NO | Historical bars have no receive/submission latency observations |
| `execution_feasibility` | Minimum gate $G$ | LIVE EXECUTION ENVIRONMENT ONLY | NO | Requires a causal execution environment or separately designed simulator |
| `capital_available` | Minimum gate $G$ | ACCOUNT / PORTFOLIO STATE | NO | No account ledger exists in OHLCV |
| `portfolio_capacity` | Minimum gate $G$ | ACCOUNT / PORTFOLIO STATE | NO | Requires portfolio state |
| `position_capacity` | Minimum gate $G$; explicitly not a position decision | ACCOUNT / PORTFOLIO STATE | NO | Requires position/allocation policy and ledger |
| `risk_capacity` | Minimum gate $G$ | ACCOUNT / PORTFOLIO STATE | NO | Requires risk-policy state |
| `broker_health` | Minimum gate $G$ | BROKER STATE | NO | No broker state exists in historical OHLCV |

Counts:

- Historically observable or causally derivable: 2.
- Live/account/broker only: 7.
- Unknown/requires design decision for the existing dataset: 4.
- Fixed configuration already authorized for historical replay: 0.

## What can participate in a faithful historical D04 replay?

Only context values backed by causal historical evidence or an explicitly frozen replay policy can participate. With the current dataset, `evaluation_time` is directly available and limited `data_integrity` may be causally derived if an authoritative mapping is adopted. The other 11 fields are not supplied by the existing dataset under frozen semantics.

The D04 modernization authority requires all 13 fields and states that they are identical in replay/feed operation. It does not authorize replacing unavailable values with perfect constants.

## Desired-position-only replay question

Under the frozen architecture, the operational fields are not irrelevant to desired position. They enter $G$, then $C$, hysteresis, envelope state, and candidate existence; D03 derives LONG/SHORT only from an OPEN qualified candidate. Omitting those fields changes D04/D03 semantics.

If the desired experiment is instead:

> What position would the analytical direction imply while ignoring live execution, capital, portfolio, risk, and broker feasibility?

that experiment is **DESIGN POLICY UNRESOLVED**. It is not the existing frozen D04/D03 contract. Defining it would require a reviewed analytical-only boundary, scenario policy, or alternate output; this audit does not choose one.

## Existing all-FLAT file

The 106,603-row file was produced with synthetic perfect D04 operational context and explicit replay control state. It is therefore:

- classification C: output contaminated by synthetic operational context;
- consequently classification D for real historical interpretation: not a genuine point-in-time historical desired-position stream.

It remains deterministic evidence of the particular synthetic best-case-envelope scenario that was run. It is not evidence that D01/D02 were analytically FLAT, and it is not a faithful execution-gated historical output because the execution/account/broker context was not historically observed.

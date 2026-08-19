# APTF D04 Context Contribution Matrix V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

| EnvelopeContext field | Participates in C? | Participates in G? | Participates elsewhere? | Can change C? | Can prevent candidate? | Can change path_direction? |
|---|---|---|---|---|---|---|
| `evaluation_time` | YES, through $H$ projection validity | NO | Output time, staleness/safety | YES | YES | NO |
| `market_eligible` | YES, through $H$ | NO | Immediate safety closure/reason/event | YES | YES | NO |
| `data_integrity` | YES, through $H$ and $G$ | YES | Safety reason and gate diagnostics | YES | YES | NO |
| `clock_event_quality` | NO | NO | Required diagnostic context only | NO | NO | NO |
| `capital_available` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `portfolio_capacity` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `position_capacity` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `liquidity_quality` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `spread_quality` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `latency_quality` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `execution_feasibility` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `risk_capacity` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |
| `broker_health` | YES, through $G$ | YES | Gate diagnostics/reason | YES | YES | NO |

## Target values

All ten gate dimensions, including row-derived data integrity, equal `1.0` for both targets, so $G=1.0$. `market_eligible=true`, projection is valid, and data integrity exceeds `0.2`, so $H=1$. `clock_event_quality=1.0` is not score-active.

Therefore fixed context participates structurally in $C$, but is multiplicatively neutral for these targets. It did not cause closure.

## Path direction

No context field can change `ReturnShape.path_direction`. D04 validates direction against the sign of terminal displacement and, if a candidate is created, copies it verbatim. Invalid context can suppress/invalidate the candidate rather than rewriting direction.

## Semantic classification

- `evaluation_time`, `market_eligible`, and `data_integrity`: D04 causal operational/safety context.
- liquidity/spread/latency/execution/broker: D04 external execution feasibility.
- capital/portfolio/position/risk: D04 external allocation/capacity context.
- `clock_event_quality`: causal synchronization diagnostic.

This external contribution is why final $C$ is broader than pure analytical shape capturability.

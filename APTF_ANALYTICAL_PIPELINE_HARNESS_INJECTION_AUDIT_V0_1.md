# APTF Analytical Pipeline Harness Injection Audit V0.1

Diagnostic only. No implementation authority.

## Result

Diagnostic status: **FAIL**. The executed D01/D02 diagnostic used zero mock values, but the audited six-month replay path declares 13 mock/synthetic values required to reach D04/D03. Therefore the complete replay path does not satisfy the requested absolute zero-mock gate.

## Source -> D01 adapter values

| Field | Value/rule | Destination | Reason | Authority | Classification |
|---|---|---|---|---|---|
| entity_id | SPY | NormalizedObservation | Replay instrument | Harness constructor | EXPLICIT CONFIGURATION |
| event_time | parsed source UTC | NormalizedObservation | D01 timestamp | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| receive_time | event_time | NormalizedObservation | Source lacks receive timestamp | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| sequence_id | zero-based source index | NormalizedObservation | Causal ordering | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| price | source close | NormalizedObservation | Existing mapping | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| volume | source volume | NormalizedObservation | Frozen input field | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| bid / ask | null | NormalizedObservation | Not present in source | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| bid_size / ask_size | null defaults | NormalizedObservation | Not present in source | Dataclass defaults | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| session | source session_type | NormalizedObservation | Existing mapping | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| source_quality | 1.0 if data_valid else 0.5 | NormalizedObservation | Quality mapping | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |
| availability_mask | price=true, volume=true | NormalizedObservation | Source columns present | Existing mapper | REQUIRED AUTHORITATIVE ADAPTER VALUE |

## D04 mock/synthetic context values (11)

| Field | Value | Destination | Reason/authority | Classification |
|---|---:|---|---|---|
| market_eligible | true | EnvelopeContext | Hard-coded by replay; no source | MOCK/SYNTHETIC VALUE |
| clock_event_quality | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| capital_available | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| portfolio_capacity | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| position_capacity | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| liquidity_quality | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| spread_quality | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| latency_quality | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| execution_feasibility | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| risk_capacity | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |
| broker_health | 1.0 | EnvelopeContext | Hard-coded perfect condition | MOCK/SYNTHETIC VALUE |

## D03 mock/synthetic values (2)

| Field | Value | Destination | Reason/authority | Classification |
|---|---:|---|---|---|
| position_candidate_id | D04C|SPY|0.0|0.0 | DecisionContext for LONG/SHORT | Code explicitly labels it synthetic | MOCK/SYNTHETIC VALUE |
| position_source_return_shape_model_time | 0.0 | DecisionContext for LONG/SHORT | Fabricated pre-row-1 time | MOCK/SYNTHETIC VALUE |

Other D03 values (`LONG` initial position, `NONE` pending target, null pending ID, and five execution/control booleans) are harness **EXPLICIT CONFIGURATION** rather than market-derived observations. This diagnostic did not use any of them.

## Unauthorized replay configuration deviation

The replay overrides D04 critical data-integrity thresholds from repository default `0.2` to `0.0`. Classification: **UNAUTHORIZED DEFAULT**. This is separate from the count of 13 mock/synthetic payload values.

## Totals

- Mock/synthetic values declared by audited replay path: **13**
- Mock/synthetic values used by this stopped diagnostic execution: **0**
- Position controller invocations: **0**
- Implementation changes: **NONE**
- Freeze changes: **NONE**

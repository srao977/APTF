# D04 Human Boundary Decisions v0.2

## 1. Status

**Status:** HUMAN-APPROVED BOUNDARY AUTHORITY; FREEZE CANDIDATE

This record resolves interface I1, interface I2, and lifecycle L1. It does not change approved capturability mathematics or authorize implementation.

## 2. I1 — Final D04Context

D04Context has 13 required typed fields: `evaluation_time`, `market_eligible`, `data_integrity`, `clock_event_quality`, `liquidity_quality`, `spread_quality`, `latency_quality`, `execution_feasibility`, `broker_health`, `capital_available`, `portfolio_capacity`, `position_capacity`, and `risk_capacity`.

Four are causal operational, five execution feasibility, and four portfolio capacity. All constrain whether the current ReturnShape can be captured, so none moves to D03. Rename legacy `timestamp` to `evaluation_time`; remove untyped metadata. No hidden or optional dictionary is permitted.

## 3. I2 — Final D04 output

D04Evaluation has exactly 23 top-level factual fields: 4 identity/time, 7 capturability, 4 envelope state/aperture, 4 lifecycle/safety, 1 optional typed CandidateEnvelope, and 3 event/diagnostic fields. It contains zero D03 decision fields.

Retire legacy `shape_quality`, `shape_component`, `envelope_component`, `lifetime_component`, local position state, and HOLD/REDUCE/MODIFY/EXIT commitment semantics. D04 reports facts; D03 decides actions.

## 4. CandidateEnvelope and identity

D04 owns candidate formation. The minimal CandidateEnvelope has five fields: `candidate_id`, `entity_id`, `source_return_shape_model_time`, `qualified_at`, and `status`.

Identity is:

```text
D04C|percent_encode_utf8(entity_id)|format17g(source_return_shape_model_time)|format17g(qualified_at)
```

The encoding is deterministic, locale-independent, replay-stable, human-auditable, and uses no random UUID, outcome, or wall clock. Candidate identity never affects capturability.

## 5. L1 — Stale-state response

Staleness is a safety condition. A stale shape cannot qualify new capture and bypasses ordinary close persistence.

| Prior state | Response |
|---|---|
| CLOSED | Remain CLOSED |
| OPENING | Force CLOSED immediately |
| OPEN | Force CLOSED immediately |
| CLOSING | Force CLOSED immediately |

For all cases: set aperture exactly to `0.0`, reset hysteresis counters, invalidate any candidate, and emit `SHAPE_STALE`; also emit `ENVELOPE_CLOSED` if prior state was non-CLOSED and `CANDIDATE_INVALIDATED` if applicable. This is factual envelope safety, not a D03 exit decision.

## 6. Supersession

A newer valid same-entity ReturnShape supersedes the older shape immediately. Invalidate the old shape's candidate, emit factual supersession/invalidation events, and evaluate the new shape without forcing CLOSED solely due to supersession. A new candidate may form only after the new shape satisfies normal D04 qualification.

## 7. Context-only reevaluation

Use the latest non-superseded ReturnShape. Check inclusive projection validity before evaluation. If valid, reevaluate normally; if stale, apply the safety response.

## 8. Recovery

After stale safety closure, a new valid ReturnShape begins from CLOSED and must satisfy normal opening persistence. Previous OPEN state, aperture, hysteresis memory, or candidate identity is not restored.

## 9. D03 boundary

D04 owns capturability, feasibility, lifecycle, aperture, hysteresis, envelope state, candidate identity, and factual events. D03 owns positions, orders, BUY/SELL/HOLD/ENTER/EXIT/REDUCE/REVERSE, action selection, and any future reward/risk decision semantics.

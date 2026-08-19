# APTF D04 Known-Input Context Contract V0.2.2

Status: VERSIONED DESIGN CORRECTION
Date: 2026-08-18

## Governing Invariant

Every active numeric D04 runtime input must have legitimate provenance. Unavailable is not numeric zero, numeric one, false, or true. Future context does not participate until an authoritative producer supplies a value and provenance.

This contract corrects the V0.2 mandatory-context absence gap. Frozen V0.2/V0.2.1 artifacts remain historical authority for their original contract and are not silently rewritten.

## Context Value Fields

The thirteen scientific/context fields remain: `evaluation_time`, `market_eligible`, `data_integrity`, `clock_event_quality`, `capital_available`, `portfolio_capacity`, `position_capacity`, `liquidity_quality`, `spread_quality`, `latency_quality`, `execution_feasibility`, `risk_capacity`, and `broker_health`.

`evaluation_time` and `data_integrity` remain required. The other eleven fields may be null only with `UNAVAILABLE` provenance. Two control fields are added: `context_role` and complete `provenance` classification.

Allowed provenance: `OBSERVED`, `DERIVED`, `STATE`, `MATHEMATICAL_CONSTANT`, `TEST_FIXTURE`, `UNAVAILABLE`.

Production context rejects `TEST_FIXTURE`. A null value must be `UNAVAILABLE`; an `UNAVAILABLE` field must be null.

## Active Evidence

For production:

```text
ACTIVE = non-null fields with recognized non-test provenance
UNAVAILABLE = null fields with UNAVAILABLE provenance
```

Current real-market active context is:

- `evaluation_time`: DERIVED from provider event time parsing;
- `data_integrity`: DERIVED from normalized `data_valid` through source quality.

Current unavailable context is:

- market eligibility;
- clock/event quality;
- liquidity, spread, latency, and execution feasibility;
- capital, portfolio, position, and risk capacity;
- broker health.

These concepts remain defined for future use.

## G Applicability

The configured ten conceptual dimensions remain unchanged. For each evaluation:

```text
G_active = min(value for configured gate dimension if value is active and known)
```

Unavailable fields are excluded, not assigned 0 or 1. The active set must not be empty. In the present production contract, required known `data_integrity` is configured as a gate, proving at least one active dimension. An empty set raises an explicit error.

## H Applicability

Projection validity, data integrity, valid finite inputs, and any available market-eligibility fact participate. When `market_eligible` is unavailable, it is omitted; it is neither true nor false. If known false, H is zero. The data-integrity threshold is loaded from authoritative config.

## Non-Drift

Q_G, Q_S, Q_R, B, thresholds 0.75/0.55, hysteresis counts 3/2, aperture alpha 0.5, candidate logic, D01/D02/D03/controller mathematics, and temporal instrumentation are unchanged. Only context applicability/provenance and removal of the proof-only integrity override are corrected.

## Historical Interpretation

Tests 001-003A used fixed neutral context. Their payload arithmetic remains reproducible and internally correct, but their G=1/H=1 context authority was placeholder-affected. With the corrected active set and their known valid `data_integrity=1`, corrected G and H remain 1, so stored C arithmetic does not change. Historical evidence is not rewritten.

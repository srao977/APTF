# APTF D04 Fixed Context Contract Audit V0.1

Status: EXPERIMENTAL / DIAGNOSTIC. NOT FROZEN PRODUCTION AUTHORITY.

## Authority gate

| Component | Version | Authority | SHA256 | Result |
|---|---|---|---|---|
| D01 | v0.2 | `D01_PRE_STAGE_3_ARCHITECTURE_FREEZE_V0_1.json` | `b6ed942e41ec1c72350cf9247597e5819a942dbe9d04770c23e243204165b235` | PASS |
| D02 | v0.2 | `D02_RETURNSHAPE_IMPLEMENTATION_V0_2_FREEZE.json` | `c8029c4b9608547bbf7960f05e4f8613480c4fb2bf8594d94482516b954f7e72` | PASS |
| D04 | v0.2.1 | `D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json` | `f72a86b3085bd11d8626f06f1fe3faedde60570365488176011239382a46f1af` | PASS |
| D03 | v0.1 | `D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json` | `6a93291ffe555a3fff1239a9a4f88c0a1546b6c46a02b60586614b60a3c91ad6` | PASS |

## Runtime contract

Runtime type: `aptf_d04.models.envelope_context.EnvelopeContext`.

Pydantic configuration forbids extra fields and non-finite values. All 13 fields are required; none has a runtime default.

| Field | Type / legal domain | Validation/default | Mathematical use | Threshold/rule | More permissive direction | Can suppress candidate/actionability? | Can affect path_direction? | Experiment classification |
|---|---|---|---|---|---|---|---|---|
| `evaluation_time` | finite float | required | Projection validity and D04 event time | valid iff `evaluation_time <= model_time + projection_interval` | Current causal timestamp, not optimized | YES, if stale | NO | REAL OBSERVATION-DERIVED |
| `market_eligible` | bool | required | Hard eligibility $H$ and safety closure | must be true for $H=1$ | `true` | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `data_integrity` | float `[0,1]` | required | Hard eligibility $H$ and minimum gate $G$ | must be `>0.2`; warning if gate `<0.5` | larger | YES | NO | REAL CAUSALLY DERIVABLE |
| `clock_event_quality` | float `[0,1]` | required | Diagnostic only; not score-active | none | no score direction; `1.0` denotes non-restrictive quality boundary | NO | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `capital_available` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `portfolio_capacity` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `position_capacity` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `liquidity_quality` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `spread_quality` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `latency_quality` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `execution_feasibility` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `risk_capacity` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |
| `broker_health` | float `[0,1]` | required | minimum gate $G$ | warning if minimum gate `<0.5` | larger | YES | NO | FIXED PERMISSIVE EXPERIMENTAL CONTEXT |

Classification counts: 1 real observation-derived, 1 real causally derivable, 11 fixed permissive experimental, 0 unresolved within D04.

## Fixed mechanic

The ten numeric fixed context fields are set to `1.0`, the legal upper bound. Nine enter $G=\min(g_1,\ldots,g_{10})$ and are monotonically non-restrictive at the upper bound. `clock_event_quality` is diagnostic only; `1.0` is legal and cannot alter score or direction. `market_eligible=true` is required for $H=1$.

The tenth gate coordinate, `data_integrity`, is not fixed. It uses the existing causal mapper: `1.0` when the current source row says `data_valid=true`, otherwise `0.5`. The two targets both derive `1.0`.

## Frozen configuration used unchanged

- critical data integrity: `0.2`
- gate warning: `0.5`
- hysteresis open/close: `0.75 / 0.55`
- open/close persistence: `3 / 2`
- aperture alpha: `0.5`

No threshold or configuration override was applied.

## Separate D03 contract blocker

D03 requires a 12-field `DecisionContext`. It includes `actual_position_state`, position candidate lineage, pending target/decision state, `execution_available`, `system_enabled`, `trading_enabled`, `emergency_flatten`, and `control_state_valid`.

The experiment authorizes controlled artificial quantities only for D04 and explicitly says ActualPosition is not used. Therefore no legitimate D03 input can be constructed under the stated constraints. This is not a D04 fixed-value problem; it is the first downstream contract blocker.

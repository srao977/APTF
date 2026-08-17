# D03 Input Contract v0.1

## Status

**PROPOSED DESIGN; FREEZE-READY FOR HUMAN REVIEW; NOT FROZEN.**

```text
D03Input_t = (D04Evaluation_t, DecisionContext_t)
```

`D04Evaluation_t` is the complete frozen 23-field D04 output. D03 receives no direct D01 or D02 object.

## DecisionContext fields

| Field | Type/range | Required | Source/owner | Classification | Causal purpose |
|---|---|---:|---|---|---|
| `context_time` | finite float seconds | Yes | causal control-event clock | `REQUIRED_FOR_DECISION` | Decision/commitment event time; must be `>= D04.evaluation_time` |
| `entity_id` | non-empty string | Yes | position/control ledger | `REQUIRED_FOR_DECISION` | Explicit join guard; must equal D04 entity |
| `actual_position_state` | `FLAT|LONG|SHORT` | Yes | authoritative position ledger | `REQUIRED_FOR_DECISION` | Current realized control state |
| `position_candidate_id` | string or null | Yes | position ledger | `REQUIRED_FOR_DECISION` | Origin candidate lineage; null iff FLAT |
| `position_source_return_shape_model_time` | finite float or null | Yes | position ledger | `REQUIRED_FOR_DECISION` | Origin shape lineage; null iff FLAT |
| `pending_target_state` | `NONE|FLAT|LONG|SHORT` | Yes | execution controller | `REQUIRED_FOR_DECISION` | Normalized target already in progress; avoids duplicate action commitments |
| `pending_decision_id` | string or null | Yes | execution controller | `REQUIRED_FOR_DECISION` | Lineage for pending target; null iff pending target is NONE |
| `execution_available` | bool | Yes | execution adapter/controller | `BELONGS_TO_EXECUTION_ADAPTER` | Whether a new transition may presently be authorized |
| `system_enabled` | bool | Yes | operator/system control | `REQUIRED_FOR_DECISION` | Global D03 control enable |
| `trading_enabled` | bool | Yes | operator/risk policy | `REQUIRED_FOR_DECISION` | Position-changing intent enable |
| `emergency_flatten` | bool | Yes | operator/risk control | `REQUIRED_FOR_DECISION` | Highest-priority explicit FLAT target |
| `control_state_valid` | bool | Yes | position/execution reconciler | `REQUIRED_FOR_DECISION` | Whether position/pending facts are trustworthy |

All 12 fields are causal at `context_time`, deterministic inputs, and replay/live identical.

## Cross-field invariants

- Context and D04 entity IDs must match.
- `context_time >= D04.evaluation_time`.
- FLAT requires null position candidate and source-shape lineage; LONG/SHORT requires both.
- `pending_target_state=NONE` iff `pending_decision_id=null`.
- A non-NONE pending target must be the target of the referenced committed decision.
- `control_state_valid` must be true before policy evaluation and commitment.
- `emergency_flatten` overrides disabled flags as a desired FLAT target; execution availability still controls authorization.
- When emergency flatten is false, either disabled flag preserves `actual_position_state`, produces NO_CHANGE, and creates no pending/deferred target from D04 changes.

## Excluded candidate fields

| Proposed information | Classification | Reason |
|---|---|---|
| D04 liquidity/spread/latency/capital/risk values | `DUPLICATES_D04_CONTEXT` | Already incorporated into frozen capturability |
| raw pending order type/price/venue/quantity | `BELONGS_TO_EXECUTION_ADAPTER` | Broker mechanics, not decision science |
| max concurrent positions/portfolio allocation | `BELONGS_TO_PORTFOLIO/RISK_MANAGER` | Initial one-entity target contract does not size or allocate |
| raw price, D01 state, D02 samples/direction | `BELONGS_UPSTREAM` | No silent upstream bypass |
| future observations/outcomes/benchmarks/P&L | `FUTURE/PROHIBITED` | Causal leakage |
| numeric exposure/quantity/entry price | `UNNECESSARY` | No sizing or cost model in first-pass D03 |
| transaction costs/slippage/commission | `BELONGS_TO_EXECUTION_ADAPTER` | Future replay/execution assumptions |
| capturability threshold or D03 score | `UNNECESSARY` | D04 candidate qualification is authoritative |

## Directional authority

Direction is not a DecisionContext field. It is the immutable factual `D04Evaluation.candidate_envelope.path_direction` propagated from source D02 ReturnShape. D03 has zero direct D02 inputs and performs no directional inference.

## Prohibited inputs

No future value, outcome label, benchmark decision, P&L, reserve value, recommendation, random value, wall-clock-only creation time, hidden metadata, replay flag, or direct D01/D02 coordinate is admitted.

## Invalid input boundary

Schema or semantic boundary failure produces no committed D03Decision. This includes missing/extra fields, unknown enums, invalid scalar domains, entity/time mismatch, position/pending lineage inconsistency, and `control_state_valid=false`. D03 fabricates no desired state and does not use BLOCKED for invalid input.

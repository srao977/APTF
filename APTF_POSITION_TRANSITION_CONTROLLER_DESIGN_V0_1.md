# APTF Position Transition Controller Design v0.1

## Canonical name and architecture

The canonical component name is **Position Transition Controller**. No D-number is assigned.

```text
Committed D03 DecisionRecord
  + authoritative ActualPosition snapshot
  -> Position Transition Controller
  -> immutable PositionTransitionPlan
  -> Human Advice | Replay Simulator | Broker Adapter
```

## Responsibility

The controller validates lineage, compares actual and desired states, derives the frozen transition class and primitive sequence, and preserves D03 authorization. It is deterministic and stateless over explicit inputs. It performs no market interpretation, sizing, routing, fill assumption, or profitability evaluation.

## Input reconciliation

A plan requires a complete committed D03 record, its canonical content hash, and an authoritative actual-position snapshot with identity/version. Entity must match. The snapshot state must equal `DecisionRecord.prior_position_state`; otherwise the decision is stale relative to execution state and processing fails closed with no plan. Unknown state never means FLAT.

## Derivation

1. Validate the D03 record, decision identity/hash, actual-position identity/version, entity, and position domain.
2. Select the unique base matrix row from actual state and `desired_position_state`.
3. Check D03 transition consistency. OPEN/CLOSE/REVERSE must agree with the base class; RETARGET may select the base changing sequence after pending-state reconciliation; BLOCKED must represent a changing base sequence; NO_CHANGE is aligned or already pending.
4. Apply D03 authorization:
   - authorized OPEN/CLOSE/REVERSE/RETARGET -> `READY`, base verbs;
   - aligned NO_CHANGE -> `NON_EXECUTABLE_NO_CHANGE`, HOLD/NO_ACTION;
   - T10/`TRANSITION_ALREADY_PENDING` -> `PENDING_ALREADY`, empty verbs;
   - BLOCKED -> `BLOCKED`, base required verbs retained but non-executable.
5. Compute deterministic transition identity and emit an immutable plan.

Only `READY` plus `action_authorized=true` permits adapter submission. A plan never proves execution occurred.

## Idempotence and ordering

Identity binds originating D03 decision ID/hash, actual-position identity/version, state pair, class, verbs, and status. Reprocessing identical inputs returns identical semantic identity. Consumers enforce uniqueness by transition ID. Plans preserve D03 decision-time order per entity. A later decision cannot bypass an unreconciled earlier READY/pending transition; current actual/pending authority must first be reconciled. This contract defines no queue.

## Invalid inputs

Malformed records, missing identity, unknown positions, entity mismatch, stale actual-position version/state, inconsistent transition intent, or unsupported fields fail closed and emit no plan. No defaulting, coercion, or recovery trade is allowed.

## D03 interactions

Emergency flatten needs no special controller policy: D03 desired FLAT maps through the matrix. Disabled decisions are aligned NO_CHANGE and become HOLD/NO_ACTION. BLOCKED is never executable or queued. No deferred target exists. RETARGET is a new authorized intent only after external pending-state reconciliation.

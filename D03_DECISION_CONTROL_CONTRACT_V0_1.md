# D03 Decision and Control Contract v0.1

## Status

**PROPOSED; FREEZE-READY FOR HUMAN REVIEW; NOT FROZEN.**

## Responsibility

D03 deterministically maps `(D04Evaluation, DecisionContext)` to an immutable decision/control record. It chooses a desired position state and describes the transition from current factual control state. It is neither a predictor nor an order generator.

## Canonical ontology

### Desired position state

`FLAT | LONG | SHORT`

This is the primary control result.

### Transition intent

`NO_CHANGE | OPEN | CLOSE | REVERSE | RETARGET | BLOCKED`

Transition intent is derived from desired state, actual state, pending target, and authorization context. It is not an order. `MAINTAIN` is deliberately not a separate action: an aligned LONG or SHORT is represented by unchanged desired state, `NO_CHANGE`, and `POSITION_ALREADY_ALIGNED`.

### Authorization

`action_authorized` is true only when a position-changing or retargeting intent may be handed to a future adapter now. `NO_CHANGE` and `BLOCKED` are never executable. BLOCKED is reserved for schema-valid input with a deterministically known actionable transition whose execution is unavailable. It is a committed audit fact, not a queued action. Invalid input is rejected before commitment and never emits BLOCKED.

## Target hierarchy

0. Schema and semantic boundary validation: reject invalid input with no committed record.
1. `emergency_flatten=true`: desired `FLAT` regardless of D04; execution availability still determines authorization.
2. `system_enabled=false` or `trading_enabled=false`: preserve actual state, emit NO_CHANGE, authorize no transition, and create no deferred target.
3. D04 stale, safety-closed, projection-invalid, non-OPEN, candidate absent, or candidate not `QUALIFIED`: desired `FLAT`.
4. D04 OPEN plus QUALIFIED candidate:
   - factual `UPWARD` orientation -> desired `LONG`;
   - factual `DOWNWARD` orientation -> desired `SHORT`;
   - factual `FLAT` orientation -> desired `FLAT`;

D03 never uses capturability components or score thresholds to override this hierarchy.

Disabled preservation is control suspension, not a market opinion. D01/D02/D04 continue evaluating. D04 closure, staleness, invalidation, or a new directional candidate cannot change the preserved target while disabled. On re-enable, D03 evaluates only the current D04 evaluation; missed transitions are not replayed.

## Transition derivation

After target selection:

- pending target non-NONE and differs from desired -> `RETARGET`;
- pending target non-NONE and equals desired -> `NO_CHANGE`, unauthorized, `TRANSITION_ALREADY_PENDING`;
- desired equals actual -> `NO_CHANGE`, unauthorized;
- FLAT actual to LONG/SHORT target -> `OPEN`, authorized;
- LONG/SHORT actual to FLAT target -> `CLOSE`, authorized;
- LONG actual to SHORT target or inverse -> `REVERSE`, authorized.
- after transition derivation, execution unavailable converts OPEN/CLOSE/REVERSE/RETARGET to `BLOCKED`, unauthorized.

`REVERSE` means desired opposite state. A future controller determines safe close/open sequencing and reports updated actual/pending state. D03 does not submit two orders or assume atomic broker execution.

## Candidate relationship

D04 owns candidate identity and qualification. Candidate lineage follows the authority that caused the target. D03:

- preserves current D04 candidate ID/source lineage for ordinary QUALIFIED UPWARD, DOWNWARD, and FLAT target rules, including FLAT/NO_CHANGE;
- emits null candidate lineage for emergency flatten, disabled preservation, safety/non-OPEN, absent-candidate, and invalidated-candidate target rules;
- never creates, rewrites, requalifies, or resurrects a D04 candidate;
- treats supersession as a new current-fact evaluation, not automatic failure.

## Lifecycle semantics

Only current `OPEN` plus a current QUALIFIED directional candidate authorizes directional exposure. `CLOSED`, `OPENING`, and `CLOSING` target FLAT. A stale/safety closure with LONG/SHORT actual state therefore derives CLOSE when execution and controls permit. With FLAT actual state it derives NO_CHANGE.

## Initialization and state

D03 is stateless. Initial context is FLAT with null position lineage and no pending target, unless an authoritative reconciler supplies an existing position. Recovery requires no hidden D03 reset; each event is evaluated from explicit current facts.

## Decision commitment

Each unique canonical input fingerprint produces one deterministic decision identity. The record is committed before future outcome access. Re-delivery of identical input is idempotent: it returns the same identity and must not append a second commitment.

The target-rule reason is always primary. Supporting reasons are duplicate-free and ordered as target detail, transition reason, then authorization-overlay reasons. Rule identity is exactly `TARGET:<target>|TRANSITION:<transition-or-NONE>|OVERLAYS:<ordered-overlays-or-NONE>`.

## Versioning

- D03 model/control version: `D03_CONTROL_V0_1_DESIGN`
- decision rule version: `D03_RULES_V0_1_DESIGN`
- output schema version: `D03_DECISION_SCHEMA_V0_1`

These are design identifiers, not frozen production versions. Any later semantic change requires explicit version change.

## Explicit exclusions

No broker, venue, order type, route, limit/stop/take-profit price, submitted quantity, sizing, cost model, fill prediction, reward/risk score, confidence score, expected return, P&L, outcome, or benchmark field is produced.

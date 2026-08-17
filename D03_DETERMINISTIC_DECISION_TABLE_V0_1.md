# D03 Deterministic Decision Table v0.1

## Status

**PROPOSED HIERARCHICAL TABLE; FREEZE-READY FOR HUMAN REVIEW; NOT FROZEN.** Candidate orientation is supplied by the six-field D04 v0.2.1 CandidateEnvelope.

## Evaluation order

Schema and semantic validation occurs first. Invalid input produces no decision record. For valid input, the first matching target rule wins, transition rules compare desired with pending or actual state, and authorization overlays run last. Every unique valid input produces an idempotently committed record, including NO_CHANGE and BLOCKED.

`D03_DETERMINISTIC_DECISION_TABLE_V0_1.json` is the canonical rule authority.

## A. Control override and validity rules

| Priority | Condition | Desired state | Intent/authorization | Primary reason |
|---:|---|---|---|---|
| Boundary | schema/invariant failure or `control_state_valid=false` | none | reject; no committed record | none |
| 0 | `emergency_flatten=true` | FLAT | derive transition; execution-gated | `EMERGENCY_FLATTEN` |
| 1 | `system_enabled=false` | reported actual; no deferred target | `NO_CHANGE`, false | `SYSTEM_DISABLED` |
| 2 | `trading_enabled=false` | reported actual; no deferred target | `NO_CHANGE`, false | `TRADING_DISABLED` |

Emergency flatten is distinct and higher priority. Disabled preservation applies regardless of D04 state/candidate changes and is control suspension, not market opinion.

## B. D04 target rules

| D04 current state/fact | Candidate | Orientation | Desired state | Primary reason |
|---|---|---|---|---|
| safety closed, stale, or projection invalid | any | any | FLAT | `D04_SAFETY_CLOSED`; exact non-null D04 safety reason is supporting |
| CLOSED | any | any | FLAT | `ENVELOPE_CLOSED` |
| OPENING | any | any | FLAT | `ENVELOPE_NOT_QUALIFIED` |
| CLOSING | any | any | FLAT | `ENVELOPE_CLOSING` |
| OPEN | absent | none | FLAT | `NO_VALID_CANDIDATE` |
| OPEN | INVALIDATED | any | FLAT | `CANDIDATE_INVALIDATED` |
| OPEN | QUALIFIED | FLAT | FLAT | `CANDIDATE_NON_DIRECTIONAL` |
| OPEN | QUALIFIED | UPWARD | LONG | `CANDIDATE_QUALIFIED` |
| OPEN | QUALIFIED | DOWNWARD | SHORT | `CANDIDATE_QUALIFIED` |

Orientation is exactly `candidate_envelope.path_direction`; D03 performs no lookup or inference.

D03 does not inspect score magnitude, gates, aperture, or events to manufacture qualification.

## C. Position transition matrix

Applies after a resolved target and before execution gating.

| Actual | Desired FLAT | Desired LONG | Desired SHORT |
|---|---|---|---|
| FLAT | `NO_CHANGE` | `OPEN` | `OPEN` |
| LONG | `CLOSE` | `NO_CHANGE` | `REVERSE` |
| SHORT | `CLOSE` | `REVERSE` | `NO_CHANGE` |

Aligned non-FLAT state uses reason `POSITION_ALREADY_ALIGNED`; aligned FLAT uses `POSITION_ALREADY_FLAT`.

## D. Pending transition rules

| Rule | Formal condition | Intent | Reason |
|---|---|---|---|
| T00 | `pending_target_state != NONE AND desired_position_state != pending_target_state` | RETARGET | `PENDING_TARGET_CONFLICT` |
| T10 | `pending_target_state != NONE AND desired_position_state == pending_target_state` | NO_CHANGE | `TRANSITION_ALREADY_PENDING` |
| T20-T23 | `pending_target_state == NONE` | NO_CHANGE/OPEN/CLOSE/REVERSE from 3x3 matrix | matrix reason |

Authorization overlay A00 applies after transition derivation: if execution is unavailable and intent is OPEN, CLOSE, REVERSE, or RETARGET, final intent is BLOCKED, unauthorized, with supporting reason `EXECUTION_UNAVAILABLE`. A blocked target is not queued. A later execution-availability event reruns D03 against then-current facts.

## E. Required lifecycle cases

- CLOSED plus no position: FLAT, NO_CHANGE.
- CLOSED/stale/safety plus LONG or SHORT: FLAT, CLOSE if authorized; BLOCKED otherwise.
- OPENING: FLAT; no preparatory directional action.
- OPEN plus qualified UPWARD/DOWNWARD candidate and FLAT: LONG/SHORT OPEN respectively.
- OPEN plus matching position: same desired state, NO_CHANGE.
- OPEN plus opposing position: desired opposite state, REVERSE; adapter sequences close/open.
- CLOSING: FLAT, closing existing position when authorized.
- Supersession with same orientation: preserve directional target; usually NO_CHANGE.
- Supersession with opposite orientation: desired opposite target; REVERSE when authorized.
- Supersession with no new qualified candidate: FLAT; CLOSE existing position when authorized.

## F. Candidate lineage

Candidate lineage follows target authority:

- emergency flatten and disabled preservation: null;
- ordinary QUALIFIED UPWARD/DOWNWARD/FLAT: current D04 candidate ID and source model time;
- safety, CLOSED, OPENING, CLOSING, absent candidate, or invalidated candidate: null.

## G. Commitment policy

All rows use `COMMIT_IF_NEW_INPUT_FINGERPRINT`. Repeated identical inputs and rule version yield the same decision ID and no duplicate durable append. Future outcomes are unavailable until append succeeds.

For every committed record:

- primary reason is the resolved target-rule reason;
- supporting reasons are ordered target detail, transition reason, authorization overlays, duplicate-free and excluding primary;
- decision rule ID is `TARGET:<target>|TRANSITION:<transition-or-NONE>|OVERLAYS:<ordered-overlays-or-NONE>`.

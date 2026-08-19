# APTF Position Action Stream Semantics Audit v0.1

## Frozen concepts

D03 owns an immutable desired-position state stream: FLAT, LONG, or SHORT. D03 separately records `transition_intent` and `action_authorized`. Aligned position and target produce NO_CHANGE and are not executable.

The Position Transition Controller maps state pairs to a plan. Its frozen matrix assigns:

- FLAT -> FLAT: NO_ACTION;
- LONG -> LONG and SHORT -> SHORT: HOLD;
- changing pairs: position-changing primitive verbs.

The controller design states that only READY plus `action_authorized=true` may be submitted. HOLD and NO_ACTION remain meaningful non-executable plan semantics.

## Why HOLD and NO_ACTION are zero in the CSV

The harness invokes the controller for every fabricated post-gate dictionary, but writes a value only inside `if plan.action_authorized`. It blanks all non-executable plans. Exact suppressed plan counts are:

- NO_ACTION: 27,850;
- HOLD: 20,097.

Thus zero HOLD and zero NO_ACTION are explained by the CSV's authorized-action-only policy, not by absence of those state relationships.

## Correct interpretation

The current `APTF_position_action` column behaves as a **new authorized execution-instruction event**, not a continuous position-advice column. A human-facing diagnostic may eventually need to distinguish current desired position from new execution action, but this audit makes no output change or redesign.

**D03 desired-position stream and position-action event stream are DISTINCT.**

The frozen architecture supports records such as desired LONG plus no new authorized action when actual state is already LONG. Blank execution action does not imply absent desired position.

# APTF Position Controller Single-Input Temporal Contract V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Input

`PositionTransitionController.derive_transition_plan` receives:

1. complete committed D03 record as a dictionary;
2. actual-position snapshot;
3. supplied D03 decision hash.

The D03 dictionary contains `decision_time=t`, D03 decision ID, fingerprints, and D04 source times. The controller directly reads/copies `decision_time` and decision ID. It does not consume D01/D02/D04 objects or preserve their fields individually.

## Output

Runtime type: `PositionTransitionPlan`.

Temporal field:

- `decision_time=1664525760.0`, copied from D03 `decision_time`; Category F inherited from original A under the current caller.

Identity/parent fields:

- `transition_id`: controller-generated hash-derived ID;
- `originating_d03_decision_id`: preserved parent ID;
- `originating_d03_decision_hash`: preserved supplied parent hash.

The output does not contain D01 trace/state identity, D02 identity as a separate field, D04 evaluation fingerprint as a separate field, candidate ID, or source D04 times. They are at most indirectly committed inside the D03 parent record/hash.

No controller `received_at`, `emitted_at`, or processing duration exists.

## Terminal semantic output distinction

The plan's `ordered_execution_verbs` are traceable to the plan and D03 parent, and the plan preserves numeric $t$. A bare string returned by `serialize_verbs` contains only verb text and carries neither time nor identity. The historical CSV separately pairs a source timestamp column with an action column, but the verb value itself has no lineage field.

Therefore a terminal verb is tied to InputObservation(t) **PARTIALLY**:

- YES within the complete `PositionTransitionPlan`/output-row container via decision time and D03 parent;
- NO as a detached serialized verb;
- not cryptographically end-to-end to the original source row because upstream identity was dropped at D01->D02.

Position Controller processing latency: NOT COMPUTABLE.

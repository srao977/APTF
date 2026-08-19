# APTF Position Execution State Authority v0.1

## Ownership

- D03 owns immutable `desired_position_state` and decision authorization.
- The position/execution ledger owns `ActualPosition`, actual-position identity/version, completed-step history, and pending execution facts.
- The Position Transition Controller owns only deterministic plans.
- A future adapter/simulator reports execution results; it does not revise D03.

ActualPosition represents confirmed established exposure. It is never inferred from desired state, D04 state, submitted intent, or an unacknowledged action. Desired LONG does not make actual LONG.

## Snapshot contract

A controller input snapshot must include non-empty entity and position identity, monotonic nonnegative version, one state from FLAT/LONG/SHORT, and causal effective time. The snapshot state must equal the committed D03 `prior_position_state`. A mismatch requires reconciliation and yields no plan.

## State updates

ActualPosition changes only after confirmed successful primitive execution. HOLD and NO_ACTION do not change it. Each confirmed change advances the ledger version. Partial reversal success is represented exactly: after a successful close and failed open, actual state is FLAT.

Unknown actual position is an invalid authority state, not FLAT. No position-changing action is authorized until reconciliation restores a valid snapshot.

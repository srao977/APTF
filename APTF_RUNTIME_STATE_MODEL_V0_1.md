# APTF Runtime State Model V0.1

## A. Market Observation

Immutable source-derived input for one entity and timestamp. It is validated before mathematics and is not runtime feedback.

Persistence: source systems may persist it; the core retains only the completed scientific context required by authority.

## B. Rolling historical context

Exactly 15 prior completed scientific records once initialized. It contains observation IDs, source timestamps, C, path direction, and frozen fields required by adaptive operators. O_n is absent while O_n is evaluated and enters only after completion.

Persistence: required across calls.

## C. Adaptive Emitter recursive state

Contains completed count, prior terminal decision, legacy internal-controller feedback state, D01 state, last source timestamp, and context linkage. Values evolve; rule definitions do not.

Persistence: required across calls. The legacy internal-controller state is not PositionState.

## D. Emitter Decision

Actionable terminal vocabulary: BUY, SELL, HOLD. Initialization has no decision. It is an immutable output fact and input to the Position State Operator, not a broker action.

Persistence: previous decision is retained only where frozen feedback authority requires it.

## E. Position State

Production long-only vocabulary: FLAT, LONG. It represents the state carried between Position Operator calls. SHORT is absent.

Persistence: required across calls and separate from EmitterState.

## F. Position Transition

Immutable result containing state_before, emitter_decision, state_after, structural classification, and execution_intent. It describes one deterministic application and is not itself persistent mutable state.

## G. Execution Intent

Broker-neutral vocabulary: BUY, SELL, NONE. It is derived from state change only. It contains no price, quantity, account, or fill.

Persistence: optional downstream event evidence; not input to Emitter mathematics.

## H. Feedback carried forward

Completed emission n may set previous decision and legacy internal-controller state for n+1. It may not rewrite n or access future observations. Production PositionState updates after the separate operator application.

## State ownership

`RuntimeCore` owns one isolated sequence: D01 model state, RollingContext, EmitterState, PositionState, and last source time. No module-level mutable state participates. Recreating a runtime instance is an explicit reset; normal processing never resets at row-count boundaries.

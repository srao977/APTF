# APTF Test 009 Plan V0.1

## Purpose and boundaries

Test 009 diagnoses whether immutable BUY/HOLD/SELL and Test 007 episodes align with causal local first- and second-derivative states of SPY's observed price process. It does not modify Runtime Core V0.1, rerun the reserve Emitter, retune any rule, add SHORT, optimize P&L, or fit a production curve.

## Authority

- Frozen Runtime Core V0.1: 22-file freeze inventory.
- Immutable Test 006B 101,221-row observation/emission evidence.
- Test 007 2,051 episodes and 101,221-row state map.
- Test 008 2,051-row P&L ledger, joined only after derivative choices are fixed.
- Derivative price: preserved source `close`, the authoritative numeric mapping to D01 `price` for each completed observation.
- Time: actual `event_timestamp_utc`; provider-event ordering authority, not a claim that timestamps are exchange bar-close instants.

## Ordered procedure

1. Verify and capture Runtime Core and Test 006B/007/008 hashes.
2. Fit causal trailing quadratics at windows 3, 5, 8, and 15 using current and prior rows only and actual elapsed minutes.
3. Calculate raw backward D1, fit failures, signs, zero crossings, sign changes, reversal rate, and persistence for each window.
4. Select the primary window using only the predeclared stability rule in the derivative method document.
5. Calculate the primary D1 empirical distribution and 5th/10th/15th percentiles of absolute D1. Fix the 10th percentile as the primary near-zero threshold before reading Emitter alignment or P&L.
6. Assign derivative states and identify crossings/cycles/precursors. Initialization rows may supply causal context but are excluded from crossing/cycle/alignment scoring.
7. Join frozen Test 007 episodes and, only descriptively after all derivative definitions are fixed, Test 008 trade results.
8. Generate turning trajectories at relative observations -15 through +15. Future-relative rows are explicitly retrospective trajectory evidence and never enter primary derivative calculation.
9. Recompute all immutable hashes and stop for human review.

## Stop conditions

Stop for any Runtime/hash change, Emitter invocation, future row in a primary fit, centered smoother, timestamp substitution, missing required source field, episode/decision/state change, incomplete output, or derivative selection based on emission/P&L results.

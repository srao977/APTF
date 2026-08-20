# APTF Test 008 Plan V0.2

## Purpose

Measure the gross economic consequence of consuming immutable Test 006B decisions through the frozen Runtime Core V0.1 long-only Position State Operator with fixed 100-share, next-chronological-observation provider-OPEN execution.

## Immutable inputs

- Runtime Core V0.1 freeze manifest and 22-file hash inventory.
- Test 007A consolidation/equivalence authority.
- Test 007 101,221-row observation map and 2,051-episode ledger.
- Test 006B immutable observation/emission CSV.

The Adaptive Emitter will not run. Runtime Core source, Emitter mathematics/state/context/feedback, Position State Operator, decisions, and historical evidence will not be modified.

## Required order

1. Verify all frozen Runtime Core hashes and capture Test 006B/007/007A authority hashes.
2. Verify 101,221 chronological SPY rows, provider `open` availability, 15 leading INITIALIZING rows, and 101,206 actionable rows.
3. Replay actionable state-before plus immutable decision through `aptf_runtime.position.apply_position_decision` and require exact Test 007 state/classification equality.
4. Audit next-row OPEN availability and pending collisions without calculating P&L.
5. Stop if initialization exclusion, structural counts, episode linkage, next-row availability, or collision count fails.
6. Only after the structural gate passes, execute pending BUY/SELL intents at the next chronological row's provider `open`, fixed quantity 100.
7. Produce complete observation, execution-event, trade, cumulative-P&L, monthly, edge-case, reconciliation, and summary evidence.
8. Recompute frozen Runtime Core and historical authority hashes. Require zero changes.

## Numeric policy

Source prices and all dollar/notional calculations use Python `Decimal` constructed directly from source strings. No intermediate rounding occurs. Three P&L methods must be exactly equal. Descriptive means, medians, population standard deviation, rates, and profit factor are serialized as decimal strings; undefined values are JSON null with an explicit reason.

## Execution ordering

At O_(n+1), first fill a pending intent from O_n at provider `open` of O_(n+1), persist the execution, and update simulated quantity. Then audit O_(n+1)'s immutable decision and potentially create the next pending intent. Desired Runtime Position State and simulated executed quantity remain separate.

## Stop conditions

Stop before P&L for any Runtime hash mismatch, non-leading initialization row, replay mismatch, structural-count mismatch, unavailable required OPEN, pending collision, missing episode, SHORT/quantity violation, or required semantic invention.

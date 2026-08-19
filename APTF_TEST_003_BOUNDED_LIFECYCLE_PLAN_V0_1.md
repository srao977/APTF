# APTF Test 003 Bounded Lifecycle Plan V0.1

Status: EXECUTED READ-ONLY TEST EVIDENCE
Date: 2026-08-18

## Scope

Starting at physical CSV row 10, process at most five consecutive one-minute observations in one continuing frozen runtime. Complete E0-E5 for each reached row. Stop immediately after the first Position Controller Decision containing BUY, HOLD, SELL, SELL_SHORT, BUY_TO_COVER, or a reversal sequence; otherwise stop after row 14. NO_ACTION alone permits the next conditional row read.

## Execution Discipline

- One `RealCausalReplayHarness`, one D01 instance, one D04 instance, one controller, and one `SystemClock`.
- Data indices 0-7 establish legitimate warm-up state.
- Row 13 is read only after row 12 E5 returns NO_ACTION.
- Row 14 is read only after row 13 E5 returns NO_ACTION.
- Row 15 is never read.
- No reset, batching, async overlap, queue, sleep, broker input, Azure, synthetic market data, parameter change, threshold change, or profitability inspection.

## Source Verification

Authoritative source confirmed:

- row 10 volume 4288.0;
- row 11 volume 758.0;
- row 12 volume 1318.0.

Prompt discrepancy: row 12 contains OHLC `365.50 / 365.58 / 365.48 / 365.57`; no OHLC field equals 366.00. The row identity is unambiguous, so authoritative values are used and the discrepancy is preserved. No later row was pre-read.

## Frozen Preconditions

- Bound mathematical/temporal/semantic/Test 001 references: 67/67 PASS.
- Fifteen Test 002 and Test 002A evidence hashes recorded.
- D04 open threshold mechanically retained as 0.75.
- D01 and D04 stateful; D02 and D03 stateless; harness-maintained transition state labeled INTERNAL CONTROLLER STATE.

## Timing Boundary

For each cycle, direct start is immediately before `create_source_event`; direct stop is immediately after complete E5 `StageResult`/envelope return. Both use `time.perf_counter_ns()` through the same `SystemClock`. Stage sums and raw reconciliation deltas follow Test 002 definitions. Integer nanoseconds provide nanosecond resolution, not a nanosecond accuracy claim.

## Non-Drift Gate

Rows 10 and 11 must reproduce Test 002 D01 DMO/FMO, D02, D04, D03 POSITION, and Position Controller Decision before row 12 may be requested. Runtime timing and UUIDs need not match.

## Outcome Rule

Report `N_FIRST_SEMANTIC_DECISION` and `N_FIRST_EXECUTION_CHANGING_DECISION` only for this observed sequence and legitimate initial state. Do not generalize lifecycle depth or fit a filter/frequency-response model.

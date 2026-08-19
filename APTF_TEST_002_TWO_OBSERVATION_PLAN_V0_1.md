# APTF Test 002 Two-Observation Plan V0.1

Status: EXECUTED READ-ONLY TEST EVIDENCE
Date: 2026-08-18

## Scope

Process exactly physical CSV rows 10 and 11 as targets t1 and t2 in one synchronous local Python runtime. Consume data indices 0-7 only as causal warm-up. Do not read physical row 12, reset state between targets, insert a market-time delay, tune parameters, alter frozen files, use broker/Azure data, or interpret profitability.

## Preconditions

- Physical row 10 mechanically resolved to data index 8, source row 9, `2022-09-30T08:08:00Z`.
- Physical row 11 mechanically resolved to data index 9, source row 10, `2022-09-30T08:09:00Z`.
- Market interval: 60 seconds; source order: PASS.
- Protected inventory: 30/30 PASS.
- Combined temporal and semantic freeze references: 37/37 PASS.
- Temporal freeze SHA256: `4e23eae07adc848614f71842c97c49271a1d22db6624d3d85e427a92ff02296a`.
- Semantic freeze SHA256: `6d584c40ad83b9322e9ab3be7158de964bc967d6d90ff94e1b016c686d934489`.

## Execution

The isolated harness `diagnostics/aptf_test_002_two_observations.py` instantiated one unchanged `RealCausalReplayHarness`, established state with indices 0-7, then invoked real frozen E0-E5 for t1 and immediately real frozen E0-E5 for t2. One `SystemClock` supplied all direct and stage monotonic samples. No concurrency, queue, network, sleep, or second initialization occurred.

## Direct Timer Boundary

`END_TO_END_START`: `SystemClock.monotonic_ns()` immediately before `create_source_event` begins E0 for the target.

`END_TO_END_STOP`: the next outer `SystemClock.monotonic_ns()` immediately after the complete E5 `StageResult`, including its `PositionTransitionPlan` envelope, has returned to the caller.

The direct timer is independently sampled. It is not derived from UTC, market time, or summed stage durations.

## State Handling

After E5 returns, the harness applies its unchanged semantic advancement rule only when the plan is authorized. State capture/report generation occurs outside each target direct boundary. The exact after-t1 snapshots are compared with before-t2 snapshots. Internal replay/control initialization is classified as `TEST/REPLAY INITIAL CONTROL STATE`, not synthetic market data or broker state.

## Timing Language

Canonical durations are integer nanoseconds. Microseconds and milliseconds are exact unit conversions. Values have nanosecond resolution; no nanosecond accuracy claim is made. Outer diagnostic sampling adds small overhead and the results are not asserted to be zero-overhead production latency.

# APTF Test 007A Plan V0.1

## Mode and prohibitions

Test 007A is an evidence-driven, additive extraction of APTF Runtime Core V0.1. It introduces no trading mathematics, retuning, decision rule, P&L, execution price, quantity, capital, broker, reserve replay, or historical artifact rewrite.

## Ordered procedure

1. Audit Tests 001, 002, 003, 004, 004A, 005, 005R, 006, 006A, 006B, and 007, including corrective Tests 002A, 003A, and 004R.
2. Classify material behavior as CURRENT_VALIDATED, SUPERSEDED, FAILED_EXPERIMENT, DIAGNOSTIC_ONLY, or HISTORICAL_REFERENCE.
3. Capture pre-extraction hashes for Test 005R, 006A, 006B, 007, frozen Emitter, and frozen D04 evidence.
4. Create the evolution ledger, authority map, and DO_NOT_REINTRODUCE registry.
5. Extend the existing `aptf_runtime` package additively with observation validation, rolling context, explicit Emitter state, the frozen Adaptive Emitter, immutable emission, long-only Position State Operator, and a single-observation runtime coordinator.
6. Run production-library unit tests.
7. Replay only Test 006A development rows 115-1114 and compare 985 actionable outputs to frozen evidence. Processing timestamps and IDs derived from them are telemetry, not deterministic scientific values; all authorized scientific, decision, context, state, ordering, and feedback fields require exact equality.
8. Read, but do not regenerate, Test 006B/Test 007 evidence and compare the Position State Operator over all 101,206 actionable rows.
9. Replay the permitted development sequence twice from identical state and compare deterministic scientific/runtime outputs.
10. Recompute historical hashes. Freeze only after G001-G119 pass.

## Extraction hypothesis

The validated Emitter behavior is controlled by D01 `step`, D02 `build_return_shape`, frozen D04 `CapturabilityModelV0_2.evaluate`, the rolling-15 operators, and the frozen decision/feedback order in `experimental_adaptive_emitter/emitter.py`. Extracting those unchanged while making observation admission explicit will produce exact scientific and state equivalence on all 985 Test 006A actionable observations.

The validated long-only behavior is controlled only by Test 007 state-before plus immutable BUY/SELL/HOLD. A pure six-case operator will reproduce all 101,206 actionable Test 007 rows exactly.

## Stop conditions

Stop without freeze for any unexplained scientific, decision, ordering, recursive-state, feedback, context, or Position transition difference; any reserve Emitter invocation; any historical hash drift; or any required semantic change.

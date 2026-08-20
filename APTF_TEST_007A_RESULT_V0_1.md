# APTF Test 007A Validated Production Runtime Core Consolidation Result V0.1

Status: **PASS**  
Acceptance: **120/120 PASS**  
Runtime baseline: **APTF Runtime Core V0.1 FROZEN**

## Runtime core

- Location: `aptf_runtime/src/aptf_runtime`
- New production source modules: 6
- Frozen inventory: 22 source, test, authority, and evidence files
- Runtime tests: 21 passed, 0 failed
- Freeze manifest SHA-256: `ee93a9c92eb39d08e29772889a86d592b76399ea673a52e41c1e6a6c2d0e2379`
- Source commit at extraction: `853df4931bef682d69968e92e000c16b7399c18e`

## Validated pipeline

```text
Observation
    -> Validation
    -> Rolling 15-observation context + persistent Emitter state
    -> Adaptive Emitter
    -> Immutable Emission
    -> BUY / SELL / HOLD
    -> Position State Operator
    -> FLAT / LONG
    -> Execution Intent
    -> BUY / SELL / NONE
```

## Equivalence

Test 006A development oracle:

- Initialization: 15/15
- Actionable Emitter outputs: 985/985
- H, Q_G, Q_S, Q_R, C: 985/985 each at tolerance 0.0
- Position Decision, state evolution, context identity, ordering: 985/985 each
- Feedback semantics: 1,970/1,970
- Adaptation records: 3,602/3,602
- BUY/SELL/HOLD: 131/102/752

Execution-specific `perf_counter_ns` fields and the historical emission ID derived from them are classified as processing telemetry, not scientific differences. All deterministic scientific and provenance fingerprints match.

Test 007 Position oracle:

- Actionable transitions: 101,206/101,206
- State-after: 101,206/101,206
- Structural classification: 101,206/101,206
- Truth table: 6/6
- Opening BUY: 2,051
- Repeated BUY while LONG: 12,198
- Closing SELL: 2,051
- SELL while FLAT: 7,728
- HOLD while LONG: 39,787
- HOLD while FLAT: 37,391

Deterministic replay ran the 1,000-observation permitted development sequence twice. Scientific emissions, Position transitions, Execution Intents, final state, and context identity were identical.

## HOLD semantics

**HOLD IS STATE-RELATIVE.**

- LONG + HOLD -> LONG: maintain the existing Position State.
- FLAT + HOLD -> FLAT: remain out of the market.

Repeated BUY while LONG creates ExecutionIntent NONE. SELL while FLAT creates ExecutionIntent NONE and cannot create SHORT.

## Prohibited behavior

Runtime Core V0.1 contains no arbitrary D04 1.0 dimension, data_integrity score, executable G, absolute C>=0.75 Adaptive gate, FLAT/NO_ACTION Emitter decision, independent 15-row reset, future access, raw repeated broker BUY, SHORT production Position State, broker, execution price, share quantity, capital, or P&L.

The frozen Emitter's legacy internal-controller feedback value can be `SHORT`; it is quarantined inside EmitterState solely to reproduce Test 006A state/feedback evidence. It is not production PositionState and cannot produce ExecutionIntent without the long-only Position Operator.

## Historical immutability

- Test 005R: unchanged 16/16
- Test 006A: unchanged 21/21
- Test 006B: unchanged 20/20; reserve Emitter rerun: NO
- Test 007: unchanged 17/17
- Frozen Emitter and D04 manifests: unchanged
- Existing Temporal Event Envelope metadata touched during extraction was restored byte-for-byte before freeze.

An older temporal manifest already disagrees with the committed `single_observation_pipeline.py` identity even though Git reports no content diff in this worktree. Test 007A did not modify or repair that pre-existing discrepancy; it is recorded in the immutability artifact and does not affect the acceptance-critical Test 005R/006A/006B/007 or Emitter/D04 identities.

## Final questions

1. **What exact validated functions were extracted?** Strict `Observation.from_source_row`/`to_d01`; continuous `RollingContext`; frozen adaptive-property, decision, D01/D02/four-factor, feedback, and emission lifecycle in `AdaptiveEmitter.process`; immutable runtime models; six-case `apply_position_decision`; and single-observation `RuntimeCore.process`.
2. **Which tests authorize them?** Tests 001/002 authorize causal one-observation sequence and temporal identity; Test 004R/D04 freeze authorizes H/Q_G/Q_S/Q_R/C and upstream quality; Test 005R authorizes source-time gaps; Test 006A authorizes Emitter/context/state/adaptation/feedback; Test 006B validates frozen out-of-sample behavior; Test 007 authorizes Position semantics.
3. **Which historical behaviors were not migrated?** G/data_integrity D04 scoring, artificial dimensions, absolute 0.75 Emitter gating, historical D03 gate semantics, failed Test 005 spacing rule, failed Test 006 mocks, FLAT/NO_ACTION decisions, block resets, raw decisions as broker actions, and all execution/P&L behavior.
4. **Did extraction alter any Emitter mathematical result?** No; 985/985 exact for H/Q_G/Q_S/Q_R/C.
5. **Did extraction alter any BUY/SELL/HOLD decision?** No; 985/985 exact.
6. **Did extraction alter recursive-state behavior?** No; 985/985 state evolution exact.
7. **Did extraction alter feedback behavior?** No; 1,970/1,970 feedback semantics exact.
8. **Is the rolling 15-observation aperture continuous?** Yes, including no reset at observations 30 or 45.
9. **Is current excluded from its prior context?** Yes.
10. **Can one observation be processed without future knowledge?** Yes; `RuntimeCore.process(observation)` requires no dataset or future length.
11. **Is HOLD explicitly state-relative?** Yes.
12. **Can repeated BUY while LONG cause another BUY intent?** No.
13. **Can SELL while FLAT cause SELL intent?** No.
14. **Can SELL while FLAT create SHORT?** No.
15. **Are Decision, Position State, and Execution Intent distinct?** Yes, with separate enums and models.
16. **Does the Position Operator reproduce Test 007?** Yes, 101,206/101,206.
17. **Does the Emitter reproduce permitted Test 006A evidence?** Yes, 985/985 actionable plus 15/15 initialization.
18. **Was Test 006B reserve rerun?** No.
19. **Were historical acceptance authorities changed?** No.
20. **Is Runtime Core V0.1 a frozen importable baseline?** Yes. Future changes must use an additive version and regression evidence.

## Test 008 readiness

- Single-observation input: YES
- Persistent state explicit: YES
- Full future dataset required: NO
- Isolated runtime instances possible: YES
- Broker dependency: NO
- P&L code: NO
- Execution price: NOT SELECTED
- Capital: NOT INTRODUCED
- Share quantity: NOT INTRODUCED
- Structurally ready for separately authorized Test 008 simulation: YES

Next action: **STOP FOR HUMAN REVIEW. Do not begin Test 008.**
# APTF Runtime Authority Map V0.1

| Production behavior | Authority | Production module | Equivalence/test |
|---|---|---|---|
| Canonical observation and required source fields | Tests 001, 004R, 006A source records | `aptf_runtime.observation` | observation validation tests; 006A replay |
| Observation identity and provenance | Temporal Event Envelope V0.2; 006A observation IDs | `aptf_runtime.observation`, existing `identity` | provenance/immutability tests; 006A context IDs |
| Upstream data-quality stop | Test 004R and D04 freeze | `aptf_runtime.observation` | invalid observation tests |
| Source timestamp/delta | Tests 005R, 006A | `aptf_runtime.observation`, `emitter` | monotonic-time and replay tests |
| D01 recursive mathematics | Test 006A frozen implementation | frozen `d01.v02.model` called by `emitter` | 985-row H/Q/C/state equivalence |
| D02 ReturnShape/path direction | Test 006A decision authority | frozen `d02.v02.builder` called by `emitter` | 985-row direction/decision equivalence |
| H, Q_G, Q_S, Q_R, C | Test 004R four-factor freeze and 006A | frozen `CapturabilityModelV0_2` called by `emitter` | 985 exact-value comparisons |
| C not absolute 0.75 gate | 003A, 004A, 005R, 006A frozen rule | `emitter` | decision path and prohibited-code tests |
| Rolling 15 prior completed records | 006A context/first-emission audits | `aptf_runtime.context.RollingContext` | rollover tests at 16, 17, 30, 45; 006A IDs |
| Current observation exclusion | 006A causal cover | `context`, `emitter` commit order | first-actionable and no-future tests |
| Adaptive values, frozen rules | 006A adaptation and decision authority | `emitter` | 985 adaptive/decision comparisons |
| Recursive Emitter state | 002, 006A state evidence | `aptf_runtime.models.EmitterState` | state continuity and deterministic replay |
| n-to-n+1 feedback | 006A feedback audit | `emitter` | feedback-causality comparison |
| Immutable scientific emission | 006A emission hashes; temporal V0.2 | `aptf_runtime.models.ImmutableEmission` | frozen-value and provenance tests |
| Emitter BUY/SELL/HOLD | 006A decision authority | `EmitterDecision` | 985 decision comparisons |
| FLAT/LONG Position State | Test 007 state-machine authority | `aptf_runtime.position` | six-case truth table; 101,206-row oracle |
| State-relative HOLD | Test 007 hold decomposition | `position.apply_position_decision` | truth table and full sequence |
| Repeated BUY/unmatched SELL | Test 007 structural exceptions | `position.apply_position_decision` | exact Test 007 counts |
| BUY/SELL/NONE Execution Intent | Mechanically derived from Test 007 state changes | `ExecutionIntent`, `PositionTransition` | truth table and full sequence |
| Single-observation coordinator | 006A causal cover and lifecycle cardinality | `aptf_runtime.runtime.RuntimeCore` | initialization, isolated-instance, replay tests |
| Source time vs processing time | Temporal V0.2 and 006A architecture | existing `clock`; `emitter` | timing-field separation tests |
| Persistent-state boundary | 002, 006A, 007 | `RuntimeState` plus D01/context/emitter/position instances | continuity and isolated-instance tests |
| Future execution adapter boundary | Test 007/007A separation | `ExecutionIntent` output only | absence scan for broker/P&L code |

## Historical code boundary

`experimental_adaptive_emitter/emitter.py` remains frozen scientific evidence. Test 007A extracts its validated mechanism additively; it does not rewrite the historical implementation or migrate the failed Test 006 harness. Test 006B is never used as an Emitter replay input.

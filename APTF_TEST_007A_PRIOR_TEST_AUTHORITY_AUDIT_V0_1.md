# APTF Test 007A Prior Test Authority Audit V0.1

## Classification vocabulary

- CURRENT_VALIDATED: may govern Runtime Core V0.1.
- SUPERSEDED: later evidence replaces the positive behavior; retained as a negative regression constraint.
- FAILED_EXPERIMENT: invalid result or unauthorized mechanism; never production authority.
- DIAGNOSTIC_ONLY: useful evidence or telemetry, not runtime semantics.
- HISTORICAL_REFERENCE: valid in its original bounded question but not current production authority.

## Test 001

- Attempt: one real CSV observation through the real causal path with prior-only warm-up.
- Result: PASS 26/26.
- Established: deterministic single-observation traversal, immutable temporal identity, no future read, and separation of source time from processing time.
- Correction: Position Controller wording was corrected from apparent actual position to D03 POSITION, POSITION CONTROLLER DECISION, and INTERNAL CONTROLLER STATE.
- Production: temporal/provenance and causal single-observation principles.
- Historical only: row-10 outcome and old D04 provenance.
- Authority: `APTF_TEST_001_ROW_10_RESULT_V0_1.md`, `APTF_TEST_001_ROW_10_TEMPORAL_TRACE_V0_1.md`, `APTF_TEST_001_POSITION_CONTROLLER_SEMANTIC_ADDENDUM_V0_1.md`.
- Status: CURRENT_VALIDATED for causality/identity; HISTORICAL_REFERENCE for bounded values.

## Test 002 and Test 002A

- Attempt: two sequential observations, then differential volume-response audit.
- Result: PASS 28/28; Test 002A passed its differential audit.
- Established: one continuing runtime, no reset, D01 and D04 statefulness, D02/D03 stateless transformation semantics, and continuous internal response despite unchanged terminal output.
- Production: sequential state continuity and one-observation advancement.
- Historical only: G-era D04 provenance and bounded row values.
- Authority: `APTF_TEST_002_RESULT_V0_1.md`, `APTF_TEST_002A_RESULT_V0_1.md`, `APTF_TEST_002A_CAUSAL_MAP_V0_1.md`.
- Status: CURRENT_VALIDATED for continuity; HISTORICAL_REFERENCE for values.

## Test 003 and Test 003A

- Attempt: five-cycle lifecycle response and threshold reachability analysis.
- Result: PASS 45/45; Test 003A found algebraic reachability but did not prove end-to-end practical reachability.
- Established: rows 10-14 bounded anchors and the distinction between algebraic and empirical reachability.
- Production: no threshold retuning follows from a small bounded sequence.
- Historical only: old D04 provenance and five-row terminal results.
- Authority: `APTF_TEST_003_RESULT_V0_1.md`, `APTF_TEST_003A_RESULT_V0_1.md`.
- Status: HISTORICAL_REFERENCE.

## Test 004

- Attempt: correct known-input D04 provenance and regress the five-cycle result.
- Result: PASS 60/60 with zero numeric delta.
- Established: provenance correctness is independent of coincident numeric equality; unavailable context is not a fabricated neutral.
- Later correction: Test 004 still retained data_integrity in G and was superseded by Test 004R.
- Production: provenance/null applicability principle only.
- Historical only: executable G and data_integrity scoring.
- Authority: `APTF_TEST_004_RESULT_V0_1.md`, `APTF_TEST_004_D04_PROVENANCE_TRACE_V0_1.json`.
- Status: SUPERSEDED for D04 equation; CURRENT_VALIDATED for provenance discipline.

## Test 004A

- Attempt: backward boundary proof from stored Test 004 evidence, with no pipeline run.
- Result: PASS, Result B, 60/60.
- Established: the evidence did not prove C=0.75 mathematically impossible and did not authorize a replacement threshold.
- Later correction: its quantitative values use the superseded G-era equation.
- Production: negative governance constraint only.
- Authority: `APTF_TEST_004A_RESULT_V0_1.md`, `APTF_TEST_004A_REACHABILITY_ANALYSIS_V0_1.md`.
- Status: HISTORICAL_REFERENCE.

## Test 004R and D04 freeze

- Attempt: remove data_integrity and empty G from executable D04 and regress known outputs.
- Result: PASS; four-factor D04 frozen.
- Established equation: `C = H * Q_G * Q_S * Q_R`.
- Production: `H`, `Q_G`, `Q_S`, `Q_R`, and `C` exactly as implemented by frozen `CapturabilityModelV0_2`; data quality remains upstream.
- Authority: `APTF_TEST_004R_RESULT_V0_1.md`, `APTF_D04_FOUR_FACTOR_FREEZE_MANIFEST_V0_1.json`, `d04_trading_envelope/src/aptf_d04/envelope/capturability_model.py`.
- Status: CURRENT_VALIDATED.

## Test 005

- Attempt: first 100-row frozen D04 empirical study.
- Result: INVALID Result E; 72/115 gates. The complete trace was not serialized and uniform 60-second spacing was incorrectly required.
- Established: incomplete evidence cannot support empirical claims; source gaps are evidence rather than automatic invalidity.
- Production: no executable behavior.
- Authority: `APTF_TEST_005_FROZEN_RESULT_V0_2.md`, `APTF_TEST_005_FROZEN_100_CYCLE_TRACE_V0_2.json`.
- Status: FAILED_EXPERIMENT and SUPERSEDED.

## Test 005R

- Attempt: corrected literal-row 100-observation study under frozen four-factor D04.
- Result: PASS, Result C, 120/120.
- Established: 100 literal rows, strict timestamp order with gaps preserved, exact C reconstruction, and empirical C range 0.02642361014377076 to 0.5577135990257739. C>=0.75 occurred zero times but impossibility and retuning were not established.
- Production: source-time gap handling and frozen four-factor empirical baseline.
- Historical only: D03 FLAT/controller NO_ACTION sequence results.
- Authority: `APTF_TEST_005R_RESULT_V0_3.md`, `APTF_TEST_005R_SOURCE_TIME_ANALYSIS_V0_3.json`.
- Status: CURRENT_VALIDATED.

## Test 006

- Attempt: causal pipeline action test using the original replay/controller route.
- Result: failed/invalid architecture. It used mock heuristics, blank decisions, independent assumptions, and crossed the later sealed reserve boundary.
- Established negatively: mock D03 hashes, close/volume heuristics, and sparse blank output are not the validated Emitter.
- Production: nothing positive.
- Authority: `APTF_CAUSAL_PIPELINE_ACTION_SPARSITY_AUDIT_V0_1.md`, `APTF_CAUSAL_PIPELINE_INTEGRATION_PATH_AUDIT_V0_1.md`, `position_transition_controller/causal_replay_harness.py`.
- Status: FAILED_EXPERIMENT.

## Test 006A

- Attempt: develop, validate, and pre-reserve freeze a causal Adaptive Emitter on physical rows 115-1114.
- Result: PASS 110/110; 1,000 observations, 15 initialization, 985 actionable, BUY 131, SELL 102, HOLD 752, reserve access zero.
- Established: exact rolling 15 prior completed observations; current observation excluded; one-row aperture advancement; continuous recursive D01/Emitter state; adaptive values with frozen rules; n-to-n+1 feedback; causal cover; one lifecycle per observation; immutable emissions; BUY/SELL/HOLD vocabulary; exact H/Q_G/Q_S/Q_R/C dependencies.
- Production: primary Emitter authority and permitted equivalence oracle.
- Diagnostic only: `perf_counter_ns` values and IDs that include those execution timings.
- Authority: `experimental_adaptive_emitter/emitter.py` at SHA-256 `e8b736dfba03b454633831585222d5270c18b7f8eae510b34ee19dc1f5c58410`, `APTF_ADAPTIVE_EMITTER_PRE_RESERVE_FREEZE_MANIFEST_V0_1.json`, `APTF_TEST_006A_WALK_FORWARD_EMISSIONS_V0_1.json`.
- Status: CURRENT_VALIDATED.

## Test 006B

- Attempt: one authorized frozen Emitter pass over sealed reserve.
- Result: PASS 120/120; 101,221 observations, 15 initialization, 101,206 actionable, BUY 14,249, SELL 9,779, HOLD 77,178.
- Established: out-of-sample non-degeneracy, state continuity, causal context, feedback, no retuning, frozen identity, immutable source/decision output.
- Production: validates the frozen Emitter identity and real-time sequential architecture.
- Prohibition: reserve Emitter execution cannot be repeated in Test 007A.
- Authority: `APTF_TEST_006B_RESULT_V0_1.md`, `APTF_TEST_006B_POSTEXECUTION_INTEGRITY_V0_1.json`, immutable Test 006B CSV.
- Status: CURRENT_VALIDATED evidence; read-only oracle metadata.

## Test 007

- Attempt: reconstruct deterministic long-only Position episodes from immutable Test 006B decisions without Emitter execution or P&L.
- Result: PASS 120/120; 101,206 actionable transitions.
- Established: FLAT/LONG Position State; HOLD is state-relative; raw decisions are not broker actions; repeated BUY while LONG and SELL while FLAT produce no state change; 2,051 opens and closes; no SHORT.
- Production: primary Position State Operator and Execution Intent authority.
- Authority: `APTF_TEST_007_STATE_MACHINE_AUTHORITY_V0_1.md`, `APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv`, `APTF_TEST_007_RESULT_V0_1.md`.
- Status: CURRENT_VALIDATED.

## Audit conclusion

Production authority is cumulative, not Test-007-only. Test 006A controls Emitter science and recursive behavior; Test 006B validates its frozen out-of-sample identity without becoming a replay source; Test 007 controls long-only Position transitions; Test 004R/D04 freeze controls C construction; temporal Tests 001-002 control identity, causal sequence, and source/processing-time separation. No required semantic change was identified.

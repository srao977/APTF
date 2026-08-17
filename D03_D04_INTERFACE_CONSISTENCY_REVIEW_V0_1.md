# D03 / D04 Interface Consistency Review v0.1

## Status

**REVIEW RESULT: CONSISTENT AND DESIGN FREEZE-READY FOR HUMAN REVIEW.** D03 is not implemented or frozen.

## A. Actual frozen D04 output consumed

PASS. The design references the live 23-field D04Evaluation and amended six-field CandidateEnvelope exactly. No prose-only surrogate model is introduced.

Current D04 executable/interface authority is v0.2.1 freeze SHA256 `F72A86B3085BD11D8626F06F1FE3FAEDDE60570365488176011239382A46F1AF`.

## B. No D01 bypass

PASS. Direct D01 inputs: zero. D03 neither reads Q_t nor creates alternate market features under this proposed contract.

## C. No D02 bypass

PASS. Direct D02 inputs: zero. Direction arrives only as D04 candidate provenance copied verbatim from source ReturnShape.

## D. Candidate ownership preserved

PASS. D04 creates and invalidates candidates. D03 preserves candidate and source-shape identities and never mints a competing candidate.

## E. D04 lifecycle ownership preserved

PASS. D03 consumes current envelope, safety, stale, candidate, and factual event states. It does not change D04 thresholds, hysteresis, aperture, supersession, staleness, or qualification.

## F. D03 decision ownership explicit

PASS. D03 alone owns desired position state, transition intent, action authorization, rule identity, and committed decision record. Actual/pending execution state is supplied by its authoritative ledger/controller.

## G. No factual state reinterpreted as outcome

PASS. D04 OPEN means current qualified capturability, not profitable trade; CLOSED/stale means no current capture authorization, not a realized loss. Scores are not reweighted or treated as expected return.

## H. No D03 feedback upstream

PASS. D03 decisions, positions, pending targets, outcomes, and P&L never feed D01, D02, D04, ReturnShape geometry, or D04Context.

## I. Replay/live equivalence

PASS by design. Identical ordered D04Evaluation/DecisionContext pairs, canonicalization, and versions yield identical decisions. No replay/live branch, scheduler, random input, or wall-clock identity exists.

## J. Zero future leakage

PASS. Future observations, outcome columns, benchmark decisions, P&L, reserve values, future fills, and evaluator feedback are prohibited before commitment.

## Directional consistency finding

PASS. D04 v0.2.1 CandidateEnvelope carries immutable `path_direction` with exact D02 domain `UPWARD|DOWNWARD|FLAT`. D03 maps those to LONG, SHORT, and FLAT without recomputation or reinterpretation.

## DecisionContext duplication review

The 12 proposed context fields do not duplicate D04 feasibility. Execution availability is a present action authorization, distinct from D04's capturability input. Position/pending state and operator controls are D03/control facts. Raw D04Context values, market features, sizing, costs, and portfolio allocation are excluded.

## Final assessment

A-J boundary invariants are satisfied. Disabled control preserves actual state and accumulates no deferred target; emergency flatten is the explicit higher-priority FLAT override. No open architectural ambiguity remains. Result: D03 design is freeze-ready for human review, but this task does not freeze or implement it.

## Committed-output reconciliation

Machine rule-table authority now defines precommit invalid-input rejection, target-primary reason precedence, canonical supporting reason order, exact decision-rule ID composition, formal pending-target RETARGET semantics, execution-unavailable BLOCKED overlay, and target-causal candidate lineage. These additions do not alter D03/D04 ownership or directional policy.

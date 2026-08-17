# D03 Decision and Control Architecture Trace v0.1

## 1. Status

**DESIGN FREEZE-READY FOR HUMAN REVIEW; NOT FROZEN; NO IMPLEMENTATION AUTHORIZED.**

## 2. System position and authority chain

```text
causal observations -> frozen D01 -> frozen D02 ReturnShape
                    -> frozen D04 D04Evaluation
                    -> D03 Decision and Control
                    -> future replay evaluator or execution adapter
```

Verified authorities:

- system authority SHA256 `30C1DEF02735B477954F0E67192477C23DD59452E77020FDA8CE113D612CFA82`;
- D01 architecture freeze `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235`;
- D02 design freeze `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`;
- D02 implementation freeze `C8029C4B9608547BBF7960F05E4F8613480C4FB2BF8594D94482516B954F7E72`;
- D04 design freeze `B5C489D060629A91DDED5B2C6EAA4076F6273AF05AED3480659CE649A1050E51`;
- D04 v0.2 historical implementation freeze `7BBA0E80723EBA002EC14FABEE8D7D3B2952DF6E8730528E8D6CC9649E8A3ABC`;
- current D04 executable authority: `D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json`, SHA256 `F72A86B3085BD11D8626F06F1FE3FAEDDE60570365488176011239382A46F1AF`.

## 3. D03 role

D03 converts current factual D04 state plus explicit causal control context into a committed desired control state. It owns decision intent and candidate disposition relative to an externally reported position/control state. It does not predict markets, construct ReturnShape, calculate capturability, create D04 candidates, submit orders, size positions, or evaluate outcomes.

## 4. Exact D04 input consumed

D03 consumes one complete frozen 23-field `D04Evaluation`, including its nullable six-field `CandidateEnvelope`. Decision-active subsets are defined in `D03_D04_INPUT_INVENTORY_V0_1.md`; the full object is retained for deterministic input fingerprinting and audit.

Direct D01 inputs: zero. Direct D02 inputs: zero under this design. A direct bypass is not silently introduced.

## 5. DecisionContext

The proposed context has 12 required causal fields: `context_time`, `entity_id`, `actual_position_state`, `position_candidate_id`, `position_source_return_shape_model_time`, `pending_target_state`, `pending_decision_id`, `execution_available`, `system_enabled`, `trading_enabled`, `emergency_flatten`, and `control_state_valid`.

It is a snapshot supplied by an authoritative position/execution/control ledger. It contains no price, market inference, D04 feasibility duplicate, quantity, P&L, outcome, benchmark, or future value.

## 6. Primary control paradigm

D03 is **desired-state centric with a derived transition intent**:

- desired position: `FLAT|LONG|SHORT`;
- transition intent: `NO_CHANGE|OPEN|CLOSE|REVERSE|RETARGET|BLOCKED`.

The desired state is authoritative. Transition intent explains the required control transition but is not a broker command. `MAINTAIN` is not a separate action: continuation is explicit as an unchanged desired state plus `NO_CHANGE` and `POSITION_ALREADY_ALIGNED`.

## 7. Hierarchical decision structure

1. Validate schema, entity, time, control snapshot, D04 invariants, and `control_state_valid=true`. Failure rejects input before policy evaluation and commits no D03Decision.
2. Apply `emergency_flatten` as the highest policy target.
3. If system or trading control is disabled, preserve the actual position/control state, emit NO_CHANGE, and create no deferred target.
4. Derive the unconstrained target from D04: only `OPEN` plus a current `QUALIFIED` directional candidate may target `LONG` or `SHORT`; every other factual D04 state targets `FLAT`.
5. If a pending transition exists, emit RETARGET only when desired differs from its pending target; otherwise derive transition from the 3x3 actual-to-desired matrix.
6. If execution is unavailable for OPEN/CLOSE/REVERSE/RETARGET, retain the known desired target but emit committed BLOCKED with no authorization or queue.
7. Commit an immutable decision record even for `NO_CHANGE` or `BLOCKED`; blocked records are audit facts and must never be queued blindly.

The resolved target rule supplies `primary_reason_code`. The transition reason and then authorization-overlay reasons become ordered supporting reasons. `decision_rule_id` is always `TARGET:<id>|TRANSITION:<id-or-NONE>|OVERLAYS:<ordered-ids-or-NONE>`. Candidate lineage follows only the target-causing authority: current D04 candidate for ordinary QUALIFIED UPWARD/DOWNWARD/FLAT; null for emergency flatten, disabled preservation, safety/non-OPEN, absent, or invalidated candidate targets.

## 8. Position/control representation

D03 is stateless over explicit context. The external ledger is authoritative for actual position and pending target. D03 owns no hidden position memory. Initialization requires `actual_position_state=FLAT`, null position lineage, `pending_target_state=NONE`, and null pending decision identity unless an existing externally reconciled state is supplied.

## 9. Candidate relationship

D04 exclusively creates and invalidates candidates. D03 preserves the current D04 candidate identity for open/reverse targets and the originating position candidate identity for close decisions when no current candidate remains. D03 never mints, mutates, or resurrects a candidate.

## 10. Lifecycle relationship

- `CLOSED`, `OPENING`, or `CLOSING`: unconstrained target `FLAT`.
- `OPEN`: `UPWARD` qualified candidate targets LONG, `DOWNWARD` targets SHORT, and `FLAT` targets FLAT.
- stale or safety-closed: target `FLAT`; an existing position yields close intent when authorized.
- supersession: evaluate only the candidate in the current D04 evaluation. Same orientation preserves target; opposite orientation implies desired opposite state; absent/invalid candidate implies `FLAT`.
- disabled control: preserve actual state even if D04 closes, stales, invalidates, or changes direction; re-enable evaluates only current D04 facts.

## 11. Commitment boundary

A decision is committed when the immutable D03 record and deterministic identity are durably appended before any future outcome is revealed. Decision time is causal `DecisionContext.context_time`, which must be greater than or equal to D04 `evaluation_time`. Candidate and source-shape lineage, desired state, transition intent, authorization, rule/version identifiers, and input fingerprints are fixed at commitment.

## 12. Replay/live equivalence and event operation

D03 is called on every new D04 evaluation or material DecisionContext change. Identical ordered input pairs and versions produce identical records. There is no scheduler, replay branch, stochastic branch, adaptive state, outcome feedback, or second hysteresis layer.

## 13. Future adapter boundary

An output adapter may translate an authorized target/intent into broker-specific sequencing, order type, venue, price, and quantity under separately frozen execution/risk policy. D03 specifies none of those. A replay evaluator associates later outcomes only after commitment.

## 14. Prohibited information

Future prices/observations, observer columns, outcome or benchmark labels, realized/expected P&L, reserve values, transaction-cost outcomes, broker results not yet causally known, alternate predictors, raw D01/D02 fields, and historical decision performance are prohibited.

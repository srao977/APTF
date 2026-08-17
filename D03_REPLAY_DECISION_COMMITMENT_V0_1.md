# D03 Replay Decision Commitment Contract v0.1

## Status

**PROPOSED DESIGN; NOT FROZEN; REPLAY NOT AUTHORIZED BY THIS DOCUMENT.**

## Commitment point

A D03 decision becomes committed only when the complete 21-field `D03Decision` record has passed schema/invariant validation and is durably appended to the causal decision ledger. This append must complete before the replay source/evaluator reveals any observation or outcome with event time later than `decision_time` for evaluation of that decision.

Schema or semantic boundary failure, including `control_state_valid=false`, produces no D03Decision and therefore no commitment. Invalid input is never represented by BLOCKED.

Computing an in-memory object, logging a partial line, or sending an unacknowledged adapter request is not commitment.

## Fixed fields

At commitment, all D03 output fields are immutable, including:

- decision and version identities;
- decision time and entity;
- D04 and full-input fingerprints;
- D04 evaluation/model-time/state references;
- candidate and source ReturnShape lineage;
- prior and desired position state;
- transition intent and authorization;
- exact rule and reason codes.

Later execution, position, outcome, benchmark, or P&L records never mutate the decision.

## Canonical input identity

Use RFC 8785 JSON Canonicalization Scheme for the complete validated D04Evaluation and DecisionContext, with enum values serialized as strings and nonfinite values rejected.

```text
source_d04_fingerprint = lowercase_hex(SHA256(JCS(D04Evaluation)))
input_fingerprint      = lowercase_hex(SHA256(JCS(D03Input)))
```

Decision time equals causal `DecisionContext.context_time`; input validation requires it to be at least D04 evaluation time.

## Deterministic decision identity

```text
decision_id =
  D03D|
  percent_encode_utf8(entity_id)|
  format17g(decision_time)|
  decision_rule_version|
  input_fingerprint
```

Percent encoding follows RFC 3986 unreserved characters with uppercase percent hex. `format17g` is locale-independent binary64 formatting. There is no UUID, random value, process clock, database sequence, outcome, or P&L component.

## Idempotency

The ledger enforces uniqueness of `decision_id`. Redelivery of identical canonical input under the same rule version returns the existing committed record and does not append a duplicate. A changed DecisionContext or D04Evaluation changes the input fingerprint and creates a new causal decision record even when desired state is unchanged.

## NO_CHANGE and BLOCKED

NO_CHANGE and BLOCKED are committed decisions because they establish what D03 knew and intended at that event. `action_authorized=false` prevents an adapter from treating them as executable requests. BLOCKED targets are not queued; a later context change causes a fresh decision against current D04 facts.

Directional commitments use only the current D04 candidate's committed `path_direction`. Disabled-control commitments fix desired state to the current actual position, use NO_CHANGE, and contain no D04-observed future target for later execution. Emergency flatten commits desired FLAT explicitly. Re-enable is a new input/decision using current D04 facts.

Candidate lineage is null for emergency flatten and disabled preservation. It preserves current D04 candidate ID/source lineage for ordinary QUALIFIED UPWARD, DOWNWARD, or FLAT target rules, and is null when no active candidate caused the target.

The target rule reason is primary. Canonically ordered supporting reasons and the exact target/transition/overlay rule composition are committed fields and therefore included in the deterministic input-to-output proof.

## Outcome association

A future evaluator associates realized outcomes through `decision_id`, entity, and decision time in a separate append-only evaluation record. Candidate identity and D04/input fingerprints permit lineage verification. Multiple decisions may exist within one upstream projection horizon and are evaluated according to a separately frozen backtest contract.

## Pre-commitment prohibitions

Before commitment, D03 and its caller may not expose or consume:

- observations with event time after decision time;
- future prices or realized returns;
- outcome/target/benchmark decision columns;
- realized or expected P&L;
- future fills, rejections, costs, or slippage;
- reserve rows or reserve-derived statistics;
- evaluator scores or prior performance-selected rules.

## Failure behavior

If input, canonicalization, schema, or durable append fails, no decision is committed and no future outcome may be associated with an uncommitted result. Retry may only use the identical still-causal input and must produce the same decision ID; otherwise a new current input event is required. Adapter execution is forbidden until commitment succeeds and `action_authorized=true`.

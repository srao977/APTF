# APTF Single-Input Causal Identity Audit V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Identity chain

| Identity | Created at | Preserved through | Replaced/dropped | Parent relationship | Original source recoverable? |
|---|---|---|---|---|---|
| source `source_row_number="17"` | normalized CSV source | source row only | dropped by mapper | none | YES at source only |
| `sequence_id=16` | source mapper | D01 input / last observation | not emitted in DMO/FMO | local row-order derivation | PARTIAL |
| D01 `trace_id="SPY:17"` | D01 after state sequence increment | DMO and internal TraceRecord | dropped by D02 output | no explicit source ID parent | PARTIAL |
| D01 `state_hash` | D01 state output | DMO | dropped by D02 output | hash excludes event time/source row identity | NO exact source recovery |
| D02 identity `(SPY,1664525760.0)` | ReturnShape contract | D04 via entity/model time | represented as D04 source time, not parent ID | derived entity + event/model time | PARTIAL |
| D04 evaluation ID | none | N/A | N/A | D03 later hashes whole evaluation | PARTIAL through generated fingerprint |
| D04 `candidate_id` | candidate qualification | candidate and D03 lineage when target-causing | target has no candidate | encodes entity/source model time/qualified time | N/A for target; partial generally |
| D03 `source_d04_fingerprint` | D03 | DecisionRecord | indirectly inside controller parent hash/ID | SHA256 of D04 evaluation | commits D04 payload, not source row |
| D03 `input_fingerprint` | D03 | DecisionRecord and decision ID | supplied to controller as hash in current harness | SHA256 of D04 evaluation + context | commits immediate inputs only |
| D03 `decision_id` | D03 | controller plan parent | preserved | entity + context time + rule version + input fingerprint | original $t$ recoverable; exact source row not proven |
| controller `transition_id` | controller | terminal plan | terminal detached verb drops it | binds D03 ID/hash, position authority, states, verbs/status | partial upstream proof |

## Finding

FULL IMMUTABLE END-TO-END CAUSAL ID EXISTS: **NO**.

First identity discontinuity: **D01 -> D02 output**. D02 consumes DMO/FMO but emits no D01 `trace_id`, `state_hash`, source sequence, or source row identity. It creates/uses `(entity_id, model_time)` as its own identity.

Later hashes create strong lineage from D04 payload to D03 and from D03 to the controller plan, but they cannot retroactively bind the original source object omitted upstream.

Event-time lineage and immutable identity lineage are therefore different results: $t$ survives; one parent ID does not.

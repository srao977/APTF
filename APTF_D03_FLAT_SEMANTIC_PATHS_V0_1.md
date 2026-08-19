# APTF D03 FLAT Semantic Paths V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Summary

The single value FLAT represents multiple non-equivalent causes. D03 preserves their distinction in `primary_reason_code`, supporting reasons, rule ID, D04 source facts, and fingerprints.

| FLAT source | Component | Condition | Analytical FLAT | Suppressed direction | Control FLAT | Execution-state FLAT |
|---|---|---|---|---|---|---|
| Candidate non-directional | D02/D04/D03 | OPEN + QUALIFIED + path FLAT | YES | NO | NO | NO |
| No candidate | D04/D03 | OPEN + null candidate | NO | YES/unknown | NO | NO |
| Invalidated candidate | D04/D03 | OPEN + non-QUALIFIED candidate | NO | YES | NO | NO |
| Envelope CLOSED | D04/D03 | state CLOSED | NO | YES | NO | NO |
| Envelope OPENING | D04/D03 | state OPENING | NO | YES/delayed | NO | NO |
| Envelope CLOSING | D04/D03 | state CLOSING | NO | YES/withdrawn | NO | NO |
| Safety/invalid/stale | D04/D03 | safety closed, stale, or projection invalid | NO | YES | safety control | NO |
| Emergency flatten | D03 | emergency flag | NO | overrides | YES | NO; desired control target |
| System disabled while actual FLAT | D03/actual ledger | disabled preservation | NO | D04 ignored | YES | YES, preserves reported actual |
| Trading disabled while actual FLAT | D03/actual ledger | disabled preservation | NO | D04 ignored | YES | YES, preserves reported actual |
| Defensive no-valid-candidate fallback | D03 | unmatched valid factual case | NO | potentially | fallback | NO |

## Absent categories

- Candidate status `EXPIRED`: not in the frozen candidate domain. Projection staleness is top-level D04 safety.
- Pending state causing FLAT: absent; pending does not alter desired.
- Execution unavailable causing FLAT: absent; it blocks transition after desired is resolved.
- Initialization default to FLAT: absent in D03 policy. Actual FLAT must be explicitly supplied; D03 fields have no neutral target default.
- Invalid input fallback to FLAT: absent; invalid input is rejected.

## Threshold chain

For an enabled directional D02 shape with $C<0.75$ from CLOSED:

```text
D02 UPWARD/DOWNWARD
  -> D04 CLOSED (not open-qualifying)
  -> no candidate
  -> D03 sees CLOSED, not raw direction
  -> R31 desired FLAT / ENVELOPE_CLOSED
```

Thus `C<0.75` does not itself semantically declare analytical FLAT. It prevents qualification; D03 subsequently selects FLAT from the resolved envelope fact.

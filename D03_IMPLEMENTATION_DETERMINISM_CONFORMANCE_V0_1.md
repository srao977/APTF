# D03 Implementation Determinism Conformance v0.1

## Independent authority

Expected records came from the frozen `design_validation/validate_d03_design_v01.py` oracle and frozen machine-readable rule/schema artifacts. The executable D03 under test was called separately.

## Exact results

| Measure | Result |
|---|---:|
| Frozen valid policy classes expected | 7,680 |
| Valid policy classes executed | 7,680 |
| Valid policy classes matched | 7,680 |
| Mismatched classes | 0 |
| Complete output fields per class | 21 |
| Field comparisons | 161,280 |
| Field-level mismatches | 0 |
| Exceptions | 0 |
| Frozen invalid classes expected | 11 |
| Invalid classes tested | 11 |
| Invalid classes rejected | 11 |
| Invalid classes committed | 0 |
| Nondeterministic same-process repeats | 0 |
| Fresh-process digest mismatches | 0 |
| Primary reason mismatches | 0 |
| Supporting reason mismatches | 0 |
| Decision rule ID mismatches | 0 |
| Candidate lineage mismatches | 0 |
| Decision identity mismatches | 0 |
| T00 mismatches | 0 |

The full 7,680-class output digest was identical in fresh Python processes with `PYTHONHASHSEED=1` and `PYTHONHASHSEED=777`.

## Verdict

PASS

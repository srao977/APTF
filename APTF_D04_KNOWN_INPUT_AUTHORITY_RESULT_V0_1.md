# APTF D04 Known-Input Authority Resolution Result V0.1

Status: PASS
Date: 2026-08-18

## Resolution

Twelve arbitrary values were confirmed and removed: eleven context placeholders plus one proof-only integrity-threshold override. Production D04 now receives only derived evaluation time and data integrity as active context. Future market, execution, account, portfolio, risk, and broker fields are null/UNAVAILABLE and non-participating until authoritative producers exist.

## Invariants

- Every active numeric D04 runtime input has OBSERVED, DERIVED, STATE, or MATHEMATICAL_CONSTANT provenance.
- Unavailable is neither 0 nor 1 and cannot carry a numeric value.
- Production cannot use TEST_FIXTURE provenance.
- G is the minimum of active known configured dimensions; current real path uses data_integrity.
- Empty active G raises; required data_integrity proves current nonempty operation.
- H omits unavailable market eligibility; known false remains ineligible.
- Arbitrary fixed-neutral injection count in real-market builders: 0.

## Before/After

| Property family | Before | After | Effect |
|---|---|---|---|
| market eligibility | literal true | null/UNAVAILABLE | no fake H pass |
| clock quality | literal 1.0 | null/UNAVAILABLE | diagnostic absence explicit |
| nine future G dimensions | literal 1.0 | null/UNAVAILABLE | excluded until real producers |
| data integrity | derived 1.0/0.5 | unchanged derived | current active G and H input |
| integrity threshold | proof override 0.0 | config 0.2 | authoritative safety restored |

## Formula Authority

| Factor | Known inputs only? | Placeholder? | Active? |
|---|---|---|---|
| H | YES | NO | YES |
| Q_G | YES | NO | YES |
| Q_S | YES | NO | YES |
| Q_R | YES | NO | YES |
| G_active | YES | NO | YES |
| C | YES | NO | YES |

Q_G/Q_S/Q_R/B remain byte-semantically unchanged. C changes only by explicit H/G applicability for absent context.

## Future Context

Defined concepts are preserved. Activation requires an authoritative producer contract, a non-null bounded value, and recognized production provenance. No broker/account/portfolio/execution architecture is invented here.

## Validation

- Dedicated provenance tests: 7/7 PASS.
- Complete D04 suite: 86/86 PASS.
- D02: 26/26 PASS.
- D03: 40/40 PASS.
- Controller unit: 6/6 PASS (six pre-existing return-value warnings).
- Temporal non-market contract: 7/7 PASS.
- Real-builder fixed-neutral scan: 0.
- Old protected inventory: 27/30 unchanged, three exact authorized deltas, zero unexpected.
- Historical Test 001-003A evidence: 41/41 byte-identical.

## Historical Interpretation

Test 003A's statement that D04 arithmetic is internally consistent remains valid. Its prior G/H provenance was placeholder-affected. Since corrected active G/H still equal 1 for those stored valid rows, arithmetic and Finding E do not numerically change. Future reachability work must use corrected active evidence.

## Acceptance

G01-G40: **40/40 PASS**.

No market row was read or processed. No threshold tuning, capturability calibration, broker/Azure work, or profitability analysis occurred.

Old D04, real-integration, and Temporal Runtime freeze manifests were not modified. Their old bindings to the authorized changed files are historical; V0.2.2 supersedes only D04 context-authority construction/applicability and does not claim a new full-system freeze.

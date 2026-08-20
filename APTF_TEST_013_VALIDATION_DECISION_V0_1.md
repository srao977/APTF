# Test 013 Validation Decision V0.1

Decision: **VALIDATION_BLOCKED**.

The chronological tail 101099-101220 has zero overlap with Test012 candidate-selection projections, but it does not provide the causal cover required by the frozen Test013 contract. Of 122 tail rows, 83 are eligible exactly-one-minute intrasection origins. Causal window cover is W15=26, W30=11, and W60=0. Therefore the W15/W30/W60 sensitivity intersection is empty.

The 11 W30-capable rows occur on one local trading date. They cannot support the predeclared Q99/Q99.9, severe-tail, cross-session, or development-drift validation. Scoring that slice or dropping W60 after cover inspection would manufacture validation.

No Test013 projection, scorecard, error quantile, perturbation, coefficient, or drift result is authorized. F4-L1-W30 remains a Test012 conditional candidate, not independently validated.

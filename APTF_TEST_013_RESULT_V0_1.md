# APTF Test 013 Result V0.1

Status: **VALIDATION_BLOCKED**  
Acceptance: **NOT EXECUTED; not 145/145 PASS**

## Independence

Observations 101099-101220 are chronologically later than and have zero overlap with all Test012 scored candidate projections. They are independent of Test012 candidate selection, but not globally virgin because earlier Test009-011 diagnostics included the immutable reserve source.

## Blocking evidence

- Tail rows: 122 on one local trading date.
- Exactly-one-minute intrasection origins: 83.
- Valid causal F4 W15 cover: 26.
- Valid causal F4 W30 cover: 11.
- Valid causal F4 W60 cover: 0.
- Frozen W15/W30/W60 sensitivity intersection: 0.

The frozen validation contract requires primary F0/W30 evaluation plus W15/W30/W60 sensitivity, tail behavior, stability, and drift evidence. Those questions cannot be answered from 11 primary rows and no W60 rows. The contract was not weakened after cover inspection.

## Execution

The runner stopped at its pre-scoring cover assertion. Projection cores, outcomes, errors, scorecards, quantiles, perturbations, coefficients, drift metrics, and promotion gates were not produced. No candidate metric was interpreted.

## Decision

F4-L1-W30 remains a **conditional Test012 candidate**. It is neither validated nor failed by Test013. Runtime promotion is prohibited. A newly acquired, predesignated chronological dataset with adequate W60 and multi-session cover is required.
# APTF D04 Capturability Architectural Semantics V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Classification

**D. MIXTURE OF ANALYTICAL CAPTURABILITY AND EXECUTION/ACTIONABILITY.**

## Mechanical basis

Final $C=HBG$ contains two semantic families:

1. Analytical path capturability in $B$: endpoint efficiency, D01 structure, uncertainty, and reversal propensity.
2. Causal envelope realizability in $H$ and $G$: projection validity, market eligibility, data integrity, liquidity, spread, latency, execution feasibility, capital, portfolio, position, risk, and broker health.

Authority calls this “present realizability of a supplied ReturnShape under the active causal envelope.” It intentionally separates operational feasibility from base shape capturability mathematically, but multiplies both into the final score used by hysteresis.

Therefore $C$ is not pure market/direction information (A), not solely analytical $B$ (B), and not primarily execution-only (C). It is the combined final score (D).

## Does C determine what APTF wants?

In the frozen flow, YES indirectly:

```text
C -> hysteresis state -> candidate existence -> candidate direction available to D03
```

D04 candidate creation requires post-hysteresis state OPEN. D03 receives a nullable candidate and only directional candidate provenance can support the UPWARD/LONG or DOWNWARD/SHORT mapping. Thus an UPWARD or DOWNWARD ReturnShape can fail to transmit its direction to D03.

Repository authority does **not specify** the semantic proposition “UPWARD below threshold means APTF analytically desires FLAT.” What it specifies is:

- D04 treats the shape as not presently capturable/qualified.
- D04 emits factual CLOSED/no-candidate state.
- Frozen D03 contract maps CLOSED/no candidate to desired FLAT.

The control result exists, but no separate pre-gate desired-position field records what desire would have been absent D04 qualification.

## Three-question test

| Question | Owner/output | Distinct representation? |
|---|---|---|
| What direction is inferred? | D02 `ReturnShape.path_direction` | YES upstream |
| What position is desired? | D03 `DecisionRecord.desired_position_state` | YES only after D04 qualification |
| Is it capturable/actionable? | D04 `capturability_score`, envelope state, candidate | YES as D04 facts |

All three concepts have named outputs, but they are not fully independent in the end-to-end contract. D03 cannot receive a no-candidate ReturnShape direction because `path_direction` is carried to D03 only inside `CandidateEnvelope`. The collapse occurs at D04 candidate qualification: pre-gate direction is not accompanied by an independent pre-gate desired position.

## Finding

**FINDING D: D04 C MIXES ANALYTICAL CAPTURABILITY AND EXTERNAL EXECUTION/ACTIONABILITY CONCERNS.**

This is an evidence statement about the frozen formula and contract, not a recommendation to move or change it.

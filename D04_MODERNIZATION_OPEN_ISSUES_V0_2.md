# D04 Modernization Open Issues v0.2

## Mathematical (0 open; 4 resolved by deterministic design)

### M1. Geometric magnitude contribution — RESOLVED

- Existing: bounded `magnitude_score` weight 0.15.
- Why it cannot survive: score/normalization retired.
- Available: terminal displacement, maximum excursion, full path.
- Missing: chosen geometry and bounded/nonbounded contribution transform.
- Normalization/parameter: likely required unless aggregation accepts natural units; no existing valid scale.
- Resolution: parameter-free endpoint efficiency `abs(terminal_displacement) / maximum_absolute_displacement`, with exact zero-path branch. Absolute magnitude remains diagnostic because no non-arbitrary scale exists.

### M2. Support contribution — RESOLVED

- Existing: bounded `forward_support` weight 0.15.
- Available: unbounded support ratio and projected support coordinates.
- Missing: direct/path representation and any bounded monotonic transform.
- Parameter: may be required; old weight does not define scale.
- Resolution: omit support ratio from the scalar base to avoid double counting strength, persistence, uncertainty, and reversal propensity; retain it diagnostically.

### M3. Modern shape/base aggregation — RESOLVED

- Existing: seven-term shape sum and equal shape/envelope blend.
- Why it cannot survive: five terms retired/redefined; weights are experimental.
- Available: explicit geometry/state coordinates and preserved context/gate.
- Missing: admitted dimensions, transforms, weights/aggregation, and interaction with envelope component.
- Resolution: hierarchical parameter-free product of geometry quality, unweighted structural geometric mean, and unweighted risk-quality geometric mean.

### M4. Temporal capturability contribution — RESOLVED

- Existing: expected lifetime divided by target 30 seconds.
- Why it cannot survive: projection interval is extent, not expected lifetime; target has no modern authority.
- Available: projection interval, half-life, endpoint decay, staleness rule.
- Missing: whether valid temporal extent/relevance should scale capturability at all and exact formula.
- Resolution: omit soft temporal factor to avoid double counting FMO decay; enforce time through hard inclusive lifecycle validity.

## Representation (0 open; 1 resolved)

### R1. Result component vocabulary

Resolution: emit `geometry_quality`, `structural_quality`, `risk_quality`, `base_capturability_score`, `feasibility_gate_score`, `capturability_score`, hard eligibility/safety, gate values, and reasons. Retire misleading `shape_component`, `envelope_component`, and `lifetime_component` names.

## Interface (0 open; 2 resolved)

### I1. Final D04Context type — RESOLVED

Final context has 13 required typed fields. Rename `timestamp` to `evaluation_time`, remove metadata, and retain all four portfolio-capacity fields in D04 because they constrain current capturability. Exact schema: `D04_MODERNIZED_INTERFACE_SCHEMA_V0_2.json`.

### I2. Final D04 output contract — RESOLVED

Final D04Evaluation has 23 top-level factual fields and an optional five-field CandidateEnvelope. Local position/continuation commitments and all D03 decision fields are absent.

## Protocol (0 open; 1 resolved)

### P1. Candidate identity construction — RESOLVED

Candidate ID is `D04C|percent_encode_utf8(entity_id)|format17g(source_model_time)|format17g(qualified_at)`. It is deterministic, replay-stable, auditable, and score-inactive.

## Lifecycle (0 open; 1 resolved)

### L1. Detailed stale-state response — RESOLVED

Staleness is immediate safety closure. CLOSED remains CLOSED; OPENING/OPEN/CLOSING force CLOSED. Aperture becomes exactly `0.0`; hysteresis resets; candidate invalidates; factual stale/closure/invalidation events emit. A new valid shape restarts from CLOSED.

## Ownership (0)

No ownership issue remains: D04 owns candidate/envelope/lifecycle/capturability; D03 owns positions and decisions.

## Testing (0 architecture issues; implementation work specified)

### T1. Fixture migration acceptance — IMPLEMENTATION TASK SPECIFIED

Use frozen 17-field synthetic ReturnShapes and the approved deterministic formula vectors; do not reverse-engineer legacy scores.

### T2. Post-formula numerical acceptance — IMPLEMENTATION TASK SPECIFIED

Use the 14 approved mathematical vectors, property tests, and synthetic threshold analysis. No historical profitability or reserve outcomes.

## Schema decision

`D04_MODERNIZED_INTERFACE_SCHEMA_V0_2.json` is created and mechanically validated. Mathematical, representation, interface, protocol, lifecycle, ownership, and architecture issues are all zero.

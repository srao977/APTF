# APTF D02-D04-D03 Responsibility Boundary V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

## D02

- Owns deterministic representation of D01 projected geometry.
- Creates `path_direction` from terminal-displacement sign.
- Direction domain: UPWARD, DOWNWARD, FLAT.
- Does not know capturability, external context, current position, desired position, or action.
- Direction is descriptive path orientation, not LONG/SHORT advice.

## D04

- Consumes the complete ReturnShape and 13-field EnvelopeContext.
- Computes $Q_G,Q_S,Q_R,B,G,H,C$.
- Owns aperture, hysteresis, envelope state, lifecycle/safety, candidate creation/invalidation, and factual events.
- Does not change direction; candidate direction is copied verbatim.
- Can suppress candidate existence through $C$, thresholds, persistence, and safety.
- Emits one complete 23-field `EnvelopeEvaluation`; `candidate_envelope` is required but nullable.

## Formal D04 -> D03 contract

D03 receives the complete immutable `EnvelopeEvaluation`. It does not receive D02 directly. Direction is available only as nullable `candidate_envelope.path_direction`.

When D04 has no candidate:

- D03 still receives the D04 evaluation in a legitimate later invocation.
- D03 does not receive the upstream UPWARD/DOWNWARD value because no top-level direction field exists.
- Frozen D03 target rules use D04 state/safety/candidate facts; D03 does not recompute direction or rescore $C$.

D03 therefore assumes D04 has already decided candidate qualification/actionability. It has no independent pre-D04/pre-gate desired-position concept in its input or output contract.

## Boundary answers

| Question | Answer |
|---|---|
| Can D02 UPWARD fail to reach D03 as direction? | YES; runtime targets A/B prove this through nullable candidate |
| Can D02 DOWNWARD fail similarly? | YES; direction sign is irrelevant to qualification math |
| Does D04 $C$ gate candidate creation? | YES, through hysteresis/envelope OPEN state |
| Can D04 rewrite UPWARD/DOWNWARD? | NO |
| Can D03 receive raw ReturnShape direction with no candidate? | NO |
| Does D03 have an independent pre-gate desired position? | NO in the frozen contract |
| Is “below threshold means analytically desires FLAT” explicitly defined? | NOT SPECIFIED as analytical semantics; current D03 control rules map non-qualified D04 facts to FLAT |

## Collapsed boundary

Direction and capturability remain separately represented through D04, but direction-to-desire is conditional on candidate qualification. The architecture does not preserve both:

```text
pre-gate directional desired position
and
present capturability/actionability
```

as simultaneous independent fields. That distinction collapses at D04 candidate creation before D03 desired-position determination.

# D04 Directional Provenance Amendment v0.2.1

## Status

**HUMAN-AUTHORIZED PATCH AMENDMENT; IMPLEMENTED AND REGRESSION-VERIFIED.** This is not a D04 redesign and changes no D04 mathematics or lifecycle policy.

## Prior authority

This amendment is based on and preserves:

- D04 modernization design v0.2 freeze SHA256 `B5C489D060629A91DDED5B2C6EAA4076F6273AF05AED3480659CE649A1050E51`;
- D04 implementation v0.2 freeze SHA256 `7BBA0E80723EBA002EC14FABEE8D7D3B2952DF6E8730528E8D6CC9649E8A3ABC`.

Both remain immutable historical authorities. v0.2.1 supersedes v0.2 only for current D04 executable/interface authority after the v0.2.1 implementation freeze.

## Reason and human decision

D03 requires directional orientation but frozen D04 v0.2 emitted an unsigned qualified candidate. Human authority approved the exact lineage:

```text
D02 ReturnShape.path_direction
  -> D04 CandidateEnvelope.path_direction
  -> D03
```

D03 does not query D02 and does not infer direction. D04 copies the existing D02 field verbatim and does not recompute, normalize, threshold, reinterpret, or adapt it.

## D02 source authority

- field: `ReturnShape.path_direction`;
- type: `d02.v02.models.PathDirection`, a string enum;
- domain: `UPWARD`, `DOWNWARD`, `FLAT`;
- initialization: D02 builder maps positive terminal displacement to UPWARD, negative to DOWNWARD, and exact zero to FLAT;
- serialization: `ReturnShape.to_dict()` emits `path_direction.value`;
- semantic owner: frozen D02;
- causal availability: yes, at ReturnShape construction from causal D01 DMO/FMO.

D01 and D02 are unchanged.

## Exact interface delta

Old CandidateEnvelope: five fields.

New CandidateEnvelope: the same five fields plus required `path_direction: PathDirection`, total six. The D04Evaluation still has exactly 23 top-level fields because `candidate_envelope` remains one nullable nested field.

The candidate model is frozen/immutable. Copy-on-write invalidation changes only status and preserves direction.

## Candidate creation and lifecycle

The sole production constructor assigns:

```text
candidate.path_direction = source ReturnShape.path_direction
```

Context reevaluation retains the same candidate. Supersession invalidates the old candidate and constructs any replacement from the new ReturnShape, so old direction cannot leak. Stale/safety invalidation preserves the invalidated candidate's source direction. Recovery uses only a newly qualified candidate and its new source shape.

## Identity

Candidate identity remains exactly:

```text
D04C|percent_encode_utf8(entity_id)|format17g(source_model_time)|format17g(qualified_at)
```

`path_direction` is provenance and is not added to identity. The source ReturnShape identity already binds the candidate to the shape from which direction is copied.

## Non-drift guarantees

Unchanged: Q_G, Q_S, Q_R, B, G, H, C, aperture, hysteresis, envelope state machine, qualification, identity, staleness, supersession behavior, recovery, context, scenarios, event ontology, and 23-field top-level evaluation.

## D03 consequence

D03 consumes `D04Evaluation.candidate_envelope.path_direction` and maps the exact D02 domain to desired position: UPWARD to LONG, DOWNWARD to SHORT, FLAT to FLAT/no directional trade. No direct D02 D03 edge is authorized.

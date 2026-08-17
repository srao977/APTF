# D04 Candidate Contract v0.2.1

## Status

Patch contract for D04 CandidateEnvelope under the directional-provenance amendment. Candidate is a required nullable field of the unchanged 23-field D04Evaluation.

## Exact six-field contract

| # | Field | Type | Required | Semantic owner | Meaning |
|---:|---|---|---:|---|---|
| 1 | `candidate_id` | string | Yes | D04 | Deterministic candidate identity |
| 2 | `entity_id` | string | Yes | D04/upstream identity | Candidate entity |
| 3 | `source_return_shape_model_time` | finite float seconds | Yes | D02 lineage carried by D04 | Source ReturnShape identity component |
| 4 | `qualified_at` | finite float seconds | Yes | D04 | Causal D04 qualification time |
| 5 | `status` | `QUALIFIED|INVALIDATED` | Yes | D04 | Candidate lifecycle status |
| 6 | `path_direction` | `d02.v02.models.PathDirection` | Yes | D02 semantic authority; D04 provenance carrier | Verbatim orientation of source ReturnShape |

Extra fields are forbidden. The model is immutable; lifecycle changes use copy-on-write.

## Direction provenance

```text
CandidateEnvelope.path_direction is source ReturnShape.path_direction
```

- source: `D02 ReturnShape.path_direction`;
- enum values: `UPWARD`, `DOWNWARD`, `FLAT`;
- adaptive: NO;
- inferred by D04: NO;
- recomputed by D04: NO;
- normalized or thresholded: NO;
- mutable: NO;
- causal at qualification: YES;
- deterministic: YES;
- auditable/serialized: YES, enum value string;
- available to D03: YES.

Direction remains associated with the source ReturnShape model time and candidate ID for the candidate lifetime. Invalidation preserves it. A superseding candidate receives only its own source shape direction.

## Identity and evaluation shape

Identity is unchanged and excludes direction. D04Evaluation remains 23 top-level fields; only the nested CandidateEnvelope field count changes from five to six.

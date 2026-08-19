# APTF D04-to-D03 Field Lineage V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

D03 consumes one complete immutable 23-field `EnvelopeEvaluation`. Every field crosses the schema/fingerprint boundary, but only a subset is target-active.

## Direct D03 reads

| D04 field | Type | Semantic | D03 read location/use | LONG | SHORT | FLAT | Veto capability | Mandatory |
|---|---|---|---|---|---|---|---|---|
| `evaluation_time` | float | D04 causal time | D03Input time invariant; source record | NO | NO | NO | invalid time relation rejects | YES |
| `entity_id` | str | evaluated entity | D03Input entity invariant; output identity | NO | NO | NO | mismatch rejects | YES |
| `return_shape_model_time` | float | D02 lineage | source record | NO | NO | NO | no target veto | YES |
| `new_envelope_state` | enum | post-D04 state | R31-R41 branching; source record | OPEN required | OPEN required | CLOSED/OPENING/CLOSING or OPEN subcases | YES | YES |
| `projection_valid` | bool | lifecycle validity | R30 | must be true | must be true | false -> FLAT | YES | YES |
| `stale` | bool | lifecycle invalidity | R30 | must be false | must be false | true -> FLAT | YES | YES |
| `safety_state` | CLEAR/SAFETY_CLOSED | safety fact | R30; source record | must be CLEAR | must be CLEAR | SAFETY_CLOSED -> FLAT | YES | YES |
| `safety_reason` | enum/null | safety detail | R30 supporting reason | NO | NO | reason lineage | accompanies veto | YES nullable |
| `candidate_envelope` | candidate/null | candidate fact | R34-R41 | required | required | absence can produce FLAT | YES | YES nullable |
| `candidate.status` | QUALIFIED/INVALIDATED | candidate lifecycle | R35-R41 | QUALIFIED | QUALIFIED | nonqualified -> FLAT | YES | if candidate |
| `candidate.path_direction` | UPWARD/DOWNWARD/FLAT | verbatim D02 orientation | R36/R40/R41 | UPWARD | DOWNWARD | FLAT | selects sign after qualification | YES if candidate |
| `candidate.candidate_id` | str | candidate identity | lineage for R36/R40/R41 | lineage | lineage | lineage for analytical FLAT | NO | if candidate |
| `candidate.source_return_shape_model_time` | float | candidate source lineage | lineage | lineage | lineage | lineage | NO | if candidate |

Candidate `entity_id` and `qualified_at` cross in the nested object/fingerprint but are not read by `_resolve_target_rule`.

## Fields not directly used for target selection

The following cross the immutable object and fingerprint but D03 does not threshold, recombine, or branch on them:

- `source_model_version`
- `hard_eligibility`
- `geometry_quality`
- `structural_quality`
- `risk_quality`
- `base_capturability_score`
- `feasibility_gate_score`
- `capturability_score`
- `previous_envelope_state`
- `aperture_before`, `aperture_after`
- `gate_dimension_values`
- `reason_codes`
- `events`

They can still causally affect desired position upstream when D04 uses them/underlying inputs to create state or candidates. D03 reads only the resolved factual state/candidate boundary.

## Direction lineage

```text
D02 ReturnShape.path_direction
  -> D04 validates sign consistency
  -> D04 CandidateEnvelope.path_direction = ReturnShape.path_direction
  -> D03 R36/R40/R41
```

D04 cannot reverse or flatten the sign. It can only withhold/invalidate the candidate. Qualified mappings are conditional on higher-priority D03 controls and D04 safety/state:

- qualified UPWARD -> LONG: CONDITIONAL;
- qualified DOWNWARD -> SHORT: CONDITIONAL;
- qualified FLAT -> FLAT: CONDITIONAL.

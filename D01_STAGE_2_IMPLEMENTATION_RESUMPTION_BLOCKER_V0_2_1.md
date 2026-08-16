# D01 Stage 2 Implementation Resumption Blocker v0.2.1

## Status

**STAGE_2_IMPLEMENTATION_DESIGN_AMBIGUITY**

Implementation resumed against both frozen Stage 2 authorities but cannot be frozen or authorized for historical execution.

## Authority Integrity

- Stage 1 freeze ID and protected hashes: PASS
- Parent Stage 2 Design v0.2 freeze SHA256: PASS
- Five parent specification hashes: 5/5 PASS
- Scoring clarification v0.2.1 freeze SHA256: PASS
- Scoring clarification protected artifacts: PASS
- Dataset identity: PASS
- D01 modified: NO

## Resolved Original Ambiguities

The v0.2.1 clarification successfully resolves:

- realized ambiguity-index formula;
- uncertainty primary statistic and null;
- state/kinematics C15 statistic and null;
- perturbation transition-magnitude formula and 15-minute primary;
- perturbation-class co-primary contrasts and adjudication;
- exact/right/interval-censored comparable-pair concordance and nulls.

## Newly Exposed Blocking Ambiguity

The frozen evidence contracts specify multiple applicable horizons for three dimensions:

```text
Strength:
    5/15/30/60 and adaptive interval

Coherence:
    5/15/30/60

Uncertainty:
    5/15/30/60 and adaptive
```

The frozen multiplicity policy requires:

```text
Each semantic dimension has one primary pre-registered effect/contrast.
```

The v0.2.1 clarification freezes 15 minutes as the primary fixed horizon only for:

- state/kinematics;
- perturbation magnitude;
- perturbation-class contrasts.

It does not select a primary horizon or deterministic horizon aggregation for strength, coherence, or uncertainty.

## Why Implementation Cannot Choose

Each possible implementation changes the primary scientific effect:

- selecting 15 minutes would extend a clarification beyond its explicit scope;
- pooling anchor/horizon rows changes weighting and dependence;
- averaging horizon-specific Spearman coefficients requires a weighting rule;
- selecting an adaptive coordinate changes the semantic claim;
- reporting several co-primary effects conflicts with one-primary-effect multiplicity language unless explicitly authorized.

No choice can be derived mechanically from the frozen texts. Selecting one during implementation would violate the prohibition on silently resolving scientific ambiguity.

## Required Frozen Clarification

A successor human-approved scoring clarification must define, for each of strength, coherence, and uncertainty:

1. the single primary horizon, or an exact deterministic horizon aggregation;
2. the primary anchor population when adaptive and fixed coordinates coexist;
3. the effect calculation when an anchor lacks one or more coordinates;
4. the bootstrap record unit and weighting under that horizon policy;
5. confirmation that all other horizons remain secondary diagnostics.

The simplest candidate is a frozen 15-minute primary for all three, but this document does not authorize that choice.

## Partial Implementation State

A separate `src/d01_stage2` infrastructure layer, synthetic tests, preflight mode, dry-run mode, Python runner, and PowerShell launcher have been created. The full runner intentionally fails before historical replay with `SCORING_SPEC_AMBIGUITY`.

These files are not an approved implementation candidate and have not been frozen. The launcher must not be run.

## Validation Completed

- Synthetic focused tests: 24/24 PASS
- Synthetic deterministic replay: PASS
- Synthetic process smoke: PASS
- Metadata/hash-only preflight: PASS
- Synthetic-only dry-run: PASS
- Historical dataset opened by dry-run: NO
- Primary historical replay started: NO
- Primary scientific results calculated: NO
- Reserve values accessed: NO

## Artifacts Intentionally Not Created

- `D01_STAGE_2_IMPLEMENTATION_MANIFEST_V0_2_1.json`
- `D01_STAGE_2_IMPLEMENTATION_READINESS_REVIEW_V0_2_1.md`
- `D01_STAGE_2_IMPLEMENTATION_V0_2_1_FREEZE.json`

They cannot truthfully report readiness while the scientific primary-effect policy is unresolved.

## Final Decision

**DO NOT RUN HISTORICAL REPLAY**

Required action: approve and freeze the missing primary-horizon/aggregation policy for strength, coherence, and uncertainty, then complete and revalidate the implementation.
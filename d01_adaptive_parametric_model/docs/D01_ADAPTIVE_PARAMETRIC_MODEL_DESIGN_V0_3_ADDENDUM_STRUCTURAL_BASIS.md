# D01 Adaptive Parametric Model Design v0.3 Addendum (Structural Basis)

## Objective
Define a structural-only, provider-capability-aware basis independence pass for D01 v0.1.2.

## Inputs
- Provider capabilities and active channel map.
- Feature manifest and lineage produced by the configured model.
- Historical SPY Phase 1/2/3 windows.

## Structural Rules
- Phase 1 is the only discovery phase.
- Retained basis is frozen and reused unchanged for Phase 2 and Phase 3.
- Retention is deterministic and structural; no predictive metric criteria are allowed.

## Dependency Detection
- Incremental-rank admission with numerical tolerance derived from singular values.
- Dependency evidence categories:
  - exact equality
  - sign reversal
  - constant multiple
  - affine with intercept
  - numerical linear dependence
  - high correlation flag (non-blocking classification aid)

## Outputs
- Feature inventory and dependency diagnostics.
- Dependency groups and basis dimension summary.
- Per-experiment basis manifests including SHA256 basis signature.
- Structural basis validation report.

## Non-Goals
- No predictive metrics.
- No EXP001B replay.
- No D02/D04 execution.
- No broker interaction.

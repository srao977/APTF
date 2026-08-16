# D01 Adaptive Parametric Model Design V0.3 Addendum (v0.1.2)

This addendum introduces a permanent feature-space property:

D01 feature space is conditional on actual observation-channel availability.

## Pipeline
Provider Capability
-> Observation Availability
-> Derivable Features
-> Feature Admissibility
-> Active Parametric Basis

## Key properties
- No synthetic placeholder channels for unavailable observations.
- Stable active feature dimension per model run.
- Polynomial and interaction generation over admissible active features only.
- Per-run feature lineage and manifest for deterministic auditability.

# D01 v0.1.2 Feature Structure Correction

## 1. Problem discovered in EXP001
EXP001 used synthetic placeholders for unavailable quote/trade channels in historical SPY OHLCV replay.

## 2. EXP001A diagnosis
EXP001A found structural singularity, including rank deficiency and infinite condition numbers for several configurations.

## 3. Architectural principle
Unavailable observation channels are excluded from active feature space and are never represented as synthetic zeros or copied fields.

## 4. Observation availability
D01 now consumes explicit channel availability and provider capability declarations.

## 5. Provider capability contract
A provider-neutral `ObservationCapabilities` contract is used to declare available/unavailable channels.

## 6. Active Channel Map
Capabilities are converted into an `ActiveChannelMap` persisted in feature manifests.

## 7. Feature dependency graph
Base features declare required source channels. Missing requirements mark features structurally inactive.

## 8. Feature Admissibility Gate
Admissibility is structural: required channels present, finite values, and stable initialization-time feature set.

## 9. Static vs causal admissibility
Static structure determines membership. Causal diagnostics are tracked but do not perform future-leaking selection.

## 10. Stable parameter dimension
Active base features are fixed at model initialization, preserving deterministic adaptive state evolution.

## 11. Feature lineage
Each active/inactive feature is emitted with derivation metadata in per-worker `feature_manifest.json`.

## 12. Quote-feature correction
`spread`/`spread_change` are only active when bid/ask channels are truly available.

## 13. Volume semantics
Bar `volume` remains bar volume. `trade_size` is not fabricated from `volume`.

## 14. Polynomial implications
Polynomial terms are generated only from active admissible base features.

## 15. Interaction implications
Interactions are generated only from active admissible base features.

## 16. Tests
v0.1.2 tests cover capability cases, unavailable-vs-zero semantics, deterministic map/lineage, intercept policy, and admissible polynomial/interaction generation.

## 17. Numerical validation
A hard gate validates A_n1/B_n1/D_n2/E_n3 on Phase 1 before full EXP001B execution.

## 18. Compatibility
v0.1.1 remains unchanged and reproducible. v0.1.2 is additive and structural.

## 19. Limitations
This release does not retune predictive math and does not include reserve data, D02, D04, or trading execution.

## 20. Version rationale
v0.1.2 is a narrow structural correction release, not a new model family.

# D04 Trading Envelope Implementation Delta v0.2

## In-place implementation delta

- Added the frozen D02 package dependency and replaced the local ReturnShape shadow with direct re-exports.
- Replaced legacy weighted capturability with exact deterministic geometry, structure, risk, base, ten-gate, eligibility, and final score components.
- Added deterministic-view validation and canonical invalid-shape safety closure.
- Replaced legacy context/output/opportunity models with exact 13/23/5-field contracts.
- Removed trade direction, continuation/position commitment, legacy score, lifetime target, and untyped metadata semantics.
- Modernized the existing TradingEnvelope for per-entity ordering, context reevaluation, supersession, stale safety, candidate identity, invalidation, and recovery.
- Retained hysteresis-before-aperture normal execution and bypass/reset safety execution.
- Updated existing CLI, realtime event flow, and JSONL audit serialization to canonical facts.
- Replaced legacy scenario score fixtures with explicit natural D02 geometry/state and causal context.
- Migrated all 23 baseline tests and added 46 modernization cases.

## Deliberate non-deltas

No D01, frozen D02, D03, design-freeze artifact, reserve data, historical replay, aperture mathematics, hysteresis mathematics, event-bus architecture, or four-state ontology was changed.

The unrelated pre-existing deletion of `d04_trading_envelope/output/run_all_v02.txt` is outside this delta and remains untouched.

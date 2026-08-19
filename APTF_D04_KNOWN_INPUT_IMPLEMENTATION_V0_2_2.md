# APTF D04 Known-Input Implementation V0.2.2

Status: IMPLEMENTED CORRECTION
Date: 2026-08-18

## Changes

- `EnvelopeContext` adds production/test role and complete provenance metadata.
- Eleven unavailable fields are nullable and explicitly `UNAVAILABLE` in production.
- `active_gate_values` excludes unavailable dimensions and rejects an empty active set.
- Capturability G uses active known configured dimensions only.
- H treats only known false market eligibility as ineligible; unavailable does not fabricate truth.
- TradingEnvelope safety follows the same known/absent rule.
- Real replay, temporal proof, and diagnostic builders use `EnvelopeContext.production` with derived evaluation time and data integrity only.
- Real replay builds D04 from authoritative `default.yaml`, removing the proof-only integrity threshold override.
- Synthetic D04 fixtures are mechanically tagged `TEST_FIXTURE` and retain full ten-gate tests.

## Unchanged

Q_G, Q_S, Q_R, B, threshold 0.75, threshold 0.55, hysteresis counts 3/2, aperture, candidate construction, D01, D02, D03, controller, temporal envelope, and historical evidence are unchanged.

## Validation

Dedicated provenance tests prove null/0/1 distinction, active provenance enforcement, test/production separation, unavailable market eligibility behavior, and zero fixed-neutral injections in real builders. Complete D04 synthetic/unit regression passes 86/86.

## Freeze Relationship

Existing D04, real-integration, and Temporal Runtime freeze manifests are preserved byte-identically, but their old hashes for the authorized changed source files are historical. V0.2.2 supersedes only D04 context-authority construction/applicability on those paths. It is not a new full-system mathematical freeze.

# APTF D04 Known-Input Authority Audit V0.1

Status: PASS / CORRECTION IMPLEMENTED
Date: 2026-08-18

## Finding

The real-market path fabricated eleven of thirteen EnvelopeContext values because the frozen V0.2 schema required all fields and defined no absence/applicability semantics. Nine fixed 1.0 fields entered G, fixed `market_eligible=true` entered H, and fixed clock quality was diagnostic. The real replay also overrode the authoritative integrity threshold from 0.2 to 0.0 solely for proof operation.

This is a design contract gap and implementation defect in input authority. Q_G/Q_S/Q_R and threshold calibration are not the defect.

## Complete Inventory

The exact D04 consumed-property inventory is 43:

| Group | Count | Current status |
|---|---:|---|
| D02 ReturnShape | 17 | all known derived active inputs |
| EnvelopeContext scientific values | 13 | 2 active derived; 11 future/unavailable |
| D04 persistent state | 5 | known state |
| D04 configuration constants | 8 | authoritative config/intrinsic constants |

Active known nonconstant properties: 24. Legitimate configuration constants: 8. Future/unavailable: 11. Unknown active: 0.

The complete property table is `APTF_D04_INPUT_PROVENANCE_INVENTORY_V0_1.json`.

## Test 003 Gate Provenance

| Gate | Property | Test 003 value | Previous authority |
|---|---|---:|---|
| g1 | liquidity_quality | 1.0 | placeholder |
| g2 | spread_quality | 1.0 | placeholder |
| g3 | latency_quality | 1.0 | placeholder |
| g4 | execution_feasibility | 1.0 | placeholder |
| g5 | capital_available | 1.0 | placeholder |
| g6 | portfolio_capacity | 1.0 | placeholder |
| g7 | position_capacity | 1.0 | placeholder |
| g8 | risk_capacity | 1.0 | placeholder |
| g9 | broker_health | 1.0 | placeholder |
| g10 | data_integrity | 1.0 | legitimately derived from data_valid/source quality |

Historical `G=1.0` was placeholder-affected. Corrected production G uses only active known configured dimensions; currently `G_active=min(data_integrity)`. For the stored valid Test 003 rows this is still 1.0, so arithmetic remains unchanged.

## H Provenance

H retains projection validity from D02/context time, known data integrity versus authoritative threshold, and valid finite input checks. Historical fixed `market_eligible=true` was a placeholder. Corrected unavailable market eligibility is null and omitted; known false remains a hard failure. Tests 001-003 had projection-valid shapes and known data integrity 1, so corrected H remains 1 for their stored rows.

## Q Provenance

- Q_G: D02 terminal displacement and maximum path excursion, both derived from real D01 FMO.
- Q_S: frozen D01 strength/coherence/persistence copied by D02.
- Q_R: frozen D01 uncertainty/reversal propensity copied by D02.

All are known derived/stateful inputs with no placeholder.

## Correction

`EnvelopeContext` now carries `context_role` and complete provenance. Production requires every scientific field classified; null iff UNAVAILABLE; TEST_FIXTURE forbidden. Eleven fields are nullable unavailable. `active_gate_values` excludes unavailable values and rejects empty sets. Required derived data integrity proves a nonempty active G under current config.

Real-market builders now activate only evaluation time and data integrity. The replay envelope is constructed from authoritative default config, removing all duplicated constants and the 0.0 integrity override.

Synthetic unit scenarios remain valid and are mechanically tagged TEST_FIXTURE. They can still supply numeric 0/1 to test formula boundaries without being confused with production evidence.

## Historical Evidence

Tests 001, 002, 002A, 003, and 003A remain byte-identical. Their D04 arithmetic is internally correct for the values supplied, but input authority was defective. Because removed values were neutral/pass values and corrected active G/H remain 1 on the stored valid rows, the stored C values do not change. Another arithmetic reconstruction is not required; any future real-market execution must use corrected provenance.

## Non-Drift

Q_G, Q_S, Q_R, B, open 0.75, close 0.55, hysteresis 3/2, aperture 0.5, D01, D02, D03, controller semantics, temporal instrumentation, market data, and historical evidence are unchanged. Old D04, real-integration, and temporal freeze manifests remain historical and are not rewritten. Their bindings to authorized changed files are superseded only for this context-authority correction; authorized implementation hashes are recorded in the validation artifact.

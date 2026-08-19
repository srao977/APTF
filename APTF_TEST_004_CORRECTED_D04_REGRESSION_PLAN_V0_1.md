# APTF Test 004 Corrected D04 Regression Plan V0.1

Status: EXECUTED REGRESSION EVIDENCE
Date: 2026-08-18

## Scope

Run exactly physical rows 10-14 from the authoritative normalized SPY source through one continuing corrected pipeline. Establish the same pre-row-10 state as Test 003 using data indices 0-7. Read no row after 14. Compare each cycle immediately with immutable Test 003 evidence and stop before the next row on any unexpected deterministic divergence.

## Corrected Authority

- Contract: `APTF_D04_KNOWN_INPUT_CONTEXT_CONTRACT_V0_2_2.md`.
- Schema: `D04_KNOWN_INPUT_CONTEXT_SCHEMA_V0_2_2.json`.
- Implementation: `APTF_D04_KNOWN_INPUT_IMPLEMENTATION_V0_2_2.md`.
- Authoritative config: `d04_trading_envelope/config/default.yaml`.
- Integrity threshold 0.2; open/close 0.75/0.55; persistence 3/2.

Production context activates derived `evaluation_time` and `data_integrity`; eleven future dimensions are null/UNAVAILABLE. Current G is `min(data_integrity)`. No broker, portfolio, account, liquidity, spread, execution, or infrastructure values are injected.

## Regression Equality

Exact equality is required for complete D01 DMO/FMO, complete D02 ReturnShape, D04 numeric fields, D04 lifecycle/semantic fields, D03 rule/position semantics, and Position Controller semantics. Tolerance is 0.0 because frozen deterministic outputs are compared as serialized Python values.

Expected provenance representation changes are not mathematical failures:

- D04 `gate_dimension_values`: ten numeric fields -> `{data_integrity: 1.0}`;
- D04/D03 fingerprints and IDs change because the complete D04 payload changes;
- controller transition identity changes because its originating D03 identity/hash changes.

Timing, UTC processing fields, execution UUIDs, and temporal event IDs are newly measured and not required to equal Test 003.

## Discipline

No code repair or tuning occurs during Test 004. No threshold/reachability/profitability analysis. No artificial one-minute wait. Historical Test 003 and Test 003A artifacts remain unchanged.

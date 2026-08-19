# APTF D04 Four-Factor Freeze Authority V0.1

Freeze ID: `D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1`  
Status: **FROZEN**  
Created: `2026-08-18T21:44:15.6360664Z`

## Current Authority

Current authoritative executable D04 capturability:

$$
C = H Q_G Q_S Q_R
$$

Active factors: `H`, `Q_G`, `Q_S`, `Q_R`.

`data_integrity` and `G` are not part of current D04. No neutral or placeholder replacement exists. Data quality and observation validity belong to upstream observation admission; a rejected observation does not enter D01 or D04.

## Factor Formulas

```text
H   = int(projection_valid and market_eligible is not False)
Q_G = 0 when maximum_absolute_displacement == 0,
      otherwise abs(terminal_displacement) / maximum_absolute_displacement
Q_S = (strength * coherence * persistence) ** (1 / 3)
Q_R = sqrt((1 - uncertainty) * (1 - reversal_propensity))
C   = H * Q_G * Q_S * Q_R
```

These formulas are frozen exactly as implemented in `capturability_model.py`.

## Threshold And State Authority

- Opening threshold: `0.75`
- Closing threshold: `0.55`
- Opening persistence: `3` observations
- Closing persistence: `2` observations
- States: `CLOSED`, `OPENING`, `OPEN`, `CLOSING`

`hysteresis.py`, `lifecycle.py`, `enums.py`, and `default.yaml` are the state/threshold authority. This freeze does not introduce `OPENING_1` or `OPENING_2` as separate enum values; progression is represented by the `OPENING` state plus the persistence counter.

## Future Concepts

Broker health, capital availability, execution feasibility, latency quality, liquidity quality, portfolio capacity, position capacity, risk capacity, and spread quality are classified as **FUTURE / NON-EXECUTABLE / NO CURRENT NUMERIC PARTICIPATION**. They are not active factors, runtime fields, or placeholder values. No Active/Inactive mechanism is implemented by this freeze.

## Validation Authority

Validated by: **Test 004R**  
Validation status: **PASS**  
Acceptance: **60/60 PASS**  
Maximum historical C delta: `0.0`  
Maximum four-factor reconstruction error: `0.0`

Numeric anchors for physical rows 10-14:

| Row | C |
|---:|---:|
| 10 | 0.22050421416872243 |
| 11 | 0.17666062360338286 |
| 12 | 0.25462532958949513 |
| 13 | 0.08848558708732783 |
| 14 | 0.28034113293008417 |

Semantic regression anchors are D04 `CLOSED` x5, D03 `FLAT` x5, and Position Controller `NO_ACTION` x5. These are regression anchors, not universal expected behavior.

## Identity And Scope

The 17 frozen authority files and SHA-256 values are recorded in `APTF_D04_FOUR_FACTOR_FREEZE_HASHES_V0_1.json`. Test 004R did not embed a complete source hash manifest, so identity uses the strongest available provenance chain: authority files predate the Test 004R trace, Test 004R exercised the live dependency path, the post-change audit passed, and pre-freeze hashes show no drift.

Temporal authority is referenced, not absorbed or modified. D01, D02, D03, Position Controller, market data, and pipeline orchestration remain outside this D04 freeze.

The stopped preliminary Test 005 plan and harness are **ABORTED / NON-AUTHORITATIVE** and are not freeze evidence. No Test 005 result or measured evidence exists.
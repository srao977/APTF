# APTF Test 004 Corrected D04 Five-Cycle Regression Result V0.1

Status: PASS
Primary result: **RESULT A**
Date: 2026-08-18

## Source And Initial State

Authoritative source: `data/market/normalized/SPY_1min_normalized_v0_1.csv`, SHA256 `73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`.

Physical rows 10-14 matched Test 003 timestamps and OHLCV exactly. Physical row 15 was not read. Test 004 pre-row-10 D01, D04, and internal controller snapshots exactly equal Test 003; canonical snapshot hashes match.

## Corrected D04 Authority

- `APTF_D04_KNOWN_INPUT_CONTEXT_CONTRACT_V0_2_2.md`
- `D04_KNOWN_INPUT_CONTEXT_SCHEMA_V0_2_2.json`
- `APTF_D04_KNOWN_INPUT_IMPLEMENTATION_V0_2_2.md`
- authoritative config `d04_trading_envelope/config/default.yaml`

Integrity threshold 0.2, no 0.0 override. Open/close thresholds 0.75/0.55 and persistence 3/2 unchanged.

Every cycle has two active known context fields (`evaluation_time`, `data_integrity`) and eleven null/UNAVAILABLE fields. G has one active configured input `{data_integrity: 1.0}`. Active placeholders and unknown active inputs are zero.

## Primary Five-Cycle Table

| Cycle | Row | Time | OHLC | Volume | D01 level | Velocity | Acceleration | D02 terminal | Direction | H | Q_G | Q_S | Q_R | G | Aperture | C | Margin | D04 | Candidate | D03 rule | D03 Position | PC Decision |
|---:|---:|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| 1 | 10 | 08:08 | 365.68/365.70/365.50/365.50 | 4288 | -0.6571388532831072 | -0.0009453815512633182 | 0.000043598246210338045 | 0.01978985584654247 | UPWARD | 1 | 1.0 | 0.6043625386410295 | 0.36485420599454843 | 1.0 | 0.2490565349467589 | 0.22050421416872243 | -0.5294957858312775 | CLOSED | null | R31/T20 | FLAT | NO_ACTION |
| 2 | 11 | 08:09 | 365.54/365.54/365.49/365.49 | 758 | -0.6487986245281485 | 0.00013900381255947696 | 0.000018073089394034406 | 0.026416809218216097 | UPWARD | 1 | 1.0 | 0.3667482303751486 | 0.48169454948065005 | 1.0 | 0.21285857927507087 | 0.17666062360338286 | -0.5733393763966171 | CLOSED | null | R31/T20 | FLAT | NO_ACTION |
| 3 | 12 | 08:10 | 365.50/365.58/365.48/365.57 | 1318 | -0.5253444238218404 | 0.002057570011428873 | 0.000031976103309160583 | 0.1502039423029219 | UPWARD | 1 | 1.0 | 0.5043730622546775 | 0.5048353067296146 | 1.0 | 0.23374195443228302 | 0.25462532958949513 | -0.49537467041050487 | CLOSED | null | R31/T20 | FLAT | NO_ACTION |
| 4 | 13 | 08:11 | 365.59/365.59/365.59/365.59 | 100 | -0.4852739124662928 | 0.0006678418558144867 | -0.00002316213592304608 | 0.006548303521185184 | UPWARD | 1 | 0.6832134425301885 | 0.2808653989173412 | 0.46112417816135437 | 1.0 | 0.16111377075980543 | 0.08848558708732783 | -0.6615144129126722 | CLOSED | null | R31/T20 | FLAT | NO_ACTION |
| 5 | 14 | 08:12 | 365.60/365.60/365.60/365.60 | 920 | -0.46006103401656456 | 0.0004202146407587684 | -0.0000041271202502407854 | 0.017447816321678744 | UPWARD | 1 | 1.0 | 0.5555355673592773 | 0.5046321953114142 | 1.0 | 0.2207274518449448 | 0.28034113293008417 | -0.46965886706991583 | CLOSED | null | R31/T20 | FLAT | NO_ACTION |

Every full D03 rule is `TARGET:R31|TRANSITION:T20|OVERLAYS:NONE`.

## Test 003 Versus Test 004

| Cycle | Test 003 C | Test 004 C | Delta | Test 003 aperture | Test 004 aperture | D04 state | D03 Position | PC Decision | Status |
|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 1 | 0.22050421416872243 | 0.22050421416872243 | 0.0 | 0.2490565349467589 | 0.2490565349467589 | CLOSED=CLOSED | FLAT=FLAT | NO_ACTION=NO_ACTION | PASS_PROVENANCE_CORRECTED |
| 2 | 0.17666062360338286 | 0.17666062360338286 | 0.0 | 0.21285857927507087 | 0.21285857927507087 | CLOSED=CLOSED | FLAT=FLAT | NO_ACTION=NO_ACTION | PASS_PROVENANCE_CORRECTED |
| 3 | 0.25462532958949513 | 0.25462532958949513 | 0.0 | 0.23374195443228302 | 0.23374195443228302 | CLOSED=CLOSED | FLAT=FLAT | NO_ACTION=NO_ACTION | PASS_PROVENANCE_CORRECTED |
| 4 | 0.08848558708732783 | 0.08848558708732783 | 0.0 | 0.16111377075980543 | 0.16111377075980543 | CLOSED=CLOSED | FLAT=FLAT | NO_ACTION=NO_ACTION | PASS_PROVENANCE_CORRECTED |
| 5 | 0.28034113293008417 | 0.28034113293008417 | 0.0 | 0.2207274518449448 | 0.2207274518449448 | CLOSED=CLOSED | FLAT=FLAT | NO_ACTION=NO_ACTION | PASS_PROVENANCE_CORRECTED |

Numeric regression coverage: 150 rows, tolerance 0.0, maximum absolute delta 0.0.

## Provenance Regression

| Property family | Test 003 | Test 004 | Numeric result | Correction |
|---|---|---|---|---|
| market_eligible | literal true | null/UNAVAILABLE | H remains 1 from known applicable facts | corrected |
| clock_event_quality | literal 1.0 | null/UNAVAILABLE | score-inactive | corrected |
| nine future G dimensions | literal 1.0 | null/UNAVAILABLE | removed from active min | corrected |
| data_integrity | derived 1.0 | derived 1.0 | active G=1 and H pass | retained legitimate |
| integrity threshold | harness 0.0 | config 0.2 | stored valid rows still pass | corrected |

All 12 affected properties are recorded for all five cycles (60 rows). Test 003 G used ten fields; Test 004 G uses `{data_integrity: 1.0}`. The numeric G result is equal, while provenance/applicability is corrected.

Because D04 `gate_dimension_values` is part of the payload, expected identities changed: D04 event ID; D03 source/input fingerprints, decision ID, and event ID; controller transition ID and event ID. These are correct content-identity changes, not semantic regressions.

## Mathematical And Semantic Regression

- Complete D01 DMO/FMO: PASS 5/5.
- Complete D02 ReturnShape: PASS 5/5.
- H, Q_G, Q_S, Q_R, G, C, aperture, and gate margin: PASS 5/5.
- D04 lifecycle state/candidate/reasons/events: PASS 5/5.
- D03 rule/Position: PASS 5/5.
- Position Controller internal-state/decision semantics: PASS 5/5.

## State And Temporal Validation

Initial state and four D01/D04/controller handoffs match exactly. Five observation IDs are unique and each is preserved E0-E5. Five parent chains are complete; cross-observation parent links are absent. No reset and no artificial wait occurred.

## Timing

| Cycle | Direct ns | Direct us | Direct ms | Math ns | All-stage ns | Delta all ns | Inter-cycle gap ns |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1663700 | 1663.7 | 1.6637 | 169600 | 183500 | 1480200 | N/A |
| 2 | 1487200 | 1487.2 | 1.4872 | 176600 | 185000 | 1302200 | 1151300 |
| 3 | 1506000 | 1506.0 | 1.5060 | 178800 | 187700 | 1318300 | 1009500 |
| 4 | 1541100 | 1541.1 | 1.5411 | 193200 | 201500 | 1339600 | 1230300 |
| 5 | 1515100 | 1515.1 | 1.5151 | 185900 | 193600 | 1321500 | 1194300 |

Timing is descriptive only and was not compared for equality with Test 003. Canonical values are integer nanoseconds with nanosecond resolution, not an accuracy claim.

## Execution Discipline

Rows 10-14 only; row 15 unread. No threshold, hysteresis, parameter, reachability, profitability, broker/portfolio, Azure, concurrency, queue, or code repair occurred during regression execution.

## Primary Result

**RESULT A: FULL MATHEMATICAL AND SEMANTIC REGRESSION PASS. CORRECTED D04 PROVENANCE CHANGED AS INTENDED. TEST 003 NUMERICAL/SEMANTIC RESULT SURVIVES.**

The D04 known-input authority defect was real. The correction removed arbitrary runtime evidence. The correction did not cause the five observed Test 003 capturability/state/decision values. Therefore the five-cycle NO_ACTION result remains a valid property of the corrected pipeline for this exact market sequence and starting state. No generalization is made beyond these observations.

## Acceptance

G01-G60: **60/60 PASS**.

Post-test protected audit: Test 003/003A 18/18 unchanged; corrected authority artifacts 10/10 unchanged; corrected implementation bindings 9/9 unchanged; source and unaffected D01/D02/D03/controller/temporal core 7/7 unchanged. No new full-system freeze is created.

# APTF Benchmark Decision Metadata Contract v0.1

## 1. Purpose and status

**Status: INCOMPLETE - BLOCKED SOURCE CONTRACT. NOT FROZEN.**

This document records the benchmark metadata discovery result without using reserve rows or inventing benchmark semantics. It does not authorize benchmark access, replay, backtesting, normalization, or model changes.

## 2. Provenance

| Role | Proven fact |
|---|---|
| Market data provider | `FirstRateData` |
| Benchmark decision provider | UNRESOLVED; no benchmark source is present or documented |
| Same provider | UNRESOLVED |
| Original market dataset | `data/market/raw/SPY_1min_firstratedata.csv`; SHA256 `B8688041F151AA291FC297205DC57539A4B2430B78FEA277566A0238EEE037CB` |
| Normalized causal dataset | `data/market/normalized/SPY_1min_normalized_v0_1.csv`; SHA256 `73957227A0CC09103F7CA5FF62B011EDD7C80C220017D91FB97C5FB6A1055D` |

The original FirstRateData source schema is exactly `timestamp`, `open`, `high`, `low`, `close`, and `volume`. It contains no benchmark decision field. The normalized 22-field schema also contains no BUY/SELL/HOLD-equivalent, decision, recommendation, target, or label field.

## 3. Decision-like artifacts distinguished

Repository search found `compute_decision_label` in `run_exp001b_compliance_pack.py`. Its domain is `EVIDENCE OF FORWARD VALUE`, `ISOLATED ADVANTAGE`, and `NO EVIDENCE`. This is an experiment-level evidence classification generated from experiment summaries. It is not a per-observation vendor trading decision, is not aligned to source timestamps, and is not eligible as the requested benchmark.

The prior Stage 2 isolation audit used synthetic poison columns named `decision`, `buy_sell_hold`, `target`, `future_return`, and `label`. Those fields were fabricated only to prove exclusion. They are not evidence that supplied benchmark columns exist.

## 4. Unresolved benchmark contract

| Required property | Status | Required external evidence |
|---|---|---|
| Original benchmark dataset identity/hash | OPEN | supplied benchmark manifest or file metadata |
| Benchmark provider | OPEN | provenance statement |
| Exact field name/type/nullability | OPEN | source schema |
| Complete literal domain | OPEN | documented domain or development-only distinct literals |
| Meaning of each literal | OPEN | vendor/source semantic specification |
| Semantic class | OPEN | position state, action, recommendation, transition, or other |
| D03 comparison field | OPEN | resolvable only after semantic class |
| Normalization mapping | OPEN | resolvable only after literal meanings |
| Entity alignment | OPEN | benchmark entity field and identity rules |
| Temporal/window alignment | OPEN | benchmark timestamp/window semantics |
| Missing/null policy | OPEN | source null contract |
| Duplicate policy | OPEN | benchmark key/cardinality contract |

## 5. Prohibited assumptions

No mapping such as `BUY -> LONG`, `SELL -> SHORT`, or `HOLD -> FLAT` is authorized. No D03 comparison field is selected. Same-row, nearest-time, interval-open, interval-close, and future-horizon alignment are all unauthorized until source semantics are supplied. Unknown values would be `UNMAPPABLE`, but the source domain itself remains unresolved.

## 6. Model-use boundary

Any future benchmark field is prohibited from D01, D02, D04, D03 DecisionContext, D03 policy, and Phase-A run control. It may be released only after immutable D03 commitment under a separately frozen harness contract.

## 7. Reserve isolation

No development rows or reserve rows were opened. No benchmark literals, frequencies, timestamps, alignment samples, APTF outputs, match rates, profitability, or reserve statistics were inspected or calculated.

## 8. Evidence

- `data/market/manifests/SPY_RAW_SOURCE_MANIFEST_V0_1.json`
- `data/market/manifests/SPY_NORMALIZED_MANIFEST_V0_1.json`
- `data/market/reports/SPY_NORMALIZATION_SPEC_V0_1.md`
- `D01_STAGE_2_DATA_PARTITION_MANIFEST.json`
- `D01_STAGE_2_INPUT_MAPPING_SPEC_V0_2.md`
- `d01_adaptive_parametric_model/output/d01_stage2_input_isolation_audit/reports/D01_STAGE_2_PRE_EXECUTION_INPUT_ISOLATION_AUDIT.md`
- `d01_adaptive_parametric_model/output/d01_stage2_input_isolation_audit/diagnostics/stage2_input_isolation_test_results.json`

## 9. Conclusion

**BENCHMARK METADATA CONTRACT: INCOMPLETE.**

Harness design cannot resume until a distinct benchmark source contract or development-partition benchmark file is supplied with schema and semantics. The sealed reserve must not be used to discover those facts.

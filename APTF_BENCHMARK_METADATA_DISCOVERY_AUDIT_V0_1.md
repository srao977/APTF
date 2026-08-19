# APTF Benchmark Metadata Discovery Audit v0.1

## Scope

Metadata-only discovery was performed to locate a per-observation benchmark decision contract. No development or reserve data row was opened.

## Files and metadata inspected

- D03 implementation freeze, implementation manifest, and referenced authority hashes
- `data/market/prepare_spy_firstratedata.py`
- raw and normalized market-data manifests
- normalization and input-mapping specifications
- partition and reserve-governance manifests/documents
- D01 observation/state contracts
- repository filename and text indexes, including ignored generated documentation
- Stage 2 input-isolation audit report, manifest, and synthetic test-result metadata
- the source of `compute_decision_label` solely to classify that identifier as experiment-level evidence rather than a trading benchmark

## Operations performed

- SHA256 verification of frozen D03 and upstream authorities
- repository filename searches for decision/benchmark data files
- text searches for benchmark, decision, label, recommendation, action, target, BUY, SELL, and HOLD terminology
- schema comparison using already documented column lists
- provenance classification of FirstRateData and experiment-generated decision terminology

## Data operations not performed

- development-partition rows read: NO
- reserve rows read: NO
- distinct benchmark-value query: NO; no benchmark field/file was found
- benchmark class counts: NO
- APTF component execution: NO
- D03 comparison: NO
- match rate or accuracy: NO
- correlation or predictive analysis: NO
- model fitting or tuning: NO
- parameter or policy change: NO
- profitability calculation: NO
- replay or backtest: NO

## Findings

The available original FirstRateData source is six-column OHLCV and has no benchmark decision field. The normalized dataset similarly has no decision-like field. No separate benchmark dataset exists in the workspace. Synthetic poison columns in prior audits are not source labels. The experiment-level `decision_label` is not a timestamped trading decision.

## Governance result

First six-month development data accessed for metadata: NO. Final six-month reserve accessed: NO. Frozen components modified: NO.

## Status

Metadata discovery is complete for the evidence currently available, but the benchmark contract remains incomplete because the benchmark source itself is absent or undocumented.

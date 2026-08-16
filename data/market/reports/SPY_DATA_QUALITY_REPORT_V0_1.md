# SPY Data Quality Report v0.1

## Row-level validity
- Valid rows: 207824
- Invalid rows: 0

## Duplicate analysis
- Duplicate timestamps: 0
- Conflicting duplicate timestamps: 0

## Timestamp anomalies
- Count: 0

## OHLC anomalies
- Count: 0

## Volume anomalies
- Negative volume rows: 0
- Zero volume rows: 0

## Irregular intervals
- See diagnostics/missing_interval_summary.csv

## Session completeness
- Distinct dates: 251
- Daily distribution: diagnostics/daily_summary.csv

## Potential concerns for D01
- Missing bid/ask fields require mapping strategy.
- Irregular intervals preserved intentionally for dt-aware replay.

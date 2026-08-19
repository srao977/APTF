# APTF 100-Row D03 Fixed-Context Causality Audit V0.1

Status: EXPERIMENTAL / DIAGNOSTIC. NOT FROZEN PRODUCTION AUTHORITY.

## Scope

The 100-row cycle was not executed because the two-row D03 gate failed. This artifact records the causality evidence for the permitted two-row D01-D04 execution and why no broader causality claim is made.

## Two-row source discipline

- Source interface: iterator-based `csv.DictReader`.
- Rows presented sequentially: YES.
- Last row read: `2022-09-30T08:17:00Z`.
- Later rows read before target commitment: NO.
- Full dataset materialized as a list/DataFrame: NO.
- Negative indexing: NO.
- Centered window: NO.
- Forward fill: NO.
- Future-return calculation: NO.
- Future OHLC access: NO.
- Future labels: NO.
- Future desired position/action verb: NO.
- Full-dataset statistic used by D01-D04: NO.

D01 maintained only prior causal runtime state. D02 was a pure function of the current D01 pair. D04 maintained prior envelope/hysteresis/aperture state and consumed only the current ReturnShape/context.

## Fixed-context behavior

The 11 fixed fields were read from one immutable JSON object and passed unchanged to each of the 18 permitted observations. `evaluation_time` and `data_integrity` were intentionally row-derived and are not fixed invariance candidates.

All fixed fields were `1.0` except `market_eligible=true`. No fixed field was derived from future market data.

## Status

Two-row D01-D04 causality: **PASS**.

Two-row full D03 causality: **NOT ESTABLISHED**, because D03 did not execute.

100-row causality: **NOT EXECUTED / NOT ASSESSED**.

# D01 Stage 2 Scoring Specification v0.2

**AUTHORITATIVE SOURCE:**  
`D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`

**IN CASE OF CONFLICT, THE FROZEN DESIGN V0.2 CONTROLS.**

This document is a canonical implementation-facing extract of approved Design v0.2. It does not create independent scientific authority.

## 13. Fixed Diagnostic Horizons

Pre-registered fixed elapsed-time horizons:

```text
1, 5, 15, 30, 60 minutes
```

They are evaluation projections, not D01 ontology. Lookup uses timestamps, never row counts. The first observation at or after target is used, with requested/actual elapsed time and overshoot recorded. Gap-crossing results carry their transition stratum.

## 14. Adaptive Temporal Horizons

Evaluate `0.5x`, `1.0x`, and `2.0x` each emitted:

- observation half-life;
- forward half-life;
- forward interval.

Coordinates are frozen at DMO emission. They are not updated by later D01 states. No opportunistic clipping is permitted; unavailable coordinates are censored. The maximum possible requested coordinate is 1,800 minutes.

## 15. Session and Gap Stratification

All observations remain in one trajectory. Classify each transition, in priority order:

1. `WEEKEND_OR_HOLIDAY_GAP`: local date difference at least two days;
2. `OVERNIGHT_GAP`: local date advances exactly one day;
3. `SESSION_TRANSITION`: same date, session label changes;
4. `DATA_GAP/IRREGULAR_INTERVAL`: same date/session, elapsed time greater than 60 seconds;
5. `INTRASESSION_CONTINUOUS`: same date/session, elapsed time in `(0,60]` seconds;
6. `START`: first observation.

UTC controls ordering; America/New_York controls local date/session labels. Strata affect analysis only, never frozen D01 input or state.

## 16. Right-Censoring Policy

No scorer may load an observation at or after reserve start `2023-03-30T04:00:00-04:00`.

- Censor each requested horizon independently if target/endpoint reaches the boundary.
- Preserve shorter available horizons.
- Right-censor survival at the last primary observation when no invalidation is observed.
- Interval-censor invalidation across gaps.
- Never treat censoring as semantic failure.
- Never shorten a requested horizon to manufacture a score.

The boundary guard executes before value access.

## 17. Calibration and Ordered Evidence

Continuous effects are primary: rank association, concordance/survival ordering, class contrasts, calibration curves, path errors, and monotonicity.

Secondary ordered summaries use predictor-only empirical quintiles. Outcomes never define bin edges. For half-life and other concentrated bounded variables, exact floor/ceiling masses are separate; interior values use up to five quantiles. If ties prevent five distinct groups, use fewer and report the reduction. Perturbation class uses native categories.

## 18. Minimum Support Policy

Support is the number of distinct populated 1,800-minute chronological blocks contributing to an estimate/class/bin:

```text
ADEQUATE:     >= 30 blocks
LIMITED:      10-29 blocks
INSUFFICIENT: < 10 blocks
```

Insufficient support forces `INCONCLUSIVE`; rarity alone is not failure. Limited support cannot yield `EMPIRICALLY_SUPPORTED`, but may yield `PARTIALLY_SUPPORTED`.

## 19. Serial-Dependence / Uncertainty Policy

Naive IID standard errors are prohibited. Use a chronological moving-block bootstrap with 1,800 elapsed-minute blocks, derived from the maximum requested adaptive horizon. Preserve all overlapping anchors/horizons inside blocks.

Use 2,000 deterministic replicates and two-sided 95% percentile intervals. Derive the seed from SHA256 of the eventual Stage 2 design-freeze identity. Report block count, replicate failures, interval type, and overlap policy.

## 20. Multiplicity Policy

Each semantic dimension has one primary pre-registered effect/contrast; horizon and stratum results are secondary diagnostics. Report effect direction/magnitude, 95% block interval, support, calibration, monotonicity, and horizon consistency.

P-values are optional and do not define classifications. If produced, apply Benjamini-Hochberg FDR at `q=0.05` across the ten primary dimension tests as one family. Unadjusted significance claims are prohibited.

## 21. Stage 2 Classification Rules

- `EMPIRICALLY_SUPPORTED`: adequate support; expected primary direction; 95% interval excludes null in that direction; no pre-registered primary contradiction.
- `PARTIALLY_SUPPORTED`: expected point direction with interval including null, limited support, or mixed subclaims without decisive opposite evidence.
- `UNSUPPORTED`: adequate support and interval excludes null opposite the expected direction, or a categorical primary contrast is decisively opposite.
- `INCONCLUSIVE`: insufficient support, invalid/censored observable, or inability to interpret the evidence.

No global PASS is generated from dimension counts or p-values. Stage 2 is allowed to fail.
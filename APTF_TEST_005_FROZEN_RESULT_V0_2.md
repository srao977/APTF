# APTF Test 005 Frozen D04 100-Minute Empirical Result V0.2

Run ID: `TEST005_FROZEN_D04_V0_2_RUN_001`  
Freeze ID: `D04_FOUR_FACTOR_POST_TEST004R_FREEZE_V0_1`  
Freeze manifest SHA-256: `a437cdb63bc7fe4aecdeece8ebd01082a62753774ad9ff7d93ee900eee3e4b79`  
Source data SHA-256: `73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d`  
Execution timestamp: `2026-08-18T21:54:17.859037Z`

## Status

**RESULT E — TEST INVALID DUE TO SOURCE-CONTINUITY AND EVIDENCE FAILURE.**

The runtime reached the `TEST005 100/100` checkpoint after processing physical rows 15–114, but then correctly rejected the run before serializing the trace because the source timestamps were not 100 consecutive one-minute observations. Twelve adjacent source intervals were 120–240 seconds rather than 60 seconds.

The failure occurred after records had been collected in memory but before the output write. The process terminated, so the complete 100-record trace is unavailable. It was not reconstructed, regenerated, or fabricated, and the pipeline was not rerun.

## Frozen Authority

- Pre-execution authority: 17/17 PASS.
- Post-execution authority: 17/17 PASS.
- Test 004R evidence pre/post: 8/8 PASS.
- Freeze artifacts: 5/5 unchanged.
- Frozen equation: `C = H * Q_G * Q_S * Q_R`.
- `data_integrity`: absent.
- G: absent.
- Thresholds/persistence: `0.75/0.55`, `3/2`.

## Source Scope And Failure

- Runtime target rows processed: 15–114.
- Runtime observations processed: 100.
- Row 115 processed: NO.
- First timestamp: `2022-09-30T08:13:00Z`.
- Last timestamp: `2022-09-30T10:15:00Z`.
- Non-60-second adjacent intervals: 12.
- Source SHA-256 pre/post: identical.

Gap details are recorded in `APTF_TEST_005_FROZEN_SOURCE_VARIATION_ANALYSIS_V0_2.json`.

## Evidence Boundary

Ten console checkpoints are preserved in the failure trace only as non-authoritative audit history. They show that the runtime reached cycle 100 and that checkpoint C values ranged within a running minimum `0.02642361014377076` and running maximum `0.5577135990257739`. These checkpoints are not a substitute for the missing 100-record series and must not be used to calculate distributions, state counts, factor counts, correlations, or a Result A-D classification.

The harness asserted four-factor reconstruction error `0.0` for each observation before adding it to memory and reached cycle 100 without a reconstruction exception. Nevertheless, the per-cycle proof rows were not serialized, so the complete reconstruction artifact is classified unavailable rather than recreated.

## Empirical Outputs

The following are unavailable because complete evidence was not persisted:

- C distribution, percentiles, bands, top/bottom 10, and actual joint maximum;
- factor distributions, bottleneck counts, and factor associations;
- threshold-proximity counts and runs;
- complete D04/D03/controller state and decision counts;
- volume/price variation and source/C associations;
- complete temporal lineage and direct/component timing series.

No threshold recommendation, backward solving, counterfactual combination, or scientific inference is made from partial checkpoints.

## Semantic Classification

- D04: **INCONCLUSIVE RESULT E**. No first non-CLOSED notice appeared and all ten checkpoints were CLOSED, but complete evidence is unavailable.
- D03: **INCONCLUSIVE RESULT E**. No first non-FLAT notice appeared and all ten checkpoints were FLAT, but complete evidence is unavailable.
- Position Controller: **INCONCLUSIVE RESULT E**. No first non-NO_ACTION notice appeared and all ten checkpoints were NO_ACTION, but complete evidence is unavailable.

## Acceptance Gates

Passed: **72/115**.

Failed gates:

- `G030`: row-15 initial state fingerprint was computed in memory but not persisted.
- `G043–G050`: complete source/D01/D02/factor/C records were not persisted.
- `G053–G060`: complete D04/D03/controller/temporal/timing records were not persisted.
- `G061–G086`: required distributions, runs, states, decisions, source analyses, perturbations, and associations could not be calculated from complete evidence.

All other gates pass, including frozen/source/historical immutability, execution through cycle 100, no row 115, no tuning or architecture changes, Result E selection, separate inconclusive semantic reporting, and post-execution authority identity.

## Scientific Findings

The requested empirical questions cannot be answered validly from this run. In particular, this evidence does not establish the actual 100-observation C maximum, threshold proximity, sustained high-C behavior, complete D04/D03/controller outcomes, lowest factor frequency, or source-response associations.

The only valid scientific conclusion is that physical rows 15–114 do not satisfy the specified uniformly consecutive one-minute timestamp contract: 12 source gaps exist. Whether such gaps are acceptable market-data behavior or require a different future test contract is a separate human decision. This run does not alter that contract.

## Non-Drift

- Frozen D04 authority: unchanged 17/17.
- Source: unchanged.
- Test 004: unchanged.
- Test 004A: unchanged.
- Test 004R: unchanged 8/8.
- Freeze artifacts: unchanged 5/5.
- No D01, D02, D04, D03, Position Controller, temporal, threshold, persistence, or test-script change occurred during execution.

## Next Action

**STOP.** Do not rerun automatically. Do not change D04 or thresholds. Return the RESULT E evidence for human review of the source-continuity requirement and evidence-write failure mode.
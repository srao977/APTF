# APTF Test 002A Volume Differential Audit Plan V0.1

Status: EXECUTED READ-ONLY EVIDENCE ANALYSIS
Date: 2026-08-18

## Scope

Analyze only the already-captured Test 002 evidence for t1 physical row 10 and t2 physical row 11. Read frozen source/design authority only to identify formulas and branches. Perform arithmetic reconstruction from stored values. Do not execute the pipeline, read market CSV rows, construct observations, run counterfactuals, tune parameters, or modify frozen/Test 001/Test 002 evidence.

## Evidence

Primary evidence is the seven `APTF_TEST_002_*_V0_1` artifacts. Test 001 evidence is used only for protected-hash verification. Frozen D01/D02/D04/D03/controller source is read, not imported or executed.

Pre-audit verification:

- Bound mathematical/temporal/semantic/Test 001 references: 67/67 PASS.
- Test 002 evidence files recorded: 7.
- Quoted t1/t2 source, D02, D04, D03, and controller values: PASS, no discrepancies.
- D01 after t1 equals D01 before t2: PASS.
- D04 after t1 equals D04 before t2: PASS.
- Unauthorized reset: NO.

## Method

1. Compare complete stored source values and actual D01 inputs.
2. Trace `source.volume -> NormalizedObservation.volume -> update_volume_influence` in frozen code.
3. Reconstruct volume reference, influence, coherence, and strength arithmetically.
4. Compare canonical D01 outputs and exact DMO/FMO fields accepted by D02.
5. Map D01 fields through the pure ReturnShape builder and separate continuous geometry from sign category.
6. Reconstruct D04 geometry, structural quality, risk quality, base score, feasibility gate, hard eligibility, final capturability, aperture update, and hysteresis gate.
7. Trace complete D04 output into D03's ordered target rules.
8. Identify the earliest decisive categorical boundary while preserving evidence that continuous differences remain in the D04 payload.
9. Re-hash all protected and Test 002 evidence.

## Causal Attribution Rule

A code dependency is evidence that volume enters a calculation. It is not evidence that the observed t1-to-t2 output delta was caused by volume alone. Because close, kinematics, perturbation class, prior state, and other recursive inputs also changed, exact isolated volume sensitivity is reported as not identifiable from stored observational evidence. No counterfactual is performed.

## Artifact Status

All Test 002A files are diagnostic evidence only. They create no mathematical or semantic authority and no freeze.

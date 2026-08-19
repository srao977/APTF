# APTF Test 003A D04 Reachability Audit Plan V0.1

Status: EXECUTED READ-ONLY MATHEMATICAL AUDIT
Date: 2026-08-18

## Scope

Use frozen D01/D02/D04/D03 source/design plus existing Test 002A and Test 003 evidence. Perform symbolic and arithmetic analysis only. Do not run the pipeline, read market data, construct synthetic observations, run counterfactuals, tune parameters/thresholds, or modify protected evidence.

## Preconditions

- Bound frozen mathematical/temporal/semantic/Test 001 authorities: 67/67 PASS.
- Test 002, Test 002A, and Test 003 files recorded: 24.
- Threshold 0.75 and all five Test 003 scores/states/candidates/R31/FLAT/NO_ACTION outcomes verified with no discrepancy.
- Observed C range: `[0.08848558708732783, 0.28034113293008417]`; threshold gap from observed max: `0.46965886706991583`.

## Method

1. Transcribe exact implementation expression and frozen design formula.
2. Trace all D02/D01/context/configuration dependencies and hard bounds.
3. Separate algebraic bound, schema-valid D04 witness, D04 state-machine reachability, and end-to-end D01-driven reachability.
4. Derive the exact inequality region for `C >= 0.75` and local sensitivities.
5. Reconstruct all five stored C values arithmetically.
6. Audit multiplication, additive penalties, clamps, normalization, dependency coupling, sign, scale, threshold provenance, hysteresis, candidate creation, and D03 compression.
7. Compare design and implementation mechanically.
8. Select exactly one finding A-E without proposing any correction.
9. Re-hash all protected/prior-test evidence.

## Classification Rule

A schema-valid D04 witness proves algebraic/D04-local reachability but does not prove that frozen D01 coupled state dynamics can generate that simultaneous tuple. Unless an end-to-end witness or proof exists, `REACHABLE MAXIMUM NOT ESTABLISHED` is required.

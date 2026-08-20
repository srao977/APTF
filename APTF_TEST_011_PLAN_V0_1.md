# APTF Test 011 RK45 Adaptive Price Trajectory Control Plan V0.1

## Purpose

Validate frozen Test 010 local Price dynamics by one-minute causal RK45 propagation while preserving the independent discrete Volume observer and dual-engine Control boundary. No Runtime/Emitter/Position change, trading/P&L selection, multi-minute projection, gap integration, color threshold, AutoPilot, or broker is permitted.

## Ordered procedure

1. Verify Runtime Core, Test 009, Test 009V, Test 010, and historical hashes.
2. Freeze RK tolerances, component atols, convergence sample, event functions, perturbations, eligibility precedence, and derivative-state rules before solver execution.
3. Run a deterministic tolerance study over 1,024 evenly spaced eligible Test 010 emissions; select tolerance numerically only.
4. Stream every actionable observation. Emit exactly one ineligible record or one one-minute RK45 projection. Freeze each emission's F_P parameters throughout that solve.
5. Persist projection/audit fields before reading actual next-state fields in the scoring phase.
6. Score P/P1/P2, signs, states, upper/lower crossings, and compare against Test 010 on the identical eligible set.
7. Copy the frozen discrete Volume observer only; never call an ODE solver for Volume.
8. Create independent-engine Control, gap, condition, cockpit-readiness, and next-test evidence.
9. Recompute every frozen hash and stop.

## Eligibility precedence

For each actionable observation:

1. `NO_NEXT_OBSERVATION` if final source row.
2. `NO_PRICE_MODEL` if no Test 010 Price emission exists.
3. `INVALID_STATE` or `INVALID_F_P` for nonfinite/malformed authority.
4. `SESSION_BOUNDARY` for Test 010 session-transition/overnight/weekend strata.
5. `TIME_GAP` for same-session elapsed time not exactly one minute.
6. otherwise RK eligible only for `INTRASESSION_CONTINUOUS` and exactly 1.0 elapsed minute.

Every actionable row appears exactly once in eligible or ineligible evidence.

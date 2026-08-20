# APTF Test 011 Next-Test Recommendation V0.1

## Recommendation

Do **not** proceed directly to cockpit color envelopes, longer RK horizons, or control-to-execution mapping.

The next authorized experiment should be:

```text
LOCAL PRICE DYNAMICS STABILIZATION AND RK-COMPATIBILITY AUDIT
```

## Evidence

- RK45 tolerance convergence passed and therefore does not explain the error.
- RK45 was worse than the frozen Test 010 one-step approximation for P, P1, and P2.
- P2 MAE increased from 0.00195209 to 0.04838932 on identical observations.
- Six projections were numerically unstable.
- P2 perturbation amplification median/p95/max was approximately 7.38/31.69/907.96.
- Upper/lower transition recall was 0.1800/0.1692.
- Price movement sign accuracy was 0.4647.

## Candidate questions for the next test

1. Is the endpoint-fitted affine F_P valid away from the endpoint state during RK stages?
2. Would state-variable reparameterization, bounded local domains, or a model defined directly in derivative coordinates improve Lipschitz/local stability?
3. Can a model be selected using conditioning plus perturbation amplification, rather than one-step endpoint error alone?
4. Is constant-jerk Test 010 approximation the appropriate one-minute propagator while F_P remains unsuitable for continuous evaluation?

Any new model family or selection rule requires a separate predeclared experiment and must not modify frozen Test 010/Test 011 evidence.

Test 012 started: **NO**
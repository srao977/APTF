# D03 Feed / Replay Equivalence Review v0.1

## Verdict

**PASS. Full committed-record equivalence is design-complete.**

## Invariant

```text
D03(D04Evaluation_t, DecisionContext_t, frozen policy/version) = D03Decision_t
```

The result is independent of whether inputs arrive through future market-feed transport or causal replay transport.

## Complete-output proof

For all 7,680 valid committed-policy classes, repeated evaluation produced identical values for all 21 fields, including desired state, transition intent, authorization, target-primary reason, ordered supporting reasons, canonical decision rule ID, candidate lineage, fingerprints, and decision identity.

The validator found:

- complete output coverage: PASS;
- reason divergence: 0;
- candidate-lineage ambiguity: 0;
- T00 divergence: 0;
- uncovered classes: 0.

## Transport separation

- replay-specific rules: 0;
- feed-specific rules: 0;
- transport/source flag in input: none;
- scheduler or 15-minute dependency: none;
- hidden mutable D03 state: none;
- stochastic/adaptive branch: none;
- future/outcome branch: none.

Signals may continue until their source stops. D03 evaluates causal D04 and DecisionContext changes without being characterized as hard real-time or tied to historical batch boundaries.

# D04 Directional Provenance Non-Drift Audit v0.2.1

## Result

**PASS.** The sole executable semantic delta is immutable propagation of `ReturnShape.path_direction` into CandidateEnvelope.

## Upstream immutability

- D01 modified: NO.
- D02 modified: NO.
- D02 design freeze remains `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`.
- D02 implementation freeze remains `C8029C4B9608547BBF7960F05E4F8613480C4FB2BF8594D94482516B954F7E72`.

## Mathematical non-drift

The v0.2 manifest hashes remain unchanged for `capturability_model.py`, `aperture_model.py`, and `hysteresis.py`. Focused UPWARD/DOWNWARD equality testing proves direction propagation does not enter CapturabilityResult.

| Component | Result |
|---|---|
| Q_G | UNCHANGED |
| Q_S | UNCHANGED |
| Q_R | UNCHANGED |
| B | UNCHANGED |
| G | UNCHANGED |
| H | UNCHANGED |
| C | UNCHANGED |
| Aperture | UNCHANGED |
| Hysteresis | UNCHANGED |

All 14 frozen formula vectors pass.

## Lifecycle/control non-drift

- Envelope state ontology and transition mapping: unchanged.
- Candidate qualification condition: unchanged.
- Candidate identity function and outputs: unchanged.
- Supersession timing/invalidations: unchanged; replacement now carries its own source direction.
- Stale and safety closure: unchanged; invalidated copy preserves direction.
- Recovery: unchanged; newly qualified candidate uses new source direction.
- D04Context and 23 top-level D04Evaluation fields: unchanged.
- Scenarios and event ontology: unchanged.

Candidate model immutability makes provenance stability explicit. Existing status invalidation already used copy-on-write, so no lifecycle algorithm changed.

## Tests

- focused directional provenance: 10/10;
- complete D04: 79/79;
- modernization: 46/46;
- frozen formula vectors: 14/14;
- D02: 26/26;
- D01 v0.2: 50/50.

No historical data, reserve, outcome, P&L, replay, backtest, learning, fitting, or calibration was used.

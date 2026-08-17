# D04 Capturability Implementation Non-Drift Audit v0.2

## Result

PASS. The executable mathematics matches the frozen deterministic formula.

| Quantity | Frozen formula | Executable implementation |
|---|---|---|
| `Q_G` | `0 if M == 0 else abs(D)/M` | exact zero branch, otherwise exact ratio |
| `Q_S` | `(strength*coherence*persistence)^(1/3)` | unweighted geometric mean |
| `Q_R` | `sqrt((1-uncertainty)*(1-reversal_propensity))` | exact complement product root |
| `B` | `Q_G*Q_S*Q_R` | exact product |
| `G` | minimum of ten frozen dimensions | exact `min` in frozen diagnostic order |
| `H` | valid projection, market eligible, integrity above critical, valid input | integer zero or one |
| `C` | `H*B*G` | exact product |

No weights, fitted coefficients, nonlinear calibration, score clipping, temporal penalty, state-support duplication, or candidate feedback enters the formula.

## Invalid and boundary behavior

- `M=0,D=0` produces zero geometry without division.
- `abs(D)>M`, inconsistent terminal/maximum path summaries, or inconsistent direction raises `INVALID_RETURNSHAPE` in direct mathematical evaluation.
- Envelope orchestration catches that exact condition and fails closed with zero capturability and canonical safety facts.
- Projection endpoint is inclusive; staleness begins strictly afterward.
- Data integrity at the critical threshold is invalid because the frozen rule is strictly above threshold.

## Executable evidence

- All 14 frozen vectors from `D04_CAPTURABILITY_DETERMINISTIC_TEST_VECTORS_V0_2.json`: PASS.
- All ten gate dimensions independently bind the minimum gate: PASS.
- Formula branch and component tests: PASS.
- Focused modernization suite: 46 passed.
- Complete D04 suite: 69 passed.

No reserve, market history, replay, outcome, or P&L data was used.

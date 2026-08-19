# APTF D04 Capturability C Definition V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Authority

The controlling semantic statement is in `D04_CAPTURABILITY_DETERMINISTIC_DESIGN_V0_2.md`, section 3:

> Capturability is the present realizability of a supplied ReturnShape under the active causal envelope.

The same authority explicitly says it is not market prediction, expected return, profit probability, attractiveness, or a trade recommendation.

## Exact definition

- Symbol: $C_i(t)$.
- Runtime field: `EnvelopeEvaluation.capturability_score`.
- Implementation: `aptf_d04.envelope.capturability_model.CapturabilityModelV0_2.evaluate`.
- Runtime result type: `aptf_d04.models.capturability.CapturabilityResult`.
- Inputs: canonical D02 `ReturnShape` plus D04 `EnvelopeContext`.
- Domain: $[0,1]$.

$$
C=HBG
$$

where:

$$
B=Q_GQ_SQ_R
$$

$$
Q_G=\begin{cases}0,&M=0\\|D|/M,&M>0\end{cases}
$$

$$
Q_S=(scp)^{1/3}
$$

$$
Q_R=\sqrt{(1-u)(1-r)}
$$

$$
G=\min(g_1,\ldots,g_{10})
$$

$$
H=\mathbf{1}[\text{projection valid}]\mathbf{1}[\text{market eligible}]\mathbf{1}[\text{data integrity}>0.2]\mathbf{1}[\text{valid finite inputs}]
$$

Terms: $D$ terminal displacement, $M$ maximum absolute displacement, $s$ strength, $c$ coherence, $p$ persistence, $u$ uncertainty, and $r$ reversal propensity.

The ten $G$ dimensions are liquidity, spread, latency, execution feasibility, capital, portfolio, position, risk, broker health, and data integrity.

## Consumers

`TradingEnvelope.process` supplies $C$ to `HysteresisController.next_state`. Frozen thresholds are:

- `open_threshold=0.75`
- `close_threshold=0.55`
- `open_persistence_observations=3`
- `close_persistence_observations=2`

`ApertureModelV0.update` separately smooths $C$ after hysteresis. Candidate creation occurs only when the post-hysteresis state is OPEN and no current candidate exists.

## Supported semantic labels

| Interpretation | Supported? | Evidence |
|---|---|---|
| Probability | NO | Authority explicitly rejects probability claims |
| Confidence | NO | No calibration/confidence definition |
| Bounded score | YES | Runtime field and range `[0,1]` |
| Quality | Component-specific only | $Q_G$, $Q_S$, and $Q_R$ are quality transforms; $C$ is capturability |
| Capturability / present realizability | YES | Exact authority definition |
| Expected return | NO | Explicitly rejected |
| Directional strength | NO | Direction sign does not enter $C$ |
| Opportunity strength | NO | Generic attractiveness explicitly rejected |
| Execution quality | PARTIAL INPUT | Execution-related dimensions enter $G$; $C$ is broader than execution quality |
| Feasibility | PARTIAL INPUT | $G$ is feasibility bottleneck inside $C$ |
| Risk | NO as a standalone semantic | Reversal/uncertainty quality and risk capacity contribute, but $C$ is not “risk” |
| Trade recommendation | NO | Explicitly rejected |

## Plain-English meaning

$C$ is a bounded present-realizability score for a supplied projected path. It combines analytical path geometry/structure/degradation with hard validity and current external feasibility. It says neither which direction the path points nor which position/order should be chosen.

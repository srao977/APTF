# D01 Stage 2 Scoring Clarification Addendum v0.2.1

## 1. Document Status and Scope

**Status:** SCORING CLARIFICATION ADDENDUM - FREEZE CANDIDATE  
**Parent authority:** `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`  
**Parent freeze:** `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2_FREEZE.json`  
**Purpose:** resolve only the scoring ambiguities recorded in `D01_STAGE_2_IMPLEMENTATION_DESIGN_AMBIGUITY.md`.

This addendum supplements and does not replace frozen Stage 2 Design v0.2. It does not modify D01, the data partition, input mapping, realized-state geometry, warm-up, session/gap policy, fixed/adaptive horizon sets, support policy, block bootstrap, four-level classification philosophy, reserve policy, or causal replay protocol.

No primary historical outcomes or reserve observation values were inspected. All formulas are deterministic, transparent, unfitted, and fixed before Stage 2 execution.

## 2. Realized Ambiguity Index

At a scored anchor/horizon, use the already-frozen components:

- path efficiency $E\in[0,1]$;
- normalized path deviation $D\ge0$;
- ambiguous incidence $I_{amb}\in\{0,1\}$.

First bound deviation:

$$
D_{bounded}=\frac{D}{1+D}.
$$

Define the realized ambiguity index:

$$
A_{realized}=\frac{(1-E)+D_{bounded}+I_{amb}}{3}.
$$

Domain:

$$
A_{realized}\in[0,1].
$$

Larger values mean greater realized ambiguity. The three frozen components contribute equally; there are no learned weights or free parameters. The index is sign/mirror invariant because each component is sign/mirror invariant.

If any required component is unavailable at a scored horizon, $A_{realized}$ is unavailable and that anchor/horizon is excluded from the uncertainty primary score. It is not imputed and is not counted as failure.

## 3. Uncertainty Primary Score

The uncertainty primary statistic is:

$$
\rho_U=\operatorname{Spearman}(U_t,A_{realized}).
$$

Expected direction: $\rho_U>0$.  
Primary null: $\rho_U=0$.

No ambiguity threshold is fitted. The frozen 1,800-minute moving-block bootstrap supplies the 95% percentile interval and support rules.

## 4. State/Kinematics Primary Statistic

Let the frozen DMO directional claim be $d_t$ and the realized through-origin future slope at horizon $h$ be $b_t(h)$.

Define directional concordance encoding:

$$
c_t(h)=\operatorname{sign}(d_tb_t(h)),
$$

where `+1` is concordant, `-1` is discordant, and `0` is ambiguous because $d_t=0$ or $b_t(h)=0$.

Zero/ambiguous anchors are excluded from the directional primary denominator and reported separately.

For valid directional anchors:

$$
C_h=\operatorname{mean}\left(\mathbf{1}[d_tb_t(h)>0]\right).
$$

The single primary horizon is fixed at 15 elapsed minutes:

$$
C_{15}=\operatorname{mean}\left(\mathbf{1}[d_tb_t(15)>0]\right).
$$

Primary effect:

$$
\theta_{state}=C_{15}-0.5.
$$

Expected direction: $\theta_{state}>0$.  
Primary null: $\theta_{state}=0$.

Secondary diagnostics remain 1/5/30/60-minute concordance, acceleration/curvature mirror concordance, path efficiency, path deviation, and continuous signed progress. This is state-geometry evidence, not trading direction accuracy.

## 5. Realized Perturbation Transition Magnitude

At elapsed horizon $h$, using frozen raw-close geometry, define:

$$
M_{transition}(h)=\sqrt{y_t(h)^2+\left(hb_t(h)\right)^2}.
$$

$y_t(h)$ is dimensionless endpoint log displacement. $b_t(h)$ is through-origin slope per elapsed minute, so $hb_t(h)$ is dimensionless horizon-scale displacement. No weights are fitted.

The single primary horizon is 15 elapsed minutes:

$$
M_{transition,15}=M_{transition}(15).
$$

The perturbation-magnitude primary statistic is:

$$
\rho_Q=\operatorname{Spearman}(Q_t,M_{transition,15}).
$$

Expected direction: $\rho_Q>0$.  
Primary null: $\rho_Q=0$.

Secondary diagnostics may use 1/5/30/60-minute transition magnitude, maximum absolute realized displacement, slope change, and frozen gap/session strata.

Sign/mirror invariance is mandatory: replacing every directional quantity with its negative leaves $M_{transition}$ unchanged.

## 6. Perturbation-Class Co-Primary Contrasts

Do not combine class outcomes into a weighted scalar. Freeze two co-primary effects at 15 elapsed minutes.

### Contrast A: Reinforcing vs Contradicting

Outcome: weakening incidence by 15 minutes.

$$
p_R=P(WEAKENING\mid REINFORCING),
$$

$$
p_C=P(WEAKENING\mid CONTRADICTING),
$$

$$
\Delta_{RC}=p_C-p_R.
$$

Expected direction: $\Delta_{RC}>0$.  
Null: $\Delta_{RC}=0$.

### Contrast B: Reinforcing vs Reversing

Outcome: reversal incidence by 15 minutes.

$$
p_{Rrev}=P(REVERSAL\mid REINFORCING),
$$

$$
p_{Vrev}=P(REVERSAL\mid REVERSING),
$$

$$
\Delta_{RV}=p_{Vrev}-p_{Rrev}.
$$

Expected direction: $\Delta_{RV}>0$.  
Null: $\Delta_{RV}=0$.

The effects remain separate. Predictor class is frozen at anchor emission; realized weakening/reversal comes only from the independent raw-close observer.

## 7. Perturbation-Class Dimension Classification

Classify the perturbation-class dimension as follows:

- `EMPIRICALLY_SUPPORTED`: both co-primary contrasts have `ADEQUATE` support; both point estimates are positive; both 95% block-bootstrap intervals exclude zero in the positive direction.
- `PARTIALLY_SUPPORTED`: both point estimates are positive but one/both intervals include zero; or one/both have `LIMITED` support; or one contrast is expected and decisive while the other is inconclusive without decisive opposition.
- `UNSUPPORTED`: `ADEQUATE` support exists and either co-primary interval excludes zero in the negative direction.
- `INCONCLUSIVE`: either required contrast has `INSUFFICIENT` support or cannot be validly scored.

Secondary subclaims remain:

- `NONE`: lower immediate transition magnitude than material classes;
- `STRUCTURAL/UNKNOWN`: greater ambiguous/data-structural incidence.

Secondary subclaims do not override the co-primary classification. Any direct semantic contradiction is reported separately.

## 8. Primary 15-Minute Horizon

Fifteen elapsed minutes is the primary fixed horizon for:

- state/kinematics concordance;
- perturbation transition magnitude;
- perturbation-class incidence contrasts.

It was already pre-registered in the frozen 1/5/15/30/60 set, avoids a one-bar test, remains local relative to broader temporal scales, and is selected before outcome inspection. It must not change after the primary run.

## 9. Censor-Aware Concordance Representation

For each anchor, represent event duration as one of:

- exact event: $[L,U]$ with finite $L=U$;
- interval-censored event: $(L,U]$ with finite $L<U$;
- right-censored duration: $(L,\infty)$, where $L$ is the last known event-free duration.

Never assign a midpoint to an interval-censored event.

## 10. Comparable-Pair Policy

For two anchors $i,j$, duration ordering is usable only when mathematically certain.

1. Exact/right-censored Harrell case: an exact event at duration $T_i$ is known earlier than anchor $j$ when $T_i<L_j$, where $L_j$ is $j$'s exact event time, interval lower bound, or right-censor bound. The mirrored rule applies for $j$ earlier than $i$.
2. Interval-censored case: interval event $i$ is certainly earlier than anchor/event $j$ only when $U_i<L_j$. It is certainly later than an exact or interval event $j$ only when $U_j<L_i$. The same strict separation rule applies between two interval-censored events.
3. Overlapping or touching uncertain intervals are `NONCOMPARABLE`.
4. Two right-censored anchors are `NONCOMPARABLE` because neither event ordering is observed.
5. Exact event durations that are equal are duration ties and contribute `0.5` when included. Predictor ties contribute `0.5`.

For a comparable pair, score `1` when oriented predictor ordering agrees with certain duration ordering, `0` when it disagrees, and `0.5` on a predictor or exact-duration tie. Concordance $C$ is the mean pair score over comparable pairs. If there are no comparable pairs, $C$ is unavailable.

Record exact events, right-censored anchors, interval-censored anchors, comparable pairs, and noncomparable interval pairs.

## 11. Concordance Orientation and Null

For persistence, observation half-life, forward half-life, and forward interval, larger predictor means longer duration, so use the predictor directly.

For reversal propensity, larger predictor means shorter time-to-reversal, so orient with $-R_t$ against duration. Equivalent ordering logic is permitted only if it produces the same pair scores and is documented.

Primary statistic:

$$
C=\frac{\text{sum comparable-pair scores}}{\text{number of comparable pairs}}.
$$

Primary effect:

$$
\theta_C=C-0.5.
$$

Expected direction after orientation: $\theta_C>0$.  
Primary null: $\theta_C=0$.

The frozen 1,800-minute moving-block bootstrap resamples anchor records with predictor, censor type, event bounds, and block identity intact. It uses 2,000 replicates and a two-sided 95% percentile interval.

If interval censoring/noncomparability leaves insufficient frozen block support, classify the dimension `INCONCLUSIVE`. Do not use midpoints, convert interval censoring to right censoring, or substitute another estimator.

## 12. Explicit Primary Null Table

| Dimension/contrast | Primary effect | Null |
|---|---|---|
| State / kinematics | $C_{15}-0.5$ | `0` |
| Strength | Spearman $\rho$ | `0` |
| Coherence | Spearman $\rho$ | `0` |
| Persistence | censor-aware $C-0.5$ | `0` |
| Uncertainty | Spearman $\rho$ | `0` |
| Reversal propensity | oriented censor-aware $C-0.5$ | `0` |
| Perturbation magnitude | Spearman $\rho$ | `0` |
| Perturbation class contrast A | $\Delta_{RC}$ | `0` |
| Perturbation class contrast B | $\Delta_{RV}$ | `0` |
| Observation half-life | censor-aware $C-0.5$ | `0` |
| Forward half-life | censor-aware $C-0.5$ | `0` |
| Forward interval | censor-aware $C-0.5$ | `0` |

## 13. Unchanged Frozen Policies

Strength remains Spearman association between strength and $|b|E$. Coherence remains Spearman association between coherence and efficiency. Their null is $\rho=0$.

The following remain exactly as frozen in parent Design v0.2:

- fixed horizons 1/5/15/30/60 minutes;
- adaptive coordinates 0.5x/1.0x/2.0x observation half-life, forward half-life, and forward interval;
- support blocks of 1,800 elapsed minutes;
- `ADEQUATE >=30`, `LIMITED 10-29`, `INSUFFICIENT <10` blocks;
- chronological moving-block bootstrap, 1,800-minute blocks, 2,000 replicates, two-sided 95% percentile interval, deterministic seed from the Stage 2 freeze identity;
- four-level classification rules except for the explicit co-primary perturbation-class adjudication in Section 7;
- session/gap, censoring, reserve, causality, replay, and determinism policies.

## 14. Causality and Non-Execution Attestation

All clarified observables use only the already-frozen raw-close future geometry $y$, $b$, $E$, normalized deviation, realized category, and censor state after anchor DMO emission. No future D01 state enters a score.

- D01 modified: NO
- Parent Stage 2 Design v0.2 modified: NO
- Historical outcomes inspected: NO
- Reserve values inspected: NO
- Stage 2 implemented: NO
- Historical replay started: NO
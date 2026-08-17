# D04 Capturability Formula Specification v0.2

## 1. Domains

Frozen D02 fields:

- $D\in\mathbb R$: `terminal_displacement`;
- $M\in[0,\infty)$: `maximum_absolute_displacement`, with valid-contract invariant $|D|\le M$;
- $s,c,p,u,r\in[0,1]$: `strength`, `coherence`, `persistence`, `uncertainty`, `reversal_propensity`.

Typed D04Context:

- $g_1,\ldots,g_{10}\in[0,1]$: configured feasibility dimensions;
- $m\in\{0,1\}$: `market_eligible`;
- $d\in[0,1]$: `data_integrity`;
- $d_{crit}\in[0,1]$: existing configured critical integrity threshold;
- $t_{eval},t_{model}\in\mathbb R$: causal evaluation/model times;
- $I_f>0$: `projection_interval`.

## 2. Exact component formulas

Geometry quality:

$$
Q_G(D,M)=\begin{cases}
0,&M=0,\\
|D|/M,&M>0.
\end{cases}
$$

Structural quality:

$$
Q_S(s,c,p)=(s c p)^{1/3}.
$$

Risk quality:

$$
Q_R(u,r)=((1-u)(1-r))^{1/2}.
$$

Temporal quality: **OMITTED**. No temporal factor or placeholder component enters $B$.

Base capturability:

$$
B=Q_G Q_S Q_R.
$$

Feasibility gate:

$$
G=\min(g_1,\ldots,g_{10}).
$$

Projection validity:

$$
v=\mathbf 1[t_{eval}\le t_{model}+I_f].
$$

Hard eligibility:

$$
H=v\,m\,\mathbf 1[d>d_{crit}]\,\mathbf 1[\text{all required inputs valid and finite}].
$$

Final capturability:

$$
C=H B G.
$$

For $H=1$, $C=B G$.

## 3. Feasibility dimensions

In fixed existing order for diagnostics, not mathematics: `liquidity_quality`, `spread_quality`, `latency_quality`, `execution_feasibility`, `capital_available`, `portfolio_capacity`, `position_capacity`, `risk_capacity`, `broker_health`, `data_integrity`. Minimum is order-independent.

## 4. Excluded mathematical inputs

`state_support_ratio` is diagnostic only to avoid duplicate use of $s,p,u,r$. `terminal_decay_factor`, `forward_half_life`, and projected state paths are diagnostic/validation/lifecycle context and do not enter $B$. Absolute $M$ does not independently enter $B$ because no non-arbitrary scale exists; it appears only as denominator in the scale-free $Q_G$.

Identity/provenance/path fields not appearing above remain required for canonical validation and lineage but are not hidden score terms.

## 5. Zero and invalid rules

- If $M=0$, valid frozen D02 requires $D=0$; set $Q_G=0$ without division.
- If $M<0$, $|D|>M$, any required scalar is nonfinite/out of range, path is empty/inconsistent, or identity/time is invalid: status `INVALID_RETURNSHAPE`, $H=0$, $C=0$.
- A nonempty constant FMO has $D=M=0$ and therefore $B=C=0$.
- Defensive final clamp to `[0,1]` is permitted only for floating-point roundoff after validating analytic invariants.

## 6. Proof of bounds

For a valid shape, $0\le |D|\le M$ gives $Q_G\in[0,1]$. Products of `[0,1]` values followed by positive roots give $Q_S,Q_R\in[0,1]`. Therefore $B\in[0,1]$. Minimum of ten `[0,1]` values gives $G\in[0,1]$. Since $H\in\{0,1\}$, $C=HBG\in[0,1]$.

## 7. Monotonicity

Holding other values fixed, $B$ is non-decreasing in endpoint efficiency, strength, coherence, and persistence; non-increasing in uncertainty and reversal propensity. $C$ is non-decreasing in each gate dimension and zero under any hard exclusion.

## 8. No arbitrary design constants

Base formula constants are only root exponents implied by unweighted geometric means. There are no fitted weights, tunable slopes/scales, learned parameters, historical thresholds, or reserve-derived values. The existing critical data-integrity threshold and gate warning threshold are preserved D04 safety/diagnostic configuration, not fitted by this design.

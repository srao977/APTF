# D04 Capturability V0 to Deterministic v0.2 Mathematics Trace

## 1. Formula comparison

Old prototype:

$$
S_{old}=\sum w_k x_k,\quad E_{old}=\sum v_j c_j,\quad
L_{old}=\operatorname{clip}(\text{expected lifetime}/30),
$$

$$
B_{old}=\operatorname{clip}((0.5S_{old}+0.5E_{old})L_{old}),\quad
C_{old}=B_{old}\min(g_j).
$$

New deterministic design:

$$
Q_G=\begin{cases}0,&M=0\\|D|/M,&M>0\end{cases},\quad
Q_S=(s c p)^{1/3},\quad Q_R=\sqrt{(1-u)(1-r)},
$$

$$
B=Q_G Q_S Q_R,\quad G=\min(g_j),\quad C=HBG.
$$

## 2. Term trace

| Old term | Old semantic/role | New disposition | New quantity/formula | Reason |
|---|---|---|---|---|
| `shape_quality` | Weighted synthetic meta-score | Retired | No replacement; explicit coherence/structure/geometry | Avoid redundant arbitrary compression |
| `forward_support` | Weighted bounded support proxy | Retired from score | Natural `state_support_ratio` retained diagnostically | Explicit formula already uses its underlying dimensions; avoid double count |
| `magnitude_score` | Weighted normalized movement proxy | Retired | $Q_G=|D|/M$ with zero branch | Scale-free consistency; no arbitrary absolute scale |
| `persistence_score` | Weighted persistence | Semantic rename | $p$ inside $Q_S=(scp)^{1/3}$ | Preserve D01 coordinate without fitted weight |
| `uncertainty` | Inverted weighted term | Preserved semantic | $(1-u)$ inside $Q_R$ | Higher uncertainty cannot improve capture |
| `reversal_risk` | Inverted weighted risk | Corrected/renamed | $(1-r)$ where $r$ is reversal propensity | Preserve penalty without probability claim |
| `decay_score` | Inverted degradation proxy | Retired from score | Decay fields diagnostic; temporal softness omitted | Avoid FMO/lifecycle time double count |
| `expected_lifetime_seconds` | Soft ratio to 30 seconds and expiry proxy | Retired | Hard inclusive projection validity $H$ | Projection interval is extent, not expected lifetime |
| shape weights | Seven fitted-looking manual constants | Retired | Unweighted geometric means/product | Parameter-free semantic conjunction |
| envelope component | Weighted soft operational average | Retired | No soft context average | Operational qualities belong in preserved hard bottleneck gate |
| equal shape/envelope blend | Compensatory 0.5/0.5 sum | Retired | Hierarchical $B$ then $G$ | Poor feasibility cannot be compensated |
| feasibility gate | Minimum of ten causal dimensions | Preserved unchanged | $G=\min(g_1,\ldots,g_{10})$ | Existing realizability principle remains valid |
| aperture/hysteresis input | Bounded final capture | Preserved | $C\in[0,1]$ | Interfaces remain compatible |

## 3. Preserved intent

The new design preserves D04's realizability question, hard feasibility bottleneck, bounded output, deterministic transparency, aperture input, hysteresis input, safety precedence, and event-driven operation. It does not preserve numeric equivalence to provisional V0.

# D01 — Adaptive Parametric Model Design

**Document:** D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_2  
**Version:** 0.2  
**Status:** LOGICAL DESIGN / EXPERIMENTAL DESIGN BASELINE  
**Framework:** Adaptive Parametric Trading Framework (APTF) — Reference 1.1  
**Artifact:** D01 — Adaptive Parametric Model

---

## 1. Purpose

D01 is the continuously evolving mathematical intelligence core of APTF.

It consumes **provider-neutral normalized observations**, estimates the current structure and state of the observed system, adapts its internal parameters as that system evolves, and emits **Dynamic Model Outputs (DMO)** describing current and possible forward evolution.

D01 is intentionally separated from trading policy, trade eligibility, capital allocation, risk authorization, broker connectivity, and execution.

Its core question is:

> **What does the currently observed system appear to be doing, how are the relationships among its signals evolving, and what possible forward evolution is supported by the evidence available now?**

D01 does not answer:

> Should the system trade?

That question belongs downstream.

---

## 2. Position in APTF

The current authoritative relationship is:

```text
Provider-specific market / external sources
                  |
                  v
       Provider-neutral normalization
                  |
                  v
                 D01
      ADAPTIVE PARAMETRIC MODEL
                  |
                  | Dynamic Model Outputs
                  v
                 D02
       RETURN SHAPE / FORWARD STATE
                  |
                  v
           RETURN FIELD F(t)
                  |
                  v
                 D04
          TRADING ENVELOPE
                  |
                  | Capturability /
                  | adaptive aperture
                  v
                 D05
          OPPORTUNITY ENGINE
                  |
                  v
        Decision / Risk / Execution
```

D01 is therefore an **intelligence producer**, not a trading engine.

---

## 3. Design Boundary

### 3.1 D01 Owns

D01 may own or produce:

- Adaptive parameter state.
- Signal-state representations.
- Signal relationships and interactions.
- Nonlinear response structures.
- State estimation.
- State-transition inference.
- Regime-relevant model state where supported.
- Temporal relevance and memory state.
- Perturbation-responsive parameter changes.
- Dynamic Model Outputs.
- Forward Model Outputs.
- Uncertainty / confidence metadata.
- Model-health metadata.
- Versioned model-state snapshots.
- Point-in-time traceability.

### 3.2 D01 Does Not Own

D01 must not own:

- EODHD-specific schemas.
- Alpaca-specific schemas.
- MCP integration.
- Market-data authentication.
- Broker authentication.
- Order placement.
- Position ownership.
- Portfolio allocation.
- Account balances.
- Trade sizing.
- Risk authorization.
- Trading Envelope thresholds.
- Capturability gates.
- BUY / SELL policy.
- Stop-loss policy.
- Execution policy.
- Broker connectivity.
- Profit targets.

The model must remain usable even if the market-data provider or broker changes.

---

## 4. Provider-Neutral Observation Principle

D01 consumes **normalized observations**, never vendor-native messages.

Conceptually:

```text
                  +--> EODHD REST / WebSocket
                  |
Market Gateway ---+--> Alpaca market data
                  |
                  +--> another provider
                  |
                  +--> historical replay
                           |
                           v
                 NORMALIZED OBSERVATIONS
                           |
                           v
                          D01
```

For APTF, EODHD is currently a candidate **market / external-data source**.

It is not a replacement for Alpaca Paper, which is an execution-test destination.

```text
EODHD
MARKET / EXTERNAL DATA SOURCE
        |
        v
APTF INTELLIGENCE
        |
        v
Alpaca Paper
EXECUTION TEST DESTINATION
```

The EODHD MCP layer is not required in the D01 production data path.

Direct source interfaces should be preferred:

- REST for historical/reference/event datasets.
- WebSocket or equivalent stream transport for real-time observations.

MCP may remain useful as a human/LLM research interface outside the deterministic APTF production data plane.

---

## 5. Observation Model

D01 should begin with primitive or near-primitive observations rather than inheriting a vendor's trading interpretation.

Potential normalized observations can include:

- Trade price.
- Bid.
- Ask.
- Bid size.
- Ask size.
- Trade size.
- Volume.
- Quote updates.
- Trade timestamps.
- Exchange timestamps.
- Receive timestamps.
- Session state.
- Instrument identity.
- Source-health metadata.
- Data-quality metadata.

Derived observations may later include:

- Price displacement.
- Velocity.
- Acceleration.
- Volatility.
- Spread.
- Liquidity measures.
- Order-flow measures.
- Volume concentration.
- Relative activity.
- Cross-instrument relationships.

The exact feature set is an experimental concern.

### Design principle

> **D01 should learn from observations rather than being forced to reproduce somebody else's technical indicator vocabulary.**

Vendor-calculated indicators can later be introduced as additional candidate signals, but they should not define the model's ontology.

---

## 6. Point-in-Time Causality

For every D01 output at model time \(t_m\):

> **Every observation, parameter state, feature, relationship, model snapshot, and derived quantity used to generate that output must have been available at or before \(t_m\).**

Historical replay must enforce the same rule.

No future observation may retroactively improve a past DMO.

This rule is mandatory for:

- training,
- replay,
- parameter estimation,
- forward evaluation,
- comparison of candidate models,
- and later real-time operation.

---

# Part I — Temporal Model

## 7. Why Fixed Forecast Horizons Are Insufficient

D01 is not designed around a sequence such as:

```text
observe fixed 60-second window
        |
        v
make one 5-minute forecast
        |
        v
wait five minutes
        |
        v
score forecast
```

That structure is too static for the current APTF ontology.

The observed system may evolve materially while a nominal horizon is still open.

D01 therefore uses:

- **Observation Intervals**
- **Model Time**
- **Forward Intervals**
- **Adaptive temporal relevance**
- **Half-life**
- **Perturbation/event-driven temporal change**

---

## 8. Temporal Primitives

The initial D01 temporal model is:

\[
\boxed{
T(t)=
\{
I_o,\mathbf{H}_o(t),t_m,I_f,H_f(t)
\}
}
\]

where:

- \(I_o\) = observation interval or observation temporal domain.
- \(\mathbf{H}_o(t)\) = observation-memory half-life state, potentially signal-specific.
- \(t_m\) = model time at which the DMO is emitted.
- \(I_f\) = forward interval or forward temporal domain.
- \(H_f(t)\) = forward-state half-life / expected persistence measure.

This is a **working logical representation**, not final mathematics.

---

## 9. Observation Interval \(I_o\)

An Observation Interval is the bounded temporal domain containing observations considered relevant to a particular model state.

It is not assumed to be:

- fixed length,
- uniformly sampled,
- uniformly weighted,
- or equally important across regimes.

An initial representation may be:

\[
I_o=[t_a,t_m]
\]

but the model should permit the effective temporal span and internal relevance to change.

---

## 10. Forward Interval \(I_f\)

A Forward Interval is the temporal domain over which a Forward Model Output expresses possible evolution.

An initial representation may be:

\[
I_f=[t_m,t_c]
\]

but D01 should not assume that the whole interval has one uniform expected state.

For example:

```text
0–10 sec      rapidly strengthening
10–25 sec     high persistence
25–50 sec     gradual decay
50–90 sec     reversal risk increasing
```

The FMO may therefore behave as a function over the forward interval rather than as one scalar attached to a horizon.

---

## 11. Non-Linear Intervals

Intervals may be non-linear in several senses.

### 11.1 Non-linear internal weighting

Observations within \(I_o\) need not contribute equally.

A temporal relevance function may be represented initially as:

\[
w(\tau)
\]

where \(\tau\) is observation age.

The function may eventually be:

- exponential,
- piecewise,
- asymmetric,
- event-dependent,
- regime-dependent,
- multi-rate,
- or learned.

### 11.2 Non-uniform observation density

D01 should not require equally spaced observations.

Conceptually:

```text
t-300s
t-120s
t-60s
t-30s
t-15s
t-7s
t-3s
t-1s
t
```

Observation density may increase near meaningful perturbations.

### 11.3 Non-linear forward geometry

A forward state may strengthen, plateau, decay, and reverse within one \(I_f\).

This temporal geometry is a natural input to D02 Return Shape construction.

---

## 12. Clock Time Versus Model Evolution

D01 should explicitly avoid assuming:

\[
\text{equal clock time}
=
\text{equal amount of system evolution}
\]

Thirty seconds in a violent market perturbation may contain more state evolution than several minutes in a quiet market.

A future research direction may introduce a model-relative temporal coordinate:

\[
d\eta = g(S(t))\,dt
\]

where \(g(S(t))\) changes according to the rate of state evolution.

This is **not committed V0.1 implementation mathematics**.

It records the architectural principle that temporal relevance may depend on system evolution, not merely wall-clock duration.

---

# Part II — Adaptive Half-Life

## 13. Half-Life as Temporal Relevance

An interval defines the available temporal domain.

A half-life describes how rapidly the influence of information within that domain loses relevance.

A simple V0 candidate decay function is:

\[
w(\Delta t)=2^{-\Delta t/H}
\]

where \(H\) is the half-life.

Example:

```text
age = 0H        influence = 100%
age = 1H        influence = 50%
age = 2H        influence = 25%
age = 3H        influence = 12.5%
```

This is an initial parameterization only.

D01 must not assume exponential decay is the final correct model.

---

## 14. Observation Memory Half-Life \(H_o\)

Observation Memory Half-Life represents how quickly historical information loses relevance to the current D01 state.

Rather than one permanent constant:

\[
H_o = constant
\]

the design permits:

\[
\boxed{H_o=H_o(t)}
\]

and ultimately:

\[
\boxed{H_o(t)=\mathcal H(S(t),P(t),E(t))}
\]

where:

- \(S(t)\) = current inferred state.
- \(P(t)\) = perturbation state.
- \(E(t)\) = event context.

---

## 15. Perturbation-Driven Half-Life

A perturbation may alter not only the inferred state but also **how much of the past the model should continue believing**.

Example:

```text
BEFORE PERTURBATION

H_o = 240 sec
historical state remains relevant

             |
             v

      PERTURBATION

             |
             v

AFTER PERTURBATION

H_o = 25 sec
pre-perturbation observations
rapidly lose influence
```

This may be a discontinuous transition.

D01 should not force memory to change smoothly when the observed system itself changes abruptly.

---

## 16. Event-Driven Half-Life

External or internally detected events may change temporal relevance.

Examples could eventually include:

- Scheduled economic event.
- Earnings event.
- Market open.
- Market close.
- Trading halt.
- Liquidity shock.
- Volatility shock.
- Sudden large displacement.
- Cross-market perturbation.

An event can:

- shorten half-life,
- lengthen half-life,
- reset half-life,
- change the decay function,
- or invalidate a prior state.

The exact event-to-half-life relationship must be learned or experimentally validated rather than assumed.

---

## 17. Adaptive Half-Life Vector

There may not be one half-life for the entire model.

D01 can eventually maintain:

\[
\boxed{
\mathbf H_o(t)
=
[
H_1(t),
H_2(t),
\ldots,
H_n(t)
]
}
\]

Potential examples include:

\[
H_{\text{price}}(t)
\]

\[
H_{\text{volume}}(t)
\]

\[
H_{\text{volatility}}(t)
\]

\[
H_{\text{liquidity}}(t)
\]

\[
H_{\text{relationship}}(t)
\]

Different perturbations may affect each component differently.

---

## 18. Forward-State Half-Life \(H_f\)

D01 may also emit a Forward-State Half-Life.

Working definition:

> **Forward-State Half-Life is the estimated period over which the current evidence supporting a forward state would fall to approximately half its current influence in the absence of reinforcing evidence.**

It can become part of the FMO and subsequently contribute to D02 Return Shape properties such as:

- expected persistence,
- opportunity lifetime,
- expected decay,
- reversal timing,
- uncertainty evolution.

\(H_f\) is distinct from \(H_o\).

---

# Part III — Adaptive Signal Entity

## 19. Why a Signal Needs More Than a Score

D01 should avoid reducing every internal signal to one scalar such as:

```text
signal_strength = 0.82
```

A signal may be:

- strong but short-lived,
- weak but persistent,
- strongly reinforced,
- strongly contradicted,
- high-mass but low directional effect,
- or low-mass but highly disruptive.

D01 therefore needs a richer internal signal representation.

---

## 20. Adaptive Signal — Working Definition

A working Adaptive Signal entity is:

\[
\boxed{
\mathcal S_i(t)=
\{
M_i(t),
\rho_i(t),
A_i(t),
H_i(t),
R_i(t),
U_i(t),
\ldots
\}
}
\]

where:

- \(M_i(t)\) = inferred effective mass.
- \(\rho_i(t)\) = inferred density / concentration.
- \(A_i(t)\) = current signal strength.
- \(H_i(t)\) = current half-life.
- \(R_i(t)\) = reinforcement state.
- \(U_i(t)\) = uncertainty.

These are logical properties.

The exact mathematical definitions are experimental.

---

## 21. Mass

### Working definition

> **Mass is an inferred property representing the amount of meaningful participating market activity supporting or opposing an observed state or perturbation.**

Volume is a key observation contributing to mass.

But:

\[
\boxed{\text{Volume is an observation; Mass is an inferred property.}}
\]

D01 must not simply rename a vendor's `volume` field as `mass`.

Mass may eventually depend on combinations of:

- raw volume,
- trade size,
- liquidity,
- bid/ask participation,
- concentration,
- directionality,
- persistence,
- relative activity,
- and market context.

---

## 22. Strength

### Working definition

> **Strength is the current influence exerted by an Adaptive Signal on D01's inferred state or relationships.**

Strength is not identical to volume or mass.

Conceptually:

```text
large volume + little directional displacement
    -> large observed participation
    -> may not imply strong directional signal

moderate volume + coherent large displacement
    -> smaller raw participation
    -> may create a strong perturbation
```

A useful research hypothesis is:

\[
\text{Strength}
\sim
f(\text{Mass},\text{movement},\text{coherence},\ldots)
\]

No fixed formula is committed.

---

## 23. Density

A future useful property may be **signal density**.

Working definition:

> **Density represents how concentrated the participating mass or supporting evidence is within temporal, price, or state space.**

For example:

```text
5M shares / 15 sec / narrow price region
    -> concentrated / dense perturbation

5M shares / 20 min / broad price region
    -> diffuse background
```

A candidate conceptual form is:

\[
\rho_i
\sim
\frac{M_i}
{\text{effective temporal / price / state extent}}
\]

This is explicitly a hypothesis, not production mathematics.

---


## 23A. Volume Influence Mathematics — V0.2 Baseline

Because traded volume is directly observable in the initial market-data set, D01 V0.1/V0.2 should not postpone all volume behavior behind an abstract future Mass model.

Volume should enter the first experimental mathematics explicitly while preserving the distinction:

\[
\boxed{\text{Observed Volume} \neq \text{Inferred Mass}}
\]

Volume is a measured input. Effective Mass remains an inferred property that may later combine volume with liquidity, concentration, directionality, and other evidence.

### 23A.1 Raw Volume

Let:

\[
V(t)
\]

represent observed trade volume over the active sampling unit or event aggregation domain.

Raw volume alone is not an appropriate signal-strength measure because its scale varies substantially by:

- instrument,
- time of day,
- market session,
- volatility state,
- sampling interval,
- and prevailing activity regime.

D01 should therefore retain raw volume for auditability while constructing one or more normalized volume measures for model use.

### 23A.2 Relative Volume

A first normalized quantity can compare current volume with an adaptive reference level:

\[
RV(t)=
\frac{V(t)}
{\widetilde{V}(t)}
\]

where:

\[
\widetilde{V}(t)
\]

is a point-in-time baseline volume estimate derived only from information available at or before model time.

The baseline may initially be a rolling or half-life-weighted mean/median and can later become state- or session-conditioned.

Interpretation:

```text
RV = 1.0     activity near current baseline
RV > 1.0     above-baseline participation
RV < 1.0     below-baseline participation
```

This is a dimensionless quantity and is preferable to comparing raw share counts across different temporal states.

### 23A.3 Log Volume Influence

Because volume spikes can be very large, a candidate compressed representation is:

\[
V_{\log}(t)=\log(1+RV(t))
\]

This prevents one extreme volume observation from dominating the model merely because its raw magnitude is very large.

The exact transform is experimental.

D01 should compare:

- raw relative volume,
- log-relative volume,
- clipped relative volume,
- and potentially rank/percentile representations.

### 23A.4 Time-Decayed Volume Influence

Volume observations should participate in the same adaptive temporal-relevance system as other D01 signals.

For an observation of age \(\Delta t\), a V0 candidate is:

\[
W_V(\Delta t,t)
=
2^{-\Delta t/H_V(t)}
\]

where:

\[
H_V(t)
\]

is the adaptive Volume Observation Half-Life.

The temporally weighted volume contribution becomes:

\[
V^*(t-\Delta t,t)
=
V_{\log}(t-\Delta t)
\cdot
W_V(\Delta t,t)
\]

or, when log compression is not used:

\[
V^*(t-\Delta t,t)
=
RV(t-\Delta t)
\cdot
W_V(\Delta t,t)
\]

Thus high historical volume does not retain permanent influence. Its relevance decays according to the currently active volume half-life.

### 23A.5 Perturbation-Responsive Volume Half-Life

The Volume Half-Life should be eligible for perturbation-driven change:

\[
H_V(t^+)
=
\Phi_V(
H_V(t^-),
P(t),
S(t),
E(t)
)
\]

For example:

```text
normal activity
H_V = 120 sec

sudden volume/price perturbation
        |
        v
H_V = 20 sec

old volume regime rapidly loses relevance
```

Conversely, persistent reinforced participation may cause \(H_V\) to lengthen.

The exact function \(\Phi_V\) is not yet committed.

### 23A.6 Volume Directionality

Raw volume has no intrinsic BUY or SELL sign.

D01 should therefore avoid treating:

\[
V(t)>0
\]

as directional evidence.

A directional volume influence may instead be inferred from the relationship between volume and market movement.

A first experimental quantity can be:

\[
D_V(t)
=
\operatorname{sgn}(\Delta p(t))
\cdot
V_{\log}(t)
\]

where \(\Delta p(t)\) is contemporaneous price displacement.

This is only a baseline hypothesis. Later implementations may use quote/trade classification, order-flow imbalance, or richer microstructure information.

### 23A.7 Volume-Movement Interaction

The initial physical analogy suggests that signal influence may depend not only on participation but on what that participation accomplishes.

A candidate interaction is:

\[
I_{VM}(t)
=
V_{\log}(t)
\cdot
|\Delta p(t)|
\]

or, when direction matters:

\[
I_{VM}^{\pm}(t)
=
V_{\log}(t)
\cdot
\Delta p(t)
\]

This tests the hypothesis:

> Large participation producing meaningful displacement may carry more state information than large participation producing little movement.

The model must also retain the inverse case as potentially informative:

```text
very high volume
+
very small displacement
```

which may indicate absorption, balance, resistance, or another state rather than "weak data."

D01 should learn the relationship instead of assigning a fixed interpretation.

### 23A.8 Volume Concentration / Density

Because equal volume distributed over different temporal extents can have different meaning, a first time-density quantity may be:

\[
\rho_V(t;I)
=
\frac{\sum_{\tau\in I}V(\tau)}
{|I|}
\]

where \(|I|\) is the duration of the active interval.

For irregular event-time sampling, D01 should use actual elapsed time rather than observation count.

A normalized density form can then compare current density with its point-in-time baseline:

\[
R\rho_V(t)
=
\frac{\rho_V(t)}
{\widetilde{\rho}_V(t)}
\]

This provides one candidate bridge from observable volume to the inferred Mass/Density concepts.

### 23A.9 Effective Mass — Initial Candidate

Effective Mass remains inferred, but because volume is available, D01 can test an explicit V0 candidate rather than leaving Mass undefined.

One possible family is:

\[
M_{\text{eff}}(t)
=
f_M(
RV(t),
\rho_V(t),
L(t),
C_D(t)
)
\]

where:

- \(RV(t)\) = relative volume,
- \(\rho_V(t)\) = volume density,
- \(L(t)\) = liquidity-related state where available,
- \(C_D(t)\) = directional/coherence state.

For the earliest experiment, a deliberately simpler baseline may be:

\[
M_{\text{eff},0}(t)=V_{\log}(t)
\]

followed by progressively richer candidate definitions.

This allows experiments to answer whether the abstraction "Mass" adds value beyond normalized volume itself.

### 23A.10 Strength Must Not Equal Volume

Signal Strength should not be set to:

\[
A(t)=RV(t)
\]

by definition.

Instead, volume should be one contributor to a learned or experimentally parameterized strength function:

\[
A_i(t)
=
f_A(
M_i(t),
\Delta p(t),
v_p(t),
a_p(t),
C_i(t),
R_i(t),
U_i(t),
\ldots
)
\]

where \(v_p\) and \(a_p\) represent price velocity and acceleration and \(C_i\) represents a candidate coherence quantity.

The important architectural distinction is:

```text
VOLUME
measured participation
       |
       v
normalized / decayed / concentrated volume state
       |
       v
candidate Effective Mass
       |
       +----------------------+
       |                      |
       v                      v
movement / coherence     temporal persistence
       |                      |
       +----------+-----------+
                  |
                  v
             STRENGTH
```

### 23A.11 Volume Influence Vector

Rather than forcing volume into one scalar, D01 V0.2 can expose a small volume-state vector:

\[
\boxed{
\mathbf V_D(t)=
[
V(t),
RV(t),
V_{\log}(t),
\rho_V(t),
D_V(t),
I_{VM}(t),
H_V(t)
]
}
\]

The first implementation may enable only a subset.

This is preferable to hiding all volume information in one hand-designed score.

### 23A.12 Initial Experimental Comparison

The D01 experiment should compare at least:

```text
V0-A   no volume term

V0-B   relative volume only

V0-C   relative volume + adaptive half-life

V0-D   volume + price-displacement interaction

V0-E   volume + adaptive half-life +
       perturbation-responsive half-life
```

Evaluation should ask whether volume improves:

- Forward Model Output stability,
- directional state quality,
- persistence estimation,
- perturbation detection,
- half-life estimation,
- uncertainty calibration,
- and out-of-sample forward value.

Do not select a volume formulation merely because it increases in-sample fit.

### 23A.13 Design Commitment

Because volume is an available primitive observation:

> **Volume influence mathematics will be included in the first D01 physical experiment rather than deferred entirely to a future Mass abstraction.**

At the same time:

> **The first implementation must preserve raw volume, normalized volume, temporal weighting, and inferred Mass as distinct concepts so experiments can determine which representation adds genuine forward value.**

---

## 24. Reinforcement

### Working definition

> **Reinforcement describes whether newly arriving evidence is extending, sustaining, weakening, or contradicting an existing Adaptive Signal.**

A signal may therefore change without merely decaying.

Example:

```text
t0
strength     0.90
half-life    20 sec

t+10
reinforcing evidence arrives
strength     0.96
half-life    45 sec

t+25
continued reinforcement
strength     0.93
half-life    80 sec

t+50
contradictory evidence
strength     0.55
half-life    18 sec
```

Thus half-life is the natural decay behavior **in the absence of reinforcement**.

---

## 25. Uncertainty

Every inferred signal property should carry uncertainty where practical.

Uncertainty should be separable from strength.

A strong signal can still have high uncertainty.

Likewise a weak signal may be estimated with high confidence.

D01 should avoid collapsing:

- strength,
- confidence,
- uncertainty,
- and persistence

into one score.

---

## 26. Signal Lifecycle

An Adaptive Signal can:

```text
EMERGE
   |
   v
STRENGTHEN
   |
   v
PERSIST
   |
   +----> REINFORCE
   |
   +----> WEAKEN
   |
   +----> DEFORM
   |
   +----> REVERSE
   |
   v
DECAY / EXPIRE
```

Perturbations may create, modify, split, merge, or terminate signals.

The physical implementation does not need to support every lifecycle behavior in V0.1, but the logical model should preserve room for them.

---

# Part IV — Perturbation Model

## 27. Perturbation

Working definition:

> **A perturbation is a meaningful change in observable conditions sufficient to alter the inferred system state, signal structure, temporal relevance, or relationship state.**

A perturbation is not automatically:

- a trade signal,
- an opportunity,
- or a directional prediction.

It is evidence that the observed system may have changed.

---

## 28. Perturbation Effects

A perturbation may affect:

\[
P_j(t)
\rightarrow
\{
\Delta A_i,
\Delta H_i,
\Delta R_i,
\Delta U_i,
\Delta M_i,
\Delta \rho_i,
\Delta \theta,
\Delta S
\}
\]

where:

- signal strength may change,
- half-life may change,
- reinforcement may change,
- uncertainty may change,
- effective mass may change,
- density may change,
- adaptive parameters may change,
- inferred state may change.

This expression records the design relationship only.

---

## 29. Perturbation Versus Trigger

A perturbation is an observed or inferred change.

A trigger is an operational decision that the change warrants deeper evaluation.

Therefore:

```text
OBSERVATIONS
     |
     v
PERTURBATION
     |
     v
TRIGGER / RE-EVALUATION
     |
     v
D01 STATE UPDATE
```

D01 may be evaluated continuously even when a separate trigger layer is used to control expensive processing.

---

# Part V — Parameter Model

## 30. Adaptive Parameters

D01 is parametric, but it must not assume:

- one parameter per signal,
- permanent linearity,
- a fixed polynomial degree,
- or one static parameter set across all conditions.

A generic representation is:

\[
\theta(t)=
[
\theta_1(t),
\theta_2(t),
\ldots,
\theta_n(t)
]
\]

The parameters themselves can evolve.

---

## 31. Nonlinear Structure

Candidate relationships may be:

- linear,
- polynomial,
- piecewise,
- interaction-based,
- state-dependent,
- regime-dependent,
- kernel/basis-based,
- probabilistic,
- or hybrid.

For example, one candidate family may be:

\[
y(t)
=
\theta_0(t)
+
\theta_1(t)x
+
\theta_2(t)x^2
+
\cdots
+
\theta_n(t)x^n
\]

But D01 must not be architecturally defined as a polynomial model.

Polynomial degree is a candidate model property subject to validation.

---

## 32. Parameter Interactions

D01 should be able to test interactions among observations or inferred signals.

For example:

```text
volume alone                 weak relationship
price velocity alone         moderate relationship
volume x price velocity      strong relationship
```

The adaptive learning process should determine whether interactions provide stable forward value.

Model complexity should not increase merely because historical fit improves.

---

## 33. Parameter State Versus Model Definition

D01 should maintain two separate concepts.

### Model Definition

Stable model/software structure.

Example:

```text
model_definition_version = D01-M0.1
feature_definition_version = F001
```

### Adaptive Parameter State

Current evolving state.

Example:

```text
parameter_state_version = 00018422
model_time = ...
```

This allows parameters to evolve without pretending every state update is a new software release.

---

# Part VI — State and Relationship Model

## 34. Current State

D01 should emit a versioned current-state representation.

Possible properties may eventually include:

- direction,
- rate of movement,
- acceleration,
- volatility structure,
- volume behavior,
- liquidity condition,
- spread condition,
- signal population,
- signal strength,
- signal half-life,
- reinforcement,
- uncertainty,
- interaction state,
- regime metadata.

The exact state vector is experimental.

---

## 35. Relationship State

D01 is not limited to classifying individual signals.

It should model relationships among signals.

Examples:

- price ↔ volume,
- volatility ↔ volume,
- spread ↔ liquidity,
- price velocity ↔ volume concentration,
- volatility ↔ directional persistence,
- instrument ↔ related instrument,
- event ↔ response.

A relationship itself may have:

- strength,
- half-life,
- reinforcement,
- uncertainty,
- and adaptive parameters.

---

## 36. State Transition

D01 should distinguish current-state intelligence from transition intelligence.

Conceptually:

```text
CURRENT STATE
     |
     v
TRANSITION STRUCTURE
     |
     v
POSSIBLE FUTURE STATES
```

Transition structure may itself adapt.

---

# Part VII — Dynamic Model Outputs

## 37. Dynamic Model Output (DMO)

### Definition

> **Dynamic Model Output (DMO) is any state, parameter, relationship, transition, uncertainty, or forward inference emitted by D01 at a particular model time.**

DMO is the general term for D01 output.

D01 is not primarily a forecasting engine.

---

## 38. DMO Validity

A DMO is valid at a **model time**.

It is not permanently valid merely because some nominal forward interval has not yet elapsed.

A DMO may:

- strengthen,
- weaken,
- reverse,
- change uncertainty,
- alter its half-life,
- change forward support,
- or expire.

Therefore:

```text
Observations
     |
     v
D01
     |
     v
DMO-A
     |
new observations
     |
     v
D01
     |
     v
DMO-B
     |
new observations
     |
     v
...
```

---

## 39. Forward Model Output (FMO)

### Definition

> **Forward Model Output (FMO) is the subset of Dynamic Model Outputs describing possible future evolution across one or more forward intervals.**

An FMO may contain:

- possible direction,
- magnitude,
- transition likelihood,
- temporal persistence,
- half-life,
- decay,
- reversal risk,
- uncertainty,
- multiple possible future states,
- and temporal geometry.

---

## 40. Forecast — Restricted Experimental Term

The word **forecast** is retained only for evaluation.

### Definition

> **Forecast is a testable forward assertion captured from an FMO at one model time and later evaluated against an observed outcome.**

For example:

```text
model_time: 10:31:00
captured FMO assertion:
    positive return state supported
    over selected evaluation interval
```

That captured assertion can later be scored.

D01 itself remains dynamic while the frozen assertion exists only for measurement.

---

## 41. DMO to D02 Contract

The authoritative conceptual relationship is:

\[
\boxed{\text{D01 DMO} \rightarrow \text{D02 Return Shape}}
\]

D02 does not receive one frozen forecast.

It receives a changing collection of model outputs and continuously expresses the relevant forward information as an elastic Return Shape.

Potential DMO/FMO fields feeding D02 include:

```text
model_time
state_version
parameter_state_version

directional_state
magnitude_state

forward_interval
forward_state_distribution

strength
effective_mass
density

observation_half_life
forward_half_life
reinforcement

persistence
decay
reversal_risk
uncertainty

relationship_state
transition_state

model_health
```

The final schema is a D01/D02 interface-design task.

---

# Part VIII — Separation from D04

## 42. D01 Does Not Determine Capturability

D01 may produce a very attractive forward state even when the market is currently impossible or undesirable to execute.

Example:

```text
D01 / D02

Return Shape quality        high
forward support             strong
uncertainty                 low
persistence                 strong
```

while D04 observes:

```text
liquidity                   poor
spread                      excessive
execution feasibility       poor
capital / risk state        constrained
```

D01 should not suppress its intelligence because of these downstream execution conditions.

---

## 43. D04 Capturability Boundary

The current D04 experimental relationship is:

\[
C_i(t)=B_i(t)\times G_i(t)
\]

where:

- \(B_i(t)\) is base Capturability.
- \(G_i(t)\) is a non-compensating feasibility gate.

Therefore:

```text
D01 / D02
excellent Return Shape
        |
        v
D04
base capture high
gate near zero
        |
        v
final Capturability near zero
        |
        v
NO passage through aperture
```

This separation is a primary architectural reason for keeping D01 independent.

---

# Part IX — Adaptation

## 44. Ever-Learning but Not Ever-Changing Production

The APTF learning principle remains:

> **Learning may continue continuously, while production parameter changes remain controlled.**

D01 can support three broad learning states:

```text
DISCOVERY
    |
    v
MAINTENANCE
    |
    v
RE-ADAPTATION
```

The detailed promotion process belongs primarily to D14 Model Registry / Promotion Controller, but D01 must produce traceable candidate state suitable for validation.

---

## 45. Adaptation Timescales

D01 design should permit at least three adaptation timescales.

### Fast

Seconds or event-driven.

Examples:

- state update,
- signal strength update,
- half-life change,
- reinforcement change,
- perturbation response,
- uncertainty update.

### Medium

Minutes to hours.

Examples:

- regime/state-family shift,
- validated parameter-state selection,
- changing relationship importance.

### Slow

Hours to days or longer.

Examples:

- parameter re-estimation,
- model structure comparison,
- interaction testing,
- polynomial-degree testing,
- stability testing,
- candidate promotion.

The first physical prototype may implement only a subset.

---

# Part X — Evaluation

## 46. D01 Evaluation Should Not Reduce to One Forecast Score

Because D01 is dynamic, evaluation should preserve the evolution of the DMO.

Example:

```text
10:31:00   FMO-A ------------------------>
10:31:20      FMO-B --------------------->
10:31:40         FMO-C ------------------>
10:32:00            FMO-D --------------->
                 ...
REALIZED MARKET PATH
```

Useful questions include:

- Did direction become more accurate as evidence accumulated?
- Did magnitude converge toward realized behavior?
- Did uncertainty decrease when it should?
- Did uncertainty increase before failure?
- Was signal deterioration detected?
- Was a reversal represented before it occurred?
- Did half-life estimates correspond to observed persistence?
- Were strong perturbations followed by appropriate memory contraction?
- Did reinforcement extend useful signal life?
- Did relationship strength persist out of sample?
- How stable were parameters across rolling intervals?

---

## 47. Forward-Output Evaluation

A specific captured FMO can be frozen for evaluation without freezing the underlying model.

For every evaluated assertion store:

```text
model_time
observation interval
observation half-life state
parameter state
current state
signal population
FMO
forward interval
forward half-life
uncertainty
realized subsequent path
evaluation result
```

This preserves point-in-time reproducibility.

---

## 48. Rejected / Unused Outputs

D01 learning must not observe only outputs that eventually became trades.

Where practical, preserve subsequent market evolution for:

- traded outputs,
- rejected outputs,
- D04-gated outputs,
- D05-rejected opportunities,
- no-action decisions.

This reduces selection bias from downstream policy.

---

# Part XI — Initial Experimental Scope

## 49. D01 V0.1 Experimental Objective

The first D01 physical experiment should **not** attempt to create a complete trading model.

Its objective should be:

> **Determine whether a small adaptive parametric system with dynamic temporal relevance can produce Forward Model Outputs that demonstrate measurable point-in-time value on unseen observations.**

---

## 50. Initial Data Progression

The current experimental progression is:

```text
EODHD free data
      |
      v
provider adapter
      |
      v
normalized observations
      |
      v
D01 experimental model
      |
      v
Dynamic Model Outputs
      |
      v
Forward Model Outputs
      |
      v
D02 Return Shape
      |
      v
D04 Trading Envelope
      |
      v
compare captured FMO assertions
with subsequent observed behavior
```

Free access is an engineering/model-test source.

It is not yet evidence that EODHD is the final production real-time provider.

---

## 51. Initial Instrument

SPY remains the preferred first controlled instrument once the selected data entitlement supports it.

If the free EODHD tier cannot provide the required SPY dataset, the architecture should not be changed merely to fit the vendor.

The provider adapter should permit another experimental source.

SPY is a controlled first carrier of Return Shapes, not the conceptual center of D01.

---

## 52. Candidate V0.1 Observations

Keep V0.1 small.

Potential starting observations:

- price,
- **trade volume / trade size (required in the initial experiment where available),**
- bid,
- ask,
- spread,
- quote size / liquidity where available,
- timestamp,
- sequence,
- session state.

Potential derived state:

- price displacement,
- velocity,
- acceleration,
- local volatility,
- volume intensity,
- directional coherence,
- spread state,
- liquidity state.

Do not introduce dozens of technical indicators before the temporal/adaptive machinery is proven.

---

## 53. Candidate V0.1 Adaptive Properties

A useful minimal Adaptive Signal should begin with:

```text
strength
half_life
reinforcement
uncertainty
volume_state
```

Because volume is directly observable, the first physical experiment should include
explicit volume influence mathematics.

`effective_mass` and `density` remain inferred candidate properties:

```text
effective_mass
density
```

They may be enabled as experimental extensions without equating either property
directly with raw volume.

The implementation prompt should preserve the ability to enable/disable individual
volume representations and inferred properties.

---

## 54. Candidate V0.1 Temporal Experiment

A first experiment can compare:

```text
A. fixed rolling interval
B. exponential decay with fixed half-life
C. adaptive half-life
D. perturbation-responsive adaptive half-life
```

on the same point-in-time observations.

Questions:

- Does adaptive half-life improve forward-state stability?
- Does perturbation-driven shortening reduce stale-state contamination?
- Does reinforcement-driven lengthening preserve useful persistent states?
- Does the model overreact to noise?
- How sensitive is performance to half-life limits?
- Are the learned/adapted half-lives stable across unseen intervals?

This gives us a controlled experimental progression rather than assuming the most complex design wins.

---

# Part XII — Physical Design Direction

## 55. Proposed D01 Physical Modules

A future Python physical design might use:

```text
d01_adaptive_parametric_model/
|
+-- models/
|   +-- normalized_observation.py
|   +-- adaptive_signal.py
|   +-- parameter_state.py
|   +-- current_state.py
|   +-- dynamic_model_output.py
|   +-- forward_model_output.py
|
+-- temporal/
|   +-- interval.py
|   +-- decay.py
|   +-- half_life.py
|   +-- temporal_relevance.py
|
+-- signals/
|   +-- signal_estimator.py
|   +-- perturbation.py
|   +-- reinforcement.py
|   +-- mass.py
|   +-- density.py
|
+-- model/
|   +-- adaptive_parametric_model.py
|   +-- parameter_update.py
|   +-- relationship_model.py
|   +-- transition_model.py
|
+-- evaluation/
|   +-- point_in_time.py
|   +-- fmo_capture.py
|   +-- realized_outcome.py
|   +-- metrics.py
|
+-- providers/
|   +-- normalized_contract.py
|   +-- replay_provider.py
|   +-- eodhd_adapter.py
|
+-- runtime/
|   +-- replay_loop.py
|   +-- audit.py
|
+-- tests/
+-- experiments/
+-- output/
```

This is a design direction, not yet an implementation instruction.

---

## 56. Replaceable Interfaces

The physical design should make these replaceable:

### Data source

```text
EODHD
Alpaca market data
historical file
another provider
        |
        v
normalized observation interface
```

### Temporal decay

```text
fixed window
fixed exponential half-life
adaptive half-life
perturbation-responsive half-life
future learned decay
```

### Parameter model

```text
linear
polynomial/basis
state-dependent
interaction model
future alternatives
```

### Transition model

```text
simple deterministic / probabilistic V0
future richer transition model
```

The architecture should make comparison easier than replacement-by-rewrite.

---

# Part XIII — Audit and Reproducibility

## 57. Every DMO Must Be Reproducible

Each emitted DMO should eventually be traceable to:

- observation IDs,
- source-normalization version,
- observation interval,
- temporal-weighting version,
- half-life state,
- parameter-state version,
- model-definition version,
- current state,
- perturbations,
- Adaptive Signals,
- relationship state,
- model time,
- FMO,
- uncertainty,
- and model-health state.

---

## 58. Deterministic Replay

Given:

- the same observation stream,
- the same starting model state,
- the same configuration,
- and the same random seed where randomness is permitted,

historical replay should produce the same DMO/FMO sequence.

Any deliberate stochastic modeling must expose and persist its seed/state.

---

# Part XIV — Safety and Failure Semantics

## 59. D01 Invalid State

D01 should support an explicit invalid/insufficient-information state.

Examples:

- insufficient observation history,
- stale normalized data,
- broken time ordering,
- invalid parameter state,
- numerical instability,
- missing required signal,
- model-health failure.

D01 should not manufacture a confident DMO when required data is invalid.

---

## 60. No Direct Trading Authority

Hard architectural rule:

> **No D01 Dynamic Model Output may directly become a broker order.**

The downstream path remains:

```text
D01
 |
 v
D02 Return Shape
 |
 v
D04 Trading Envelope
 |
 v
D05 Opportunity
 |
 v
D06 Decision
 |
 v
D07 Independent Risk
 |
 v
D09 Execution Policy
 |
 v
D10 Broker Adapter
```

---

# Part XV — Working Hypotheses Versus Commitments

## 61. Current Design Commitments

The following are current logical commitments:

- D01 is provider-neutral.
- D01 produces Dynamic Model Outputs.
- Forward Model Outputs are a subset of DMO.
- Forecast is restricted to captured evaluation assertions.
- D01 output is time/version specific.
- Temporal relevance is not assumed uniform.
- Observation and forward intervals can be elastic.
- Half-life is an initial temporal-relevance primitive.
- Half-life can be adaptive.
- Half-life can be event/perturbation responsive.
- Signal strength and half-life are distinct.
- Reinforcement is distinct from strength.
- Volume is an observation; mass is inferred.
- D01 does not decide Capturability.
- D01 does not place trades.
- Point-in-time causality is mandatory.

---

## 62. Current Working Hypotheses

The following are hypotheses to test, not commitments:

- Exponential half-life is useful.
- Adaptive half-life improves predictive value.
- Perturbation-driven half-life reset is beneficial.
- Reinforcement should lengthen half-life.
- Contradiction should shorten half-life.
- Effective mass improves signal representation.
- Volume is a strong contributor to effective mass.
- Signal density is useful.
- Strength can be expressed as a function of mass, movement, and coherence.
- Relationships themselves should have half-lives.
- Model-relative time can outperform clock-time-only modeling.
- Polynomial or other nonlinear basis functions add stable forward value.

Every hypothesis must be experimentally falsifiable where practical.

---

# Part XVI — Open Design Questions

## 63. Temporal Questions

- What constitutes the first practical \(I_o\)?
- Should \(I_o\) have a hard maximum span?
- What are reasonable initial minimum/maximum half-lives?
- Should half-life vary continuously, discretely, or both?
- What perturbation magnitude warrants discontinuous memory reset?
- Should observation and forward half-life use the same decay family?
- Should each signal own its own half-life from V0.1?

---

## 64. Signal Questions

- What is the minimum useful Adaptive Signal state?
- Is effective mass identifiable from available market observations?
- How should directional coherence be represented?
- Is density useful in time only, price only, or joint state space?
- How should reinforcement be distinguished from ordinary noise?
- Can signals merge/split in a useful and stable way?

---

## 65. Parameter Questions

- Which first parametric family should establish the baseline?
- Should V0.1 use linear relationships first?
- Should polynomial degree be tested immediately or only after baseline?
- Which interaction terms are permitted initially?
- How should parameter drift be bounded?
- How should uncertainty over parameter state be represented?

---

## 66. DMO/FMO Questions

- What is the minimum DMO contract required by D02?
- Should FMO represent discrete branches or a continuous distribution?
- How should FMO temporal geometry be encoded?
- Which outputs are required for initial Return Shape construction?
- How often should a new DMO be emitted?
- Should perturbations force immediate DMO emission?

---

## 67. Evaluation Questions

- What is the primary metric for D01 V0.1?
- Directional accuracy?
- Distribution calibration?
- Magnitude error?
- Transition accuracy?
- Half-life/persistence accuracy?
- Stability across unseen intervals?
- A composite measure?

No profit metric should be used as the sole D01 model-selection criterion.

---

# Part XVII — Recommended Immediate Next Step

## 68. D01 V0.1 Design-to-Experiment Progression

Recommended progression:

```text
1. Freeze this D01 logical-design baseline
            |
            v
2. Define normalized observation contract
            |
            v
3. Define minimal Adaptive Signal
            |
            v
4. Define temporal baseline:
      fixed interval
      fixed half-life
      adaptive half-life
      perturbation-driven half-life
            |
            v
5. Define volume influence baseline:
      relative volume
      temporal decay
      volume density
      volume x movement interaction
            |
            v
6. Define DMO / FMO schema
            |
            v
7. Build deterministic historical replay
            |
            v
8. Run point-in-time experiments
            |
            v
9. Compare temporal / volume models
            |
            v
10. Connect D01 DMO/FMO to D02
            |
            v
11. Replay D01 -> D02 -> D04
```

Only after the D01/D02/D04 replay behaves credibly should the design move toward real-time paper execution.

---

# Part XVIII — Consolidated D01 Picture

## 69. Current Logical Diagram

```text
              PROVIDER-NEUTRAL OBSERVATIONS
                         |
                         v
               +-------------------+
               | DATA / TIME       |
               | INTEGRITY         |
               +---------+---------+
                         |
                         v
                OBSERVATION DOMAIN
                       I_o
                         |
          +--------------+--------------+
          |                             |
          v                             v
    PERTURBATIONS                 RAW / DERIVED
      / EVENTS                      SIGNALS
          |                             |
          +--------------+--------------+
                         |
                         v
               ADAPTIVE SIGNAL FIELD
               S1  S2  ...  Sn
                         |
            +------------+------------+
            |            |            |
            v            v            v
         Strength      Half-Life    Reinforcement
            |            |            |
            +------+-----+-----+------+
                   |           |
                   v           v
               Mass/Density  Uncertainty
                         |
                         v
                RELATIONSHIP MODEL
                         |
                         v
                 PARAMETER STATE
                       theta(t)
                         |
                         v
                   CURRENT STATE
                         |
                         v
                TRANSITION STRUCTURE
                         |
                         v
              DYNAMIC MODEL OUTPUTS
                         |
                   +-----+-----+
                   |           |
                   v           v
             State outputs   FMO
                              |
                              | I_f / H_f
                              v
                             D02
                        RETURN SHAPE
```

---

## 70. Governing D01 Principle

> **D01 continuously estimates an evolving system rather than producing isolated static forecasts. It maintains adaptive parameters, signal strength, temporal relevance, reinforcement, relationships, uncertainty, and state-transition intelligence; emits versioned Dynamic Model Outputs at model time; and allows D02 to express the forward-relevant portion of that intelligence as an elastic Return Shape.**

And:

> **A perturbation may change not only what D01 believes the system is doing, but also how strongly D01 should continue to believe the observations and relationships that preceded the perturbation.**

---

## 71. Status After This Document

With this design baseline:

```text
D01 Adaptive Parametric Model

Status:
LOGICAL DESIGN / EXPERIMENTAL DESIGN BASELINE

Next:
define V0.1 physical experiment and implementation contract
```

The mathematics deliberately remain open where evidence is required.

The next physical design should prove the **adaptive temporal and DMO behavior** before attempting to optimize trading performance.

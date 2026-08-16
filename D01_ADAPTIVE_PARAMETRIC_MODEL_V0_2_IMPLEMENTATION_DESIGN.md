# D01 --- Adaptive Parametric Model v0.2 Implementation Design

**Document:**
`D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN`\
**Model Version:** D01 v0.2\
**Status:** IMPLEMENTATION-READY DESIGN BASELINE\
**Framework:** Adaptive Parametric Trading Framework (APTF)\
**Supersedes as active implementation target:** D01 v0.1.2\
**Preserves:** D01 v0.1.2 and EXP001/001A/001B as experimental baseline
and evidence\
**Primary downstream consumer:** D02 Return Shape\
**Execution boundary:** No broker, order, position, sizing, or
trading-policy responsibility

------------------------------------------------------------------------

## 1. Purpose

D01 v0.2 is the first intentional D01 model designed around APTF's
original dynamic-state architecture.

D01 v0.1.x established the implementation, replay, causality, numerical,
and experimental infrastructure. Its final corrected EXP001B run did
**not** establish control-relative forward value for the v0.1.2
directional formulation. Increasing polynomial order produced only small
changes in directional accuracy while materially worsening numerical
conditioning. D01 v0.2 therefore must **not** be implemented as another
polynomial-order tuning pass or as an attempt to optimize an
UP/NEUTRAL/DOWN classifier.

D01 v0.2 instead estimates an evolving, multidimensional state for one
modeled entity and emits a fan-out of versioned **Dynamic Model Outputs
(DMO)**. Forward-looking subsets of those outputs are **Forward Model
Outputs (FMO)**. D02 consumes these evolving outputs to construct an
elastic Return Shape.

The governing question is:

> **Given the observations available at model time, what is the current
> state of the entity, how strongly is that state supported, how is it
> changing, how persistent is it, what perturbations are acting on it,
> and what forward evolution remains supported over an elastic
> interval?**

D01 does not answer:

> Should APTF trade?

------------------------------------------------------------------------

## 2. Position in APTF

``` text
Provider-specific observations
          |
          v
Provider-neutral normalization
          |
          v
+-----------------------------+
| D01 Adaptive Parametric     |
| Model v0.2                  |
|                             |
| Observation state           |
| Adaptive latent state       |
| Perturbation response       |
| Relevance / half-life       |
| Uncertainty                 |
| DMO fan-out                 |
| FMO fan-out                 |
+-----------------------------+
          |
          v
D02 Elastic Return Shape
          |
          v
D04 Trading Envelope
          |
          v
Opportunity / Risk / Execution
```

D01 is an intelligence producer. D02 constructs forward geometry. D04
determines whether that geometry is physically capturable.

------------------------------------------------------------------------

## 3. Empirical Constraint from D01 v0.1.2

The final corrected EXP001B result is a design constraint, not a target
to tune against.

### 3.1 What v0.1.2 established

-   The final corrected frozen-basis execution completed with
    deterministic, point-in-time replay.
-   Reserve data remained unused.
-   The v0.1.2 formulation was classified as showing **NO EVIDENCE OF
    CONTROL-RELATIVE FORWARD VALUE**.
-   Polynomial-order directional accuracy changed only slightly across
    n1/n2/n3.
-   Higher-order bases produced severe conditioning costs and some
    rank-deficient Phase-3 structures.
-   Volume, adaptive half-life, and perturbation-responsive half-life
    showed no measurable benefit **under the v0.1.2 directional
    evaluation**.

### 3.2 What this does not establish

EXP001B does **not** establish that:

-   adaptive state estimation is useless;
-   volume has no information;
-   half-life is conceptually invalid;
-   perturbations are irrelevant;
-   DMO/FMO are invalid;
-   Return Shape is invalid;
-   D01 should become a conventional classifier.

### 3.3 v0.2 response

D01 v0.2 SHALL:

1.  retain the adaptive-state architecture;
2.  retain DMO/FMO terminology;
3.  retain elastic temporal relevance and half-life;
4.  retain perturbation and volume influence as measurable model
    components;
5.  remove polynomial expansion as the organizing principle of the
    model;
6.  avoid using directional classification as the model's primary
    internal objective;
7.  expose primitive state quantities so downstream experiments can
    determine which combinations have value.

------------------------------------------------------------------------

## 4. Fundamental Entity Topology

D01 has a fundamental entity-local topology:

\[ 1 `\text{entity}`{=tex} : 1 `\text{D01 instance}`{=tex} :
N `\text{input channels}`{=tex} : M `\text{output channels}`{=tex} \]

For entity (i):

\[
`\mathcal{M}`{=tex}\_i:`\mathbf{X}`{=tex}\_i(t)`\rightarrow`{=tex}`\mathbf{Y}`{=tex}\_i(t)
\]

where:

\[ `\mathbf{X}`{=tex}\_i(t)= \[x\_{i1}(t),x\_{i2}(t),...,x\_{iN}(t)\]\^T
\]

is the provider-neutral observation vector and:

\[ `\mathbf{Y}`{=tex}\_i(t)= \[y\_{i1}(t),y\_{i2}(t),...,y\_{iM}(t)\]\^T
\]

is the DMO/FMO fan-out.

There is **not** a required 1:1 mapping between an input channel and an
output channel. Multiple inputs may jointly influence one state
quantity, and one input may influence many outputs.

The entity boundary must be explicit in code. Cross-entity relationships
may later be supplied as normalized relationship channels, but one D01
instance must not silently share mutable state with another entity.

------------------------------------------------------------------------

## 5. Provider-Neutral Input Contract

D01 v0.2 must consume normalized observations, never vendor-native
objects.

Minimum market-data-compatible observation schema:

``` text
entity_id
event_time
receive_time
sequence_id
price
volume
bid                  optional
ask                  optional
bid_size             optional
ask_size             optional
session
source_quality
availability_mask
```

Derived primitive channels may include:

``` text
price_displacement
price_velocity
price_acceleration
realized_variability
spread
relative_volume
volume_density
activity_rate
```

The implementation must preserve an `availability_mask`. Missing bid/ask
or volume information must not be silently converted into a real zero
observation.

------------------------------------------------------------------------

## 6. Point-in-Time Causality

For every output at model time (t_m):

\[
`\mathcal{I}`{=tex}(t_m)={x(`\tau`{=tex}):`\tau`{=tex}`\le `{=tex}t_m}
\]

Only information in (`\mathcal{I}`{=tex}(t_m)) may influence the output.

No future observation may:

-   alter a historical state;
-   alter a historical DMO;
-   alter a historical FMO;
-   alter a historical half-life;
-   alter a historical uncertainty estimate;
-   enter a feature through centered or future-looking normalization.

Replay and live execution must use the same causal update interface.

------------------------------------------------------------------------

## 7. Temporal Geometry

D01 v0.2 must not assume that model relevance is defined only by fixed
clock horizons.

At model time (t_m), define:

\[ T_i(t_m)=
{I\_{o,i},,`\mathbf{H}`{=tex}*{o,i}(t_m),,t_m,,I*{f,i}(t_m),,`\mathbf{H}`{=tex}\_{f,i}(t_m)}
\]

where:

-   (I_o) = observation interval/domain;
-   (`\mathbf `{=tex}H_o) = observation relevance half-lives;
-   (I_f) = forward interval/domain;
-   (`\mathbf `{=tex}H_f) = forward relevance half-lives.

Intervals may be:

-   unequal;
-   overlapping;
-   non-linear;
-   event-defined;
-   perturbation-defined;
-   activity-defined;
-   elastic in length.

Fixed 1m/5m/15m/30m horizons may remain **evaluation projections**, but
they must not define the internal ontology of v0.2.

------------------------------------------------------------------------

## 8. Relevance and Half-Life

Half-life represents the decay of relevance, not a fixed forecast
expiration.

For state component (k), a baseline relevance kernel may be:

\[ w_k(`\Delta `{=tex}t)=2\^{-`\Delta `{=tex}t/H_k(t)} \]

but (H_k(t)) is adaptive.

Define:

\[ H_k(t)= `\operatorname{clip}`{=tex} `\left`{=tex}( H\_{0,k}
`\cdot `{=tex}R_k(t) `\cdot `{=tex}C_k(t) `\cdot `{=tex}P_k(t),
H\_{min,k}, H\_{max,k} `\right`{=tex}) \]

where:

-   (H\_{0,k}) = baseline half-life;
-   (R_k(t)) = reinforcement factor;
-   (C_k(t)) = contradiction factor;
-   (P_k(t)) = perturbation-response factor.

Interpretation:

-   coherent reinforcement may lengthen relevance;
-   contradiction may shorten relevance;
-   strong perturbation may shorten, reset, or reinitialize relevance;
-   stable persistence may lengthen relevance.

The exact factor functions are tunable implementation functions, but
their inputs and outputs must be logged.

Half-life SHALL be available separately for major DMO/FMO channels
rather than one global scalar.

------------------------------------------------------------------------

## 9. Core State Representation

D01 v0.2 shall maintain an explicit adaptive state vector:

\[ `\mathbf `{=tex}z_i(t)= \[ L,, V,, A,, K,, S,, P,, Q,, U,, R,, D\]\^T
\]

Initial semantic channels:

  -----------------------------------------------------------------------
  Symbol                  Name                    Meaning
  ----------------------- ----------------------- -----------------------
  \(L\)                   level/displacement      normalized location
                          state                   relative to adaptive
                                                  reference

  \(V\)                   state velocity          first-order evolution

  \(A\)                   state acceleration      change in state
                                                  velocity

  \(K\)                   curvature               local
                                                  bending/nonlinearity of
                                                  state path

  \(S\)                   strength                evidence-weighted
                                                  magnitude/coherence of
                                                  state

  \(P\)                   persistence             tendency of current
                                                  state/evolution to
                                                  continue

  \(Q\)                   perturbation state      magnitude and character
                                                  of recent disturbance

  \(U\)                   uncertainty             uncertainty associated
                                                  with state/output

  \(R\)                   reversal propensity     evidence that current
                                                  evolution may change
                                                  sign/form

  \(D\)                   decay/relevance         current temporal
                                                  relevance state
  -----------------------------------------------------------------------

These are semantic outputs. The implementation may maintain additional
internal parameters, but it must not collapse all semantics into one
opaque score.

------------------------------------------------------------------------

## 10. Adaptive Reference and Primitive Kinematics

Let normalized price-like state be (p(t)).

Maintain a causal adaptive reference (`\mu`{=tex}(t)):

\[
`\mu`{=tex}*t=`\mu`{=tex}*{t-1}+`\alpha`{=tex}*`\mu`{=tex}(t)(p_t-`\mu`{=tex}*{t-1})
\]

Define displacement:

\[ L_t=`\frac{p_t-\mu_t}{s_t+\epsilon}`{=tex} \]

where (s_t) is a causal adaptive scale.

For irregular intervals:

\[ `\Delta `{=tex}t_t=t_t-t\_{t-1} \]

\[ V_t=`\frac{L_t-L_{t-1}}{\Delta t_t+\epsilon}`{=tex} \]

\[ A_t=`\frac{V_t-V_{t-1}}{\Delta t_t+\epsilon}`{=tex} \]

A causal curvature proxy may begin as:

\[ K_t=`\frac{A_t}{(1+V_t^2)^{3/2}}`{=tex} \]

The implementation must make (`\epsilon`{=tex}), scale floors, and
clipping explicit in configuration.

These quantities are **state descriptors**, not predictions.

------------------------------------------------------------------------

## 11. Adaptive Parameter Update

v0.2 should use bounded adaptive updates rather than unconstrained
polynomial regression as its central mechanism.

For adaptive parameter (`\theta`{=tex}\_k):

\[ `\theta`{=tex}*{k,t} = `\Pi`{=tex}*{`\Theta`{=tex}\_k} `\left[
\theta_{k,t-1}
+
\eta_k(t)\,
g_k(t)
\right]`{=tex}\]

where:

-   (g_k(t)) is a causal innovation/update term;
-   (`\eta`{=tex}\_k(t)) is adaptive learning rate;
-   (`\Pi`{=tex}\_{`\Theta`{=tex}\_k}) projects into an admissible
    bounded domain.

A generic adaptive learning rate:

\[ `\eta`{=tex}*k(t)= `\eta`{=tex}*{0,k} `\cdot`{=tex} f_S(S_t)
`\cdot`{=tex} f_U(U_t) `\cdot`{=tex} f_Q(Q_t) \]

Required behavior:

-   high uncertainty may reduce aggressive adaptation;
-   a strong credible perturbation may temporarily increase adaptation;
-   weak/noisy evidence must not produce parameter explosion;
-   every adaptive parameter must have explicit bounds.

The implementation shall expose parameter snapshots and update
magnitudes.

------------------------------------------------------------------------

## 12. Innovation

Define an innovation/residual vector:

\[ `\mathbf `{=tex}e_t=
`\mathbf `{=tex}x_t-`\hat{\mathbf x}`{=tex}\_{t\|t-1} \]

The model need not be a classical Kalman filter, but it must explicitly
distinguish:

-   expected evolution;
-   newly observed deviation;
-   adaptation caused by that deviation.

A normalized innovation magnitude:

\[ J_t= `\sqrt{
\mathbf e_t^T
\mathbf W_t
\mathbf e_t
}`{=tex} \]

may be used as one input to perturbation strength.

------------------------------------------------------------------------

## 13. Perturbation Model

A perturbation is a meaningful change in the observed system relative to
its currently inferred state.

Represent:

\[ `\mathbf `{=tex}q_t= \[ q\_{`\text{price}`{=tex}},
q\_{`\text{volume}`{=tex}}, q\_{`\text{spread}`{=tex}},
q\_{`\text{activity}`{=tex}}, q\_{`\text{relationship}`{=tex}}\]\^T \]

and aggregate magnitude:

\[ Q_t= `\phi`{=tex}*Q(`\mathbf `{=tex}q_t,`\mathbf `{=tex}z*{t-1}) \]

v0.2 must distinguish at least:

``` text
NONE
REINFORCING
CONTRADICTING
REVERSING
STRUCTURAL/UNKNOWN
```

The model must not equate "large move" with "strong useful signal."
Perturbation significance depends on state, uncertainty, activity, and
coherence.

Perturbations may:

-   change adaptive learning rates;
-   shorten or reset half-life;
-   increase uncertainty initially;
-   strengthen a state if coherently reinforced;
-   raise reversal propensity if contradictory.

------------------------------------------------------------------------

## 14. Strength and Volume Influence

Strength is not volume itself.

Volume is an observed quantity. "Mass" is an inferred analogy: the
amount of market participation supporting or resisting observed
movement.

Define normalized volume influence:

\[ v_t\^\*=
`\log`{=tex}`\left`{=tex}(1+`\frac{V_t^{obs}}{\widetilde V_t+\epsilon}`{=tex}`\right`{=tex})
\]

where (`\widetilde `{=tex}V_t) is a causal adaptive volume reference.

A candidate effective mass:

\[ M_t= f_M(v_t^\*,,a_t^\*,,`\ell`{=tex}\_t\^\*,,c_t) \]

where:

-   (a_t\^\*) = normalized activity;
-   (`\ell`{=tex}\_t\^\*) = optional liquidity contribution;
-   (c_t) = coherence/quality.

Candidate strength:

\[ S_t= `\sigma`{=tex} `\left`{=tex}( `\beta`{=tex}\_0 +`\beta`{=tex}\_M
M_t +`\beta`{=tex}\_V \|V_t\| +`\beta`{=tex}\_A \|A_t\|
+`\beta`{=tex}\_C C_t -`\beta`{=tex}\_U U_t `\right`{=tex}) \]

where (`\sigma`{=tex}) maps strength to (\[0,1\]).

This is an initial implementable form, not a claim that these
coefficients are empirically optimal.

Critical rule:

> Volume may influence strength, perturbation interpretation,
> uncertainty, and half-life, but volume must not automatically imply
> direction.

All volume influence terms must be individually switchable for ablation
experiments.

------------------------------------------------------------------------

## 15. Coherence

Coherence measures whether multiple relevant channels support a
compatible state interpretation.

Let signed normalized evidence components be (r_j(t)). One simple
starting measure:

\[ C_t= `\frac{
\left|\sum_j \omega_j r_j(t)\right|
}{
\sum_j \omega_j |r_j(t)|+\epsilon
}`{=tex} \]

with:

\[ 0`\le `{=tex}C_t`\le1`{=tex} \]

High coherence means evidence aligns. Low coherence means signals
disagree or cancel.

Coherence contributes to strength and uncertainty but is not itself
direction.

------------------------------------------------------------------------

## 16. Persistence

Persistence represents support for continuation of the current
state/evolution.

A causal exponentially decayed agreement measure may begin as:

\[ P_t= (1-`\alpha`{=tex}*P)P*{t-1} + `\alpha`{=tex}*P `\cdot`{=tex}
`\operatorname{agreement}`{=tex}(V_t,V*{t-1},A_t,Q_t) \]

Normalize to:

\[ 0`\le `{=tex}P_t`\le1`{=tex} \]

Persistence must be separate from strength:

-   a strong perturbation may have low persistence;
-   a weak state may have high persistence;
-   persistent evidence may lengthen FMO half-life.

------------------------------------------------------------------------

## 17. Uncertainty

D01 must emit uncertainty explicitly.

A starting composite:

\[ U_t= `\sigma`{=tex} `\left`{=tex}( `\gamma`{=tex}\_e
`\widetilde `{=tex}J_t +`\gamma`{=tex}\_c(1-C_t) +`\gamma`{=tex}\_q
Q_t\^{unknown} +`\gamma`{=tex}\_d D_t\^{data} +`\gamma`{=tex}\_s
S_t\^{instability} `\right`{=tex}) \]

where the terms represent:

-   normalized innovation;
-   incoherence;
-   unclassified perturbation;
-   data-quality degradation;
-   parameter/state instability.

Required:

\[ 0`\le `{=tex}U_t`\le1`{=tex} \]

Uncertainty is not inverse strength by definition. Both may be high
during a major coherent but newly emerging perturbation.

------------------------------------------------------------------------

## 18. Reversal Propensity

Reversal propensity is not a BUY/SELL signal.

A candidate form:

\[ R_t= `\sigma`{=tex} `\left`{=tex}(
`\rho`{=tex}\_1,`\operatorname{oppose}`{=tex}(V_t,A_t) +
`\rho`{=tex}\_2,Q_t\^{contradict} + `\rho`{=tex}\_3(1-P_t) +
`\rho`{=tex}\_4,`\operatorname{extreme}`{=tex}(L_t) + `\rho`{=tex}\_5
U_t `\right`{=tex}) \]

It expresses evidence that the current state path may not persist.

D02 may use this to widen, skew, shorten, or bifurcate Return Shape
geometry.

------------------------------------------------------------------------

## 19. Risk Ratio / State Quality Ratio

D01 may expose a **descriptive state-quality ratio**, but it must not
become portfolio or trading risk authorization.

Define initially:

\[ `\mathcal `{=tex}R_t= `\frac{
S_t P_t
}{
U_t + R_t + \epsilon
}`{=tex} \]

Interpretation:

-   numerator = supported/persistent state evidence;
-   denominator = uncertainty plus reversal pressure.

This is a model-state diagnostic only.

It must be named in code so it cannot be confused with:

-   reward/risk trade ratio;
-   position risk;
-   Value at Risk;
-   capital-at-risk;
-   D04 capturability.

Suggested output name:

`state_support_ratio`

not `trade_risk_ratio`.

------------------------------------------------------------------------

## 20. DMO Definition

A **Dynamic Model Output (DMO)** is any state, parameter, relationship,
transition, uncertainty, or forward inference emitted by D01 at a
particular model time.

DMO validity is model-time-specific.

A DMO may:

-   strengthen;
-   weaken;
-   reverse;
-   decay;
-   expire;
-   be superseded by a later DMO.

A DMO is not permanently valid merely because its original forward
interval has not elapsed.

------------------------------------------------------------------------

## 21. Required DMO v0.2 Fan-Out

At minimum emit:

``` text
model_time
entity_id
model_version

state_level
state_velocity
state_acceleration
state_curvature

strength
coherence
persistence

perturbation_magnitude
perturbation_class

uncertainty
reversal_propensity
state_support_ratio

observation_half_life
forward_half_life

parameter_state
parameter_update_magnitude

data_quality
model_health

dmo_version
trace_id
```

Every numeric semantic channel must document:

-   units or normalization;
-   expected range;
-   invalid/missing representation;
-   causal inputs;
-   update rule.

------------------------------------------------------------------------

## 22. FMO Definition

A **Forward Model Output (FMO)** is the subset of DMO describing
possible future evolution from the current state.

It is not required to be one point forecast.

For forward coordinate (`\tau`{=tex}):

\[ `\mathbf `{=tex}F_t(`\tau`{=tex}) = \[
`\hat `{=tex}L_t(`\tau`{=tex}), `\hat `{=tex}V_t(`\tau`{=tex}),
`\hat `{=tex}U_t(`\tau`{=tex}), `\hat `{=tex}S_t(`\tau`{=tex}),
`\hat `{=tex}P_t(`\tau`{=tex}), `\hat `{=tex}R_t(`\tau`{=tex})\] \]

for:

\[ `\tau`{=tex}`\in `{=tex}I_f(t) \]

A first v0.2 propagation model may use bounded local state dynamics:

\[ `\hat `{=tex}L_t(`\tau`{=tex}) = L_t + V_t`\tau`{=tex} +
`\frac12`{=tex} A_t`\tau`{=tex}\^2 \]

with relevance decay and uncertainty expansion:

\[ `\hat `{=tex}S_t(`\tau`{=tex}) = S_t,2\^{-`\tau`{=tex}/H\_{S,t}} \]

\[ `\hat `{=tex}P_t(`\tau`{=tex}) = P_t,2\^{-`\tau`{=tex}/H\_{P,t}} \]

\[ `\hat `{=tex}U_t(`\tau`{=tex}) = `\operatorname{clip}`{=tex}
`\left`{=tex}( U_t+`\lambda`{=tex}\_U(`\tau`{=tex},Q_t), 0,1
`\right`{=tex}) \]

This local propagation is an initial FMO generator, not a claim that
price follows a quadratic trajectory. Curvature and acceleration must be
bounded and decay with relevance.

------------------------------------------------------------------------

## 23. Elastic Forward Interval

The FMO forward interval length must be state-dependent.

Define:

\[ I_f(t)=\[0,L_f(t)\] \]

with:

\[ L_f(t)= `\operatorname{clip}`{=tex} `\left`{=tex}( L_0
`\cdot `{=tex}f_P(P_t) `\cdot `{=tex}f_S(S_t) `\cdot `{=tex}f_U(U_t)
`\cdot `{=tex}f_Q(Q_t), L\_{min}, L\_{max} `\right`{=tex}) \]

Expected behavior:

-   stronger persistent coherent state -\> potentially longer interval;
-   high uncertainty -\> shorter interval;
-   contradictory/reversing perturbation -\> shorter interval;
-   stable reinforcement -\> interval may extend.

The interval may be discretized for D02, but the underlying concept
remains elastic.

------------------------------------------------------------------------

## 24. FMO Sampling Geometry

Do not require uniform forward samples.

A default non-linear sampling schedule may concentrate points near model
time:

\[
`\tau`{=tex}\_j=L_f(t)`\left`{=tex}(`\frac{j}{m}`{=tex}`\right`{=tex})\^r
\]

where (r\>1) gives denser near-term sampling.

The exact schedule must be configurable.

D02 must receive the actual (`\tau`{=tex}\_j) coordinates rather than
assume fixed spacing.

------------------------------------------------------------------------

## 25. D02 Contract

D01 v0.2 SHALL NOT construct the final Return Shape.

It provides the state ingredients.

Conceptually:

``` text
D01
 |
 +-- level / velocity / acceleration / curvature
 +-- strength / coherence / persistence
 +-- perturbation state
 +-- uncertainty
 +-- reversal propensity
 +-- half-life / elastic interval
 +-- forward state samples
 |
 v
D02
 |
 v
Elastic Return Shape
```

D02 is responsible for translating these into return-space geometry.

This separation must be preserved in code.

------------------------------------------------------------------------

## 26. No Primary Direction Classifier

D01 v0.2 must not contain a primary architecture whose objective is:

``` text
UP
NEUTRAL
DOWN
```

Direction may be derived later as an **evaluation projection** from an
FMO.

Example:

\[ direction_h(t)= `\operatorname{sign}`{=tex} (`\hat `{=tex}L_t(h)-L_t)
\]

but this is not the model ontology.

This distinction is essential.

------------------------------------------------------------------------

## 27. No Unbounded Polynomial Basis

D01 v0.2 SHALL NOT use n1/n2/n3 polynomial feature expansion as its
central adaptive representation.

Polynomial or interaction terms may only be introduced later as
individually justified, bounded candidate relationships.

Any such term must have:

-   semantic purpose;
-   numerical scaling;
-   explicit bound;
-   ablation switch;
-   conditioning diagnostics.

No combinatorial feature expansion.

------------------------------------------------------------------------

## 28. Numerical Safety

All adaptive quantities require explicit numerical contracts.

Required protections:

``` text
finite-value assertion
scale floor
denominator epsilon
bounded learning rate
bounded parameter domain
bounded state domain where appropriate
bounded half-life
bounded forward interval
bounded uncertainty
bounded strength
bounded persistence
bounded reversal propensity
```

No silent NaN/Inf replacement.

A non-finite core state is a model-health failure.

------------------------------------------------------------------------

## 29. Model Health

Emit:

``` text
health_status
nonfinite_count
clipping_count
parameter_bound_hits
innovation_extreme_count
data_gap_count
basis_or_state_dimension
update_norm
state_norm
```

Suggested states:

``` text
HEALTHY
DEGRADED_DATA
DEGRADED_NUMERICAL
PERTURBED
INVALID
```

`PERTURBED` is not necessarily unhealthy; it means the system is
experiencing a material disturbance.

------------------------------------------------------------------------

## 30. Determinism

Given identical:

-   normalized observation sequence;
-   configuration;
-   initial state;
-   model version;
-   random seed where applicable;

D01 v0.2 must produce identical semantic outputs and parameter
evolution.

Runtime metadata such as PID and wall-clock duration is excluded.

------------------------------------------------------------------------

## 31. State Snapshot

Implement a serializable state snapshot containing at least:

``` text
entity_id
model_version
model_time
observation_sequence
adaptive_reference
adaptive_scale
state_vector
adaptive_parameters
half_life_state
perturbation_state
uncertainty_state
previous_observation
previous_dmo
configuration_hash
state_hash
```

A restored snapshot followed by the same observations must reproduce the
uninterrupted run.

------------------------------------------------------------------------

## 32. Configuration

Create an explicit v0.2 configuration object.

Minimum groups:

``` text
reference:
  alpha
  min_scale

kinematics:
  dt_floor
  velocity_bound
  acceleration_bound
  curvature_bound

adaptation:
  base_learning_rates
  min_learning_rate
  max_learning_rate
  parameter_bounds

volume:
  enabled
  reference_alpha
  influence_bounds

strength:
  coefficients
  bounds

coherence:
  channel_weights

persistence:
  alpha
  bounds

perturbation:
  thresholds
  classes
  adaptation_multiplier_bounds

uncertainty:
  coefficients
  bounds

reversal:
  coefficients
  bounds

half_life:
  baseline
  min
  max
  reinforcement_multiplier_bounds
  contradiction_multiplier_bounds
  perturbation_reset_policy

forward:
  min_interval
  baseline_interval
  max_interval
  sample_count
  sampling_exponent

numerical:
  epsilon
  clipping_policy
  nonfinite_policy
```

Every run must persist the resolved configuration and its SHA256.

------------------------------------------------------------------------

## 33. Implementation Modules

Recommended implementation structure:

``` text
d01_adaptive_parametric_model/
  src/
    d01/
      v02/
        __init__.py
        config.py
        observations.py
        state.py
        reference.py
        kinematics.py
        innovation.py
        volume.py
        coherence.py
        perturbation.py
        strength.py
        persistence.py
        uncertainty.py
        reversal.py
        half_life.py
        adaptation.py
        forward.py
        outputs.py
        health.py
        snapshot.py
        model.py
        trace.py
```

Avoid one monolithic model file.

`model.py` should orchestrate components; it should not hide all
mathematics.

------------------------------------------------------------------------

## 34. Update Sequence

For each new observation at (t), execute in deterministic order:

``` text
1. Validate observation and causal sequence.
2. Update availability/data-quality state.
3. Compute dt.
4. Update causal reference and scale.
5. Compute primitive normalized state.
6. Compute kinematics.
7. Compute expected observation/state.
8. Compute innovation.
9. Update volume/activity influence.
10. Classify perturbation.
11. Compute coherence.
12. Update strength.
13. Update persistence.
14. Update uncertainty.
15. Update reversal propensity.
16. Update half-life/relevance state.
17. Update bounded adaptive parameters.
18. Build current DMO.
19. Generate elastic FMO.
20. Run numerical/model-health assertions.
21. Persist trace/snapshot metadata.
22. Return versioned output.
```

Codex must preserve this ordering unless the design document is
explicitly revised.

------------------------------------------------------------------------

## 35. Output Versioning

Every output shall include:

``` text
model_version = "0.2"
dmo_schema_version
fmo_schema_version
config_hash
state_hash
trace_id
```

Never overwrite the meaning of an existing schema version.

------------------------------------------------------------------------

## 36. Traceability

For a selected observation, a reviewer must be able to answer:

-   What observation arrived?
-   What was the prior state?
-   What changed?
-   Was the observation reinforcing or contradictory?
-   What perturbation was inferred?
-   How did strength change?
-   How did uncertainty change?
-   How did half-life change?
-   Which parameters adapted?
-   What DMO was emitted?
-   What FMO interval was emitted?
-   Why did the forward interval lengthen or shorten?

Provide a structured trace mode for this purpose.

------------------------------------------------------------------------

## 37. Unit Tests

At minimum implement tests for:

### Causality

-   future observation cannot affect prior output;
-   out-of-order observation rejected or explicitly handled;
-   replay/live update path identical.

### Kinematics

-   constant state -\> near-zero velocity/acceleration;
-   linear state -\> stable velocity;
-   changing velocity -\> expected acceleration sign.

### Volume

-   volume changes strength/mass inputs when enabled;
-   volume alone does not force direction;
-   disabled volume path produces deterministic ablation.

### Perturbation

-   reinforcing event classified correctly;
-   contradicting event classified correctly;
-   reversal event raises reversal propensity;
-   perturbation can shorten/reset half-life.

### Half-life

-   reinforcement can lengthen;
-   contradiction can shorten;
-   bounds always enforced;
-   decay follows configured relevance function.

### Strength / uncertainty

-   outputs remain bounded;
-   high coherence can increase strength;
-   disagreement can increase uncertainty;
-   strength and uncertainty may coexist at high values.

### FMO

-   elastic interval changes with state;
-   non-linear sample coordinates are ordered;
-   no FMO sample precedes model time;
-   uncertainty does not decrease merely because horizon increases
    unless model evidence explicitly supports it.

### Numerical

-   no NaN/Inf;
-   bounded state;
-   bounded parameters;
-   deterministic replay.

### Snapshot

-   save/restore equivalence.

------------------------------------------------------------------------

## 38. Synthetic Acceptance Scenarios

Before historical SPY testing, create deterministic scenarios.

### S01 --- Stationary

Constant price/activity.

Expected: - low velocity/acceleration; - low perturbation; - low
strength unless evidence supports otherwise; - short/neutral FMO
geometry.

### S02 --- Smooth Persistent Drift

Gradual monotonic displacement with coherent activity.

Expected: - stable velocity; - positive persistence; - increasing or
sustained strength; - longer forward relevance than S01 if uncertainty
remains controlled.

### S03 --- Accelerating Move

Velocity increases coherently.

Expected: - acceleration rises; - curvature changes; - strength may
rise; - FMO reflects changing state.

### S04 --- High-Volume Reinforcement

Existing move receives unusually high coherent volume.

Expected: - effective mass/strength response; - reinforcement
classification; - half-life may lengthen.

### S05 --- High-Volume Contradiction

High volume opposes current evolution.

Expected: - contradiction perturbation; - uncertainty and/or reversal
propensity rises; - forward half-life shortens.

### S06 --- Sudden Reversal

State changes direction abruptly.

Expected: - strong perturbation; - reversal propensity rises; -
old-state relevance collapses/shortens; - new state begins adapting.

### S07 --- Noisy Incoherent Market

Alternating motion with inconsistent volume/activity.

Expected: - low coherence; - elevated uncertainty; - limited
persistence; - short elastic forward interval.

### S08 --- Data Gap

Observation interval suddenly expands.

Expected: - no fabricated intermediate observations; -
uncertainty/data-quality degradation; - kinematic dt handled correctly.

### S09 --- Same Price Path, Different Volume

Two paths share identical prices but different volume patterns.

Expected: - kinematic direction identical; -
strength/perturbation/half-life may differ; - proves volume is
influence, not direction.

### S10 --- Perturbation Recovery

Large disturbance followed by coherent stabilization.

Expected: - perturbation initially high; - half-life/state confidence
rebuilds rather than instantly returning.

------------------------------------------------------------------------

## 39. Initial Historical Experiment for v0.2

Do **not** begin by rerunning the old EXP001B directional matrix.

The first historical v0.2 experiment should validate whether semantic
outputs correspond to observable future behavior.

Suggested experiment name:

`D01_V02_HISTORICAL_EXPERIMENT_001_STATE_VALIDITY`

Primary questions:

1.  Does high persistence correspond to longer realized continuation
    than low persistence?
2.  Does high reversal propensity correspond to higher realized state
    reversal frequency?
3.  Does high uncertainty correspond to larger subsequent model error /
    dispersion?
4.  Does stronger coherent state correspond to more stable subsequent
    evolution?
5.  Does perturbation-triggered half-life shortening improve calibration
    of output validity?
6.  Does volume influence improve any of the above relative to
    volume-disabled ablation?
7.  Does the elastic forward interval contain a measurable relationship
    with how long an FMO remains directionally/state-consistent?

These are **component validity tests**, not trading tests.

------------------------------------------------------------------------

## 40. Evaluation Projections

For empirical evaluation only, DMO/FMO may be projected onto measurable
labels.

Examples:

### Persistence calibration

For persistence bin (b):

\[
`\Pr`{=tex}(`\text{state continuation over }`{=tex}`\tau `{=tex}`\mid `{=tex}P_t`\in `{=tex}b)
\]

should generally increase with (b) if persistence is meaningful.

### Reversal calibration

\[
`\Pr`{=tex}(`\text{state reversal over }`{=tex}`\tau `{=tex}`\mid `{=tex}R_t`\in `{=tex}b)
\]

should generally increase with reversal-propensity bin.

### Uncertainty calibration

\[ E\[\|`\text{FMO error}`{=tex}\| `\mid `{=tex}U_t`\in `{=tex}b\] \]

should generally increase with uncertainty.

### Strength calibration

Measure realized continuation magnitude/stability conditioned on (S_t).

### Half-life calibration

Compare estimated relevance survival against realized state-consistency
duration.

This approach tests whether each semantic output means what its name
claims.

------------------------------------------------------------------------

## 41. Ablation Design

v0.2 must make major mechanisms switchable without changing code.

Required ablations:

``` text
volume influence ON/OFF
perturbation-responsive adaptation ON/OFF
adaptive half-life ON/OFF
coherence influence ON/OFF
reversal channel ON/OFF
elastic forward interval ON/OFF
```

Ablation must preserve point-in-time causality and deterministic replay.

The purpose is to establish causal contribution, not merely correlation.

------------------------------------------------------------------------

## 42. Success Criteria for v0.2

Do not define success as "direction accuracy \> X".

D01 v0.2 is successful enough to proceed to deeper D02 integration when:

1.  all synthetic semantic scenarios pass;
2.  deterministic replay passes;
3.  numerical health passes;
4.  semantic outputs are calibrated in the expected direction on unseen
    historical data;
5.  at least some DMO components demonstrate measurable value over
    simple controls/ablations;
6.  the value is not confined to one pathological slice;
7.  results survive a frozen holdout;
8.  D02 can consume the output without D01 acquiring trading-policy
    responsibilities.

A failure of one semantic component should lead to revision/removal of
that component, not automatic rejection of the entire D01 architecture.

------------------------------------------------------------------------

## 43. Experimental Data Discipline

Maintain:

``` text
development/calibration period
validation period
reserve/holdout period
```

Reserve data must remain untouched until explicitly authorized.

Every experiment must persist:

``` text
dataset path
dataset SHA256
date boundaries
observation count
session coverage
configuration hash
model version
code commit/hash where available
worker PIDs
determinism result
reserve_used flag
```

------------------------------------------------------------------------

## 44. Parallelism

Parallelize across independent:

-   configurations;
-   ablations;
-   entities;
-   synthetic scenarios.

Never parallelize chronological state evolution within one D01 instance.

For Windows:

``` text
ProcessPoolExecutor
top-level worker
if __name__ == "__main__":
```

Long experiments must persist actual PID/concurrency evidence. A
configured `max_workers` value is not proof of parallel execution.

------------------------------------------------------------------------

## 45. Implementation Phases

### Phase A --- v0.2 Core

Implement:

-   configuration;
-   observation contract;
-   state vector;
-   reference/scale;
-   kinematics;
-   innovation;
-   strength;
-   coherence;
-   persistence;
-   perturbation;
-   uncertainty;
-   reversal;
-   half-life;
-   DMO;
-   FMO;
-   health;
-   snapshots.

No historical predictive experiment.

### Phase B --- Synthetic Verification

Run S01--S10 and unit tests.

Hard stop if semantics do not behave as designed.

### Phase C --- Historical State-Validity Experiment

Use frozen historical development/validation periods.

Test semantic calibration and ablations.

Do not use reserve.

### Phase D --- D02 Interface Trial

Only after D01 component validity is established, pass DMO/FMO into D02.

### Phase E --- Reserve Confirmation

Only after an explicit review decision.

------------------------------------------------------------------------

## 46. Codex Implementation Rules

Codex SHALL:

-   implement this document literally before optimizing;
-   keep v0.1.2 intact;
-   create v0.2 in a separate namespace/module path;
-   avoid refactoring v0.1.2 unless required for a shared
    provider-neutral interface;
-   not use EXP001B results to tune coefficients;
-   not inspect reserve data;
-   not add broker integration;
-   not implement D02 or D04;
-   not introduce hidden feature expansion;
-   not add a neural network or external ML library merely to improve
    fit;
-   not silently alter formulas;
-   document every deliberate deviation from this design.

If a formula is underdetermined, implement the simplest bounded
deterministic form consistent with this document and record it in the
implementation report.

------------------------------------------------------------------------

## 47. Required Implementation Artifacts

Codex should produce:

``` text
D01_V0_2_IMPLEMENTATION_REPORT.md
D01_V0_2_MATHEMATICAL_SPECIFICATION.md
D01_V0_2_OUTPUT_SCHEMA.md
D01_V0_2_SYNTHETIC_VALIDATION.md
D01_V0_2_NUMERICAL_HEALTH.md
D01_V0_2_DETERMINISM.md
D01_V0_2_V01_BASELINE_DIFFERENCES.md
```

Machine-readable:

``` text
v02_default_config.json
v02_output_schema.json
v02_synthetic_metrics.csv
v02_scenario_results.csv
v02_determinism.json
v02_manifest.json
```

Logs:

``` text
logs/v02_build.log
logs/v02_tests.log
logs/v02_synthetic_validation.log
```

------------------------------------------------------------------------

## 48. Required Implementation Completion Gate

D01 v0.2 implementation is complete only if:

``` text
D01 v0.1.2 preserved                    PASS
D01 v0.2 isolated namespace             PASS
Point-in-time causality                 PASS
Provider-neutral observation contract  PASS
State fan-out implemented               PASS
Strength implemented                    PASS
Volume influence implemented            PASS
Perturbation model implemented          PASS
Adaptive half-life implemented          PASS
Uncertainty implemented                 PASS
Reversal propensity implemented         PASS
Elastic FMO interval implemented        PASS
No primary direction classifier         PASS
No combinatorial polynomial expansion  PASS
Numerical safety                        PASS
S01-S10                                 PASS
Determinism                             PASS
Snapshot restore                        PASS
Reserve data used                       NO
D02 implemented                         NO
D04 modified                            NO
Broker integration                      NONE
```

------------------------------------------------------------------------

## 49. Initial Default Parameter Philosophy

Defaults must be conservative and bounded.

They are engineering initialization values, **not fitted truths**.

Rules:

-   small adaptation rates;
-   finite minimum scale;
-   finite maximum kinematic state;
-   half-life bounded above and below;
-   uncertainty starts nonzero;
-   forward interval starts short;
-   perturbations may shorten relevance faster than reinforcement
    lengthens it;
-   volume influence starts modest;
-   no one input channel may dominate strength by default.

Every default must be documented and configurable.

------------------------------------------------------------------------

## 50. Design Invariants

The following are architectural invariants for D01 v0.2:

1.  **One entity has one causal evolving D01 state.**
2.  **Many normalized inputs may fan out into many semantic outputs.**
3.  **DMO is broader than forecast.**
4.  **FMO is a dynamic forward-state representation, not a static
    promise.**
5.  **Output validity belongs to model time and may change with new
    evidence.**
6.  **Temporal intervals are elastic and may be non-linear.**
7.  **Half-life is adaptive and may be event/perturbation driven.**
8.  **Strength is not volume; volume contributes to inferred effective
    mass/evidence.**
9.  **Uncertainty is explicit.**
10. **Perturbation is explicit.**
11. **Reversal propensity is descriptive, not a trade instruction.**
12. **D01 does not construct the Trading Envelope.**
13. **D01 does not authorize trades.**
14. **Polynomial complexity is not a substitute for state semantics.**
15. **Every historical output must be point-in-time reproducible.**
16. **Every semantic output must eventually be empirically testable.**

------------------------------------------------------------------------

## 51. First Codex Milestone

The first Codex implementation milestone should end after **Phase B ---
Synthetic Verification**.

It should NOT immediately launch another six-month SPY experiment.

The milestone should answer:

> **Does D01 v0.2 behave internally like the adaptive dynamic-state
> model specified here?**

Only after that review should APTF authorize the historical
state-validity experiment.

------------------------------------------------------------------------

## 52. Final Definition

D01 v0.2 is:

> **A provider-neutral, entity-local, causal adaptive parametric model
> that continuously estimates a multidimensional evolving state,
> measures the strength, persistence, uncertainty, perturbation response
> and temporal relevance of that state, and emits versioned Dynamic
> Model Outputs and elastic Forward Model Outputs for downstream Return
> Shape construction.**

It is not:

-   a static forecast;
-   a three-class direction classifier;
-   a polynomial curve-fitting exercise;
-   a trading strategy;
-   a risk engine;
-   a broker interface.

That distinction is the implementation baseline for D01 v0.2.

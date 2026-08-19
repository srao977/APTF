# APTF D04 Context Field Classification V0.1

Status: DIAGNOSTIC / DESIGN REVIEW ONLY. NOT FROZEN AUTHORITY.

## Frozen D04 input

`TradingEnvelope.process` consumes two separate objects:

1. `ReturnShape`: 17 D02 fields plus nested forward samples.
2. `EnvelopeContext`: 13 required causal context fields.

D04 does not alter market direction. It computes capturability, applies safety/lifecycle logic, updates hysteresis/aperture, and creates or invalidates a candidate.

Legend:

- “Candidate/actionability” means an indirect effect through validation, $H$, $B$, $G$, $C$, hysteresis, safety, or lifecycle.
- “Execution permission” means a distinct post-desire authorization. D04 has no such output; its execution-related fields are pre-desire capturability inputs.

## A. ReturnShape field-by-field classification

| Field | Source | Type | Mathematical use in D04 | Affects direction? | Affects candidate existence? | Affects capturability? | Affects actionability? | Affects execution permission? | Related to six verbs? | Live-only? | Historically derivable? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `model_time` | D02 | float | Ordering, supersession, projection validity | NO | YES, lifecycle | Indirect through $H$ | YES | NO | Indirect | NO | YES | Identity component |
| `entity_id` | D02 | str | Entity binding and candidate identity | NO | Validation only | NO | Validation only | NO | NO | NO | YES | No market math |
| `source_model_version` | D02 | str | Version validation/provenance | NO | Validation only | NO | Validation only | NO | NO | NO | YES | Audit/provenance |
| `current_level` | D02 | float | Recompute/validate displacement geometry | NO | Invalid input can suppress | Validation only | Validation only | NO | Indirect only on failure | NO | Derived by D01 | Does not set orientation in D04 |
| `projection_interval` | D02 | float | Projection validity/staleness | NO | YES | Through $H$ | YES | NO | Indirect | NO | Derived by D01/D02 | Inclusive endpoint |
| `forward_half_life` | D02 | float | Contract validation/diagnostic | NO | Invalid input can suppress | No direct score term | Validation only | NO | No direct relation | NO | Derived by D01 | No soft temporal factor |
| `forward_samples` | D02 | tuple | Full-path validation and recomputation of terminal/max geometry | NO | Invalid input can suppress | Validation supports $Q_G$ | Validation only | NO | Indirect only on failure | NO | Derived by D01 | D04 does not replace samples |
| `terminal_displacement` | D02 | float | $Q_G=|D|/M$ and direction-invariant validation | NO; validates D02 direction | YES through $Q_G$ | YES | YES | NO | Indirect | NO | Derived by D02 | Signed value retained |
| `maximum_absolute_displacement` | D02 | float | $Q_G=|D|/M$; zero branch | NO | YES through $Q_G$ | YES | YES | NO | Indirect | NO | Derived by D02 | Absolute magnitude not separately scored |
| `path_direction` | D02 | enum | Validate sign consistency; copy verbatim to candidate | D02 owns it; D04 cannot change | No score effect | NO | Candidate provenance only | NO | Indirect via D03 desire | NO | Derived by D02 | Domain UPWARD/DOWNWARD/FLAT |
| `terminal_decay_factor` | D02 | float | Validation/diagnostic | NO | Invalid input only | No direct term | Validation only | NO | NO | NO | Derived by D02 | Soft temporal factor omitted |
| `strength` | D02/D01 | float | $Q_S=(scp)^{1/3}$ | NO | YES | YES | YES | NO | Indirect | NO | Derived by D01 | Structural coordinate |
| `coherence` | D02/D01 | float | $Q_S=(scp)^{1/3}$ | NO | YES | YES | YES | NO | Indirect | NO | Derived by D01 | Structural coordinate |
| `persistence` | D02/D01 | float | $Q_S=(scp)^{1/3}$ | NO | YES | YES | YES | NO | Indirect | NO | Derived by D01 | Structural coordinate |
| `uncertainty` | D02/D01 | float | $Q_R=\sqrt{(1-u)(1-r)}$ | NO | YES | YES | YES | NO | Indirect | NO | Derived by D01 | Not a calibrated probability |
| `reversal_propensity` | D02/D01 | float | $Q_R=\sqrt{(1-u)(1-r)}$ | NO | YES | YES | YES | NO | Indirect | NO | Derived by D01 | Does not reverse direction in D04 |
| `state_support_ratio` | D02/D01 | float | Diagnostic; deliberately omitted to avoid double counting | NO | Invalid input only | No direct term | Validation only | NO | NO | NO | Derived by D01 | Unbounded nonnegative ratio |

## B. EnvelopeContext field-by-field classification

| Field | Source | Type | Mathematical use | Affects direction? | Affects candidate existence? | Affects capturability? | Affects actionability? | Affects execution permission? | Related to six verbs? | Live-only? | Historically derivable from existing data? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `evaluation_time` | External causal context | float | Projection validity in $H$; output/event time | NO | YES | YES, through $H$ | YES | NO direct | Indirect through desire | NO | YES | Source timestamp available |
| `market_eligible` | External causal context | bool | Hard eligibility $H$; safety closure | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | Not inherently | NO authoritative mapping | Can drive D03 FLAT via closure |
| `data_integrity` | External causal context | float [0,1] | Hard eligibility $H$ and one dimension of $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | NO | Partially derivable | Critical threshold plus bottleneck |
| `clock_event_quality` | External causal context | float [0,1] | Diagnostic only | NO | NO | NO | NO | NO | NO | Not necessarily | NO authoritative mapping | Required but not score-active |
| `capital_available` | Account/portfolio context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | NO | NO | Portfolio capacity category |
| `portfolio_capacity` | Account/portfolio context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | NO | NO | Portfolio state |
| `position_capacity` | Account/portfolio context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | NO | NO | Explicitly not a position decision |
| `liquidity_quality` | Execution context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | Data-dependent | NO in OHLCV | Needs liquidity evidence |
| `spread_quality` | Execution context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | Data-dependent | NO in OHLCV | Needs quotes/spread |
| `latency_quality` | Execution context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | YES | NO | Requires live/simulated latency |
| `execution_feasibility` | Execution context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | YES for real execution | NO | Broad feasibility fact |
| `risk_capacity` | Account/risk context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | NO | NO | Requires risk state |
| `broker_health` | Broker context | float [0,1] | Minimum gate $G$ | NO | YES | YES | YES | NO distinct post-desire gate | Indirect through desire | YES | NO | Broker-state fact |

## Frozen D04 mathematics

Let $D$ be terminal displacement, $M$ maximum absolute displacement, $s$ strength, $c$ coherence, $p$ persistence, $u$ uncertainty, and $r$ reversal propensity:

$$Q_G=0\text{ if }M=0;\quad Q_G=|D|/M\text{ otherwise}$$

$$Q_S=(scp)^{1/3}$$

$$Q_R=\sqrt{(1-u)(1-r)}$$

$$B=Q_GQ_SQ_R$$

$$G=\min(\text{liquidity, spread, latency, execution, capital, portfolio, position, risk, broker, data})$$

$$H=\mathbf{1}[\text{projection valid}]\mathbf{1}[\text{market eligible}]\mathbf{1}[\text{data integrity above critical}]\mathbf{1}[\text{valid inputs}]$$

$$C=HBG$$

| Quantity | Can change D02 direction? | Can suppress candidate? | Can make candidate unavailable/non-actionable? | Can separately prevent execution after a verb is selected? |
|---|---|---|---|---|
| $Q_G$ | NO | YES through $B/C$ | YES | NO |
| $Q_S$ | NO | YES through $B/C$ | YES | NO |
| $Q_R$ | NO | YES through $B/C$ | YES | NO |
| $B$ | NO | YES through $C$ | YES | NO |
| $G$ | NO | YES through $C$ | YES | NO |
| $H$ | NO | YES; hard closure | YES | NO |
| $C$ | NO | YES through hysteresis/state | YES | NO |

D04 receives direction from D02 and determines whether that directional shape is capturable enough to produce/retain a candidate. It does not determine or transform direction.

## D04 context to verb matrix

| D04 field | Changes desired position? | Changes verb identity? | Can block already-selected verb? | Execution-only in frozen implementation? | Evidence |
|---|---|---|---|---|---|
| `evaluation_time` | Indirectly | Indirectly | NO | NO | Staleness -> state/candidate -> D03 target |
| `market_eligible` | Indirectly | Indirectly | NO | NO | $H$/safety closure |
| `data_integrity` | Indirectly | Indirectly | NO | NO | $H$ and $G$ |
| `clock_event_quality` | NO | NO | NO | NO | Diagnostic only |
| `capital_available` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `portfolio_capacity` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `position_capacity` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `liquidity_quality` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `spread_quality` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `latency_quality` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `execution_feasibility` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `risk_capacity` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |
| `broker_health` | Indirectly | Indirectly | NO | NO | $G$ -> $C$ -> candidate |

“Changes verb identity” is indirect only: D04 changes candidate availability, D03 changes desired state, and the controller then applies the state-pair matrix. D04 never names a verb.

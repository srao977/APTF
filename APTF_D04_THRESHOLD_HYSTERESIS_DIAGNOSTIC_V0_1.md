# APTF D04 Threshold and Hysteresis Diagnostic V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Frozen configuration

| Field | Value | Exact role |
|---|---:|---|
| `hysteresis.open_threshold` | 0.75 | A CLOSED/OPENING state is open-qualifying when $C\ge0.75$ |
| `hysteresis.close_threshold` | 0.55 | An OPEN/CLOSING state is close-qualifying when $C\le0.55$ |
| `open_persistence_observations` | 3 | Number of consecutive open-qualifying evaluations needed to move OPENING to OPEN |
| `close_persistence_observations` | 2 | Number of consecutive close-qualifying evaluations needed to move CLOSING to CLOSED |
| `aperture.alpha` | 0.5 | Exponential smoothing coefficient for aperture after state evaluation |

These are configuration constants in `d04_trading_envelope/config/default.yaml`.

## Threshold semantics and provenance

`0.75` and `0.55` are thresholds on the normalized capturability score $C$. They are not probabilities, confidence levels, directional thresholds, or percentages of expected return.

The deterministic capturability design explicitly states that these numeric thresholds were inherited from the earlier score and were not validated for the new $C$ scale at design time; it required analytic/synthetic component-level revalidation, never outcome tuning. The later frozen implementation reports synthetic/formula/state-machine tests, but repository authority provides no empirical market calibration or probability interpretation for `0.75`.

## Hysteresis state machine

- CLOSED + $C<0.75$ -> CLOSED and reset both counters.
- CLOSED + $C\ge0.75$ -> OPENING, open counter becomes 1.
- OPENING needs consecutive open-qualifying observations until counter reaches 3.
- OPEN + $C>0.55$ -> OPEN.
- OPEN + $C\le0.55$ -> CLOSING, close counter becomes 1.
- CLOSING needs consecutive close-qualifying observations until counter reaches 2.

Persistence means consecutive D04 evaluations, not elapsed time, candidate duration, D02 direction persistence, or the D01 `persistence` coordinate.

## Target state table

| Property | Target A | Target B |
|---|---:|---:|
| timestamp | 2022-09-30T08:16:00Z | 2022-09-30T08:17:00Z |
| D02 `path_direction` | UPWARD | UPWARD |
| $C$ | 0.4814590392445292 | 0.3605075262704571 |
| $G$ | 1.0 | 1.0 |
| aperture before | 0.31165485069974536 | 0.3965569449721373 |
| aperture after | 0.3965569449721373 | 0.37853223562129723 |
| open threshold | 0.75 | 0.75 |
| close threshold | 0.55 | 0.55 |
| prior state | CLOSED | CLOSED |
| pre open/close counters | 0 / 0 | 0 / 0 |
| open qualifying | false | false |
| post open/close counters | 0 / 0 | 0 / 0 |
| candidate condition (`post_state==OPEN`) | false | false |
| candidate created | false | false |
| candidate qualified | NOT REACHED | NOT REACHED |
| final state | CLOSED | CLOSED |

## Aperture

The exact implementation is:

$$
A_t=\alpha\operatorname{clamp}(C_t)+(1-\alpha)\operatorname{clamp}(A_{t-1}),\quad\alpha=0.5.
$$

Aperture is a smoothed D04 control-state view of capturability. It does not contribute to $C$, does not change either threshold, is not directional, and is not checked by candidate creation. Candidate creation uses the post-hysteresis envelope state.

For A: $0.5(0.4814590392445292)+0.5(0.31165485069974536)=0.3965569449721373$.

For B: $0.5(0.3605075262704571)+0.5(0.3965569449721373)=0.37853223562129723$.

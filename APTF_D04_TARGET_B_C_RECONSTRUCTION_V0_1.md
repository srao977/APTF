# APTF D04 Target B C Reconstruction V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

Timestamp: `2022-09-30T08:17:00Z`. The source loop broke immediately after this row; no later row was read.

## Exact numeric calculation

```text
D = terminal_displacement          = 0.3183024678069359
M = maximum_absolute_displacement  = 0.3183024678069359
Q_G = abs(D) / M                   = 1.0

s = strength                       = 0.8976642163450754
c = coherence                      = 0.9999931783150069
p = persistence                    = 0.6672308993184185
s*c*p                              = 0.5989452165144206
Q_S = (s*c*p)^(1/3)                = 0.8429381315925792

u = uncertainty                    = 0.2727585484077373
r = reversal_propensity            = 0.7484880373502629
1-u                                = 0.7272414515922627
1-r                                = 0.2515119626497371
(1-u)*(1-r)                        = 0.18290992481021376
Q_R = sqrt((1-u)*(1-r))            = 0.4276796988520893

B = Q_G * Q_S * Q_R                = 0.3605075262704571
G = min(ten gate dimensions)       = 1.0
projection_valid                   = true
market_eligible                    = true
data_integrity > 0.2               = true
valid finite inputs                = true
H                                  = 1

raw_C = H * B * G                  = 0.3605075262704571
runtime capturability_score        = 0.3605075262704571
exact float equality               = PASS
```

No post-computation clamp changed the value.

## State/candidate chain

| Property | Value |
|---|---|
| D02 direction | UPWARD |
| prior envelope state | CLOSED |
| prior open/close counters | `0 / 0` |
| open qualifying (`C >= 0.75`) | false |
| close qualifying (`C <= 0.55`) | true, but CLOSED branch resets counters |
| post state | CLOSED |
| post counters | `0 / 0` |
| candidate creation condition | false |
| candidate qualification | NOT REACHED |
| candidate | NONE |

## Aperture

```text
prior aperture = 0.3965569449721373
aperture_after = 0.5*C + 0.5*prior
               = 0.37853223562129723
```

Aperture does not enter $C$, thresholds, direction, or candidate creation.

## Fixed-threshold counterfactual boundary

With $H=G=Q_G=1$:

$$
Q_SQ_R\ge0.75.
$$

Current product is `0.3605075262704571`; required multiplicative increase is `2.0804003948515097`.

Holding $Q_S$ fixed requires $Q_R=0.8897450143618614`. Holding $Q_R$ fixed requires impossible $Q_S=1.753648821800596`. Holding current uncertainty fixed would require invalid `r <= -0.08856032456416618`; holding reversal fixed would require invalid `u <= -2.1475488570866053`. There is no unique minimum change; several endogenous analytical factors must change jointly.

# APTF D04 Target A C Reconstruction V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

Timestamp: `2022-09-30T08:16:00Z`. The source iterator stopped no later than Target A for this reconstruction claim; genuine preceding rows established causal D01/D04 state.

## Exact numeric calculation

```text
D = terminal_displacement          = 0.489964861958388
M = maximum_absolute_displacement  = 0.489964861958388
Q_G = abs(D) / M                   = 1.0

s = strength                       = 0.8043937518637954
c = coherence                      = 0.9999999907876206
p = persistence                    = 0.6840391573948615
s*c*p                              = 0.5502368191696115
Q_S = (s*c*p)^(1/3)                = 0.8194388482618388

u = uncertainty                    = 0.296755743816712
r = reversal_propensity            = 0.5091154115712131
1-u                                = 0.703244256183288
1-r                                = 0.4908845884287869
(1-u)*(1-r)                        = 0.3452117672614417
Q_R = sqrt((1-u)*(1-r))            = 0.5875472468333434

B = Q_G * Q_S * Q_R                = 0.4814590392445292
G = min(ten gate dimensions)       = 1.0
projection_valid                   = true
market_eligible                    = true
data_integrity > 0.2               = true
valid finite inputs                = true
H                                  = 1

raw_C = H * B * G                  = 0.4814590392445292
runtime capturability_score        = 0.4814590392445292
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
| candidate creation condition (`state == OPEN and candidate is None`) | false |
| candidate qualification | NOT REACHED |
| candidate | NONE |

## Aperture

Configuration field `aperture.alpha=0.5` is a smoothing coefficient, not the aperture value and not a threshold.

```text
prior aperture = 0.31165485069974536
aperture_after = 0.5*C + 0.5*prior
               = 0.3965569449721373
```

Aperture does not enter $C$, alter the open threshold, or create a candidate in the implementation.

## Fixed-threshold counterfactual boundary

With $H=G=Q_G=1$, reaching the unchanged threshold requires:

$$
Q_SQ_R\ge0.75.
$$

Current product is `0.4814590392445292`; required multiplicative increase is `1.557764916360997`.

There is no unique minimum leaf change. Holding $Q_S$ fixed requires $Q_R=0.9152604878214772$. Holding $Q_R$ fixed would require impossible $Q_S=1.276493088925555`. With current uncertainty fixed, changing reversal alone would require invalid `r <= -0.19119602215261655`; with reversal fixed, changing uncertainty alone would require invalid `u <= -0.7065146886124629`. Multiple endogenous factors must change jointly.

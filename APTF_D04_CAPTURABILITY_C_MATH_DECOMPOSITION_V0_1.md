# APTF D04 Capturability C Mathematical Decomposition V0.1

Status: READ-ONLY DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Complete computational chain

```text
D01 strength, coherence, persistence
  -> Q_S = cube_root(strength * coherence * persistence)

D01 uncertainty, reversal_propensity
  -> Q_R = sqrt((1-uncertainty) * (1-reversal_propensity))

D02 terminal_displacement, maximum_absolute_displacement
  -> Q_G = abs(terminal_displacement) / maximum_absolute_displacement
     (exact zero branch when maximum is zero)

Q_G * Q_S * Q_R -> B

10 D04 gate dimensions -> G = minimum

D02 lifecycle + D04 eligibility/integrity + valid-input check -> H

H * B * G -> C
```

No aperture, hysteresis counter, envelope state, candidate, `path_direction`, absolute magnitude scale, support ratio, half-life, terminal decay, or learned coefficient enters $C$.

## Leaf-input lineage

| Leaf | Domain | Source component/field | Current/prior | Transformation | Weight/coefficient | Contribution |
|---|---|---|---|---|---|---|
| $D$ | finite signed float | D02 `terminal_displacement` | current | absolute value divided by $M$ | none | $Q_G$ |
| $M$ | nonnegative float | D02 `maximum_absolute_displacement` | current | denominator / exact-zero branch | none | $Q_G$ |
| $s$ | `[0,1]` | D01 via D02 `strength` | causal D01 state at current row | geometric mean | exponent `1/3` | $Q_S$ |
| $c$ | `[0,1]` | D01 via D02 `coherence` | causal D01 state | geometric mean | exponent `1/3` | $Q_S$ |
| $p$ | `[0,1]` | D01 via D02 `persistence` | causal D01 state | geometric mean | exponent `1/3` | $Q_S$ |
| $u$ | `[0,1]` | D01 via D02 `uncertainty` | causal D01 state | complement then geometric mean | `1-u`, exponent `1/2` | $Q_R$ |
| $r$ | `[0,1]` | D01 via D02 `reversal_propensity` | causal D01 state | complement then geometric mean | `1-r`, exponent `1/2` | $Q_R$ |
| nine non-data gate dimensions | `[0,1]` | D04 `EnvelopeContext` | current fixed scenario context | minimum | none | $G$ |
| data integrity | `[0,1]` | current row-derived context | current | minimum and hard threshold | critical `0.2` | $G$ and $H$ |
| evaluation time | finite float | current observation | current | compare to model time + interval | none | $H$ |
| model time | finite float | D02 `model_time` | current | projection-valid comparison | none | $H$ |
| projection interval | `[10,600]` | D02 `projection_interval` | current | projection-valid comparison | none | $H$ |
| market eligible | bool | D04 external context | current fixed scenario context | indicator | none | $H$ |
| valid finite inputs | bool | D04 validation | current | indicator | none | $H$ |
| critical integrity threshold | `[0,1]` | frozen D04 config | fixed | strict `>` comparison | `0.2` | $H$ |

## Reproduced input table

| C input | Source | Target A | Target B | Changed? | Effect on C | Semantic classification |
|---|---|---:|---:|---|---|---|
| terminal displacement $D$ | D02 | 0.489964861958388 | 0.3183024678069359 | YES | No change to $Q_G$ because $D=M$ both rows | D02 RETURN-SHAPE DESCRIPTION |
| maximum displacement $M$ | D02 | 0.489964861958388 | 0.3183024678069359 | YES | No change to $Q_G$ | D02 RETURN-SHAPE DESCRIPTION |
| strength $s$ | D01 | 0.8043937518637954 | 0.8976642163450754 | YES | Raises $Q_S$ all else equal | D01 ANALYTICAL STATE |
| coherence $c$ | D01 | 0.9999999907876206 | 0.9999931783150069 | YES | Slightly lowers $Q_S$ all else equal | D01 ANALYTICAL STATE |
| persistence $p$ | D01 | 0.6840391573948615 | 0.6672308993184185 | YES | Lowers $Q_S$ all else equal | D01 ANALYTICAL STATE |
| uncertainty $u$ | D01 | 0.296755743816712 | 0.2727585484077373 | YES | Raises $Q_R$ all else equal because uncertainty fell | D01 ANALYTICAL STATE |
| reversal propensity $r$ | D01 | 0.5091154115712131 | 0.7484880373502629 | YES | Materially lowers $Q_R$ | D01 ANALYTICAL STATE |
| $Q_G$ | D04 transform of D02 | 1.0 | 1.0 | NO | Neutral multiplicative factor | D04 ANALYTICAL/CAPTURABILITY STATE |
| $Q_S$ | D04 transform | 0.8194388482618388 | 0.8429381315925792 | YES | Increased factor | D04 ANALYTICAL/CAPTURABILITY STATE |
| $Q_R$ | D04 transform | 0.5875472468333434 | 0.4276796988520893 | YES | Decreased factor | D04 ANALYTICAL/CAPTURABILITY STATE |
| $H$ | D04 hard eligibility | 1 | 1 | NO | Neutral multiplicative factor | D04 ANALYTICAL/CAPTURABILITY STATE |
| $G$ | D04 context minimum | 1.0 | 1.0 | NO | Neutral multiplicative factor | D04 EXTERNAL/EXECUTION CONTEXT |

## Why C fell

$$
\Delta C=C_B-C_A=-0.12095151297407208
$$

Factor ratios are exact:

- $Q_{G,B}/Q_{G,A}=1$
- $Q_{S,B}/Q_{S,A}=1.0286772873663315$
- $Q_{R,B}/Q_{R,A}=0.7279069064779394$
- $H_B/H_A=1$
- $G_B/G_A=1$
- product ratio $C_B/C_A=0.7487813020109447$

$Q_S$ increased, but $Q_R$ decreased more strongly. The direct mechanical driver is the risk-complement product falling from `0.3452117672614417` to `0.18290992481021376`, principally alongside reversal propensity increasing to `0.7484880373502629`. Because the model is multiplicative, there is no canonical additive share of $\Delta C$ for each factor.

## Leaf count used in console classification

Unique computational leaves/conditions: 23.

- Market observation: 2 (`evaluation_time`, derived `data_integrity`).
- D01 analytical: 5.
- D02 ReturnShape: 4 (`D`, `M`, `model_time`, `projection_interval`).
- D04 analytical/capturability: 1 (`valid finite inputs`).
- D04 external/execution context: 10 (market eligibility plus nine non-data gate dimensions).
- D04 hysteresis/control: 0.
- Other: 1 (critical integrity threshold).

# D01 Stage 2 Evidence Contracts v0.2

**AUTHORITATIVE SOURCE:**  
`D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`

**IN CASE OF CONFLICT, THE FROZEN DESIGN V0.2 CONTROLS.**

This document is a canonical implementation-facing extract of approved Design v0.2. It does not create independent scientific authority.

## 22. Dimension-Level Evidence Contracts

| Dimension | Semantic claim | Independent observable | Primary score | Secondary diagnostics | Horizons | Expected relationship | Minimum support/censoring | Confounder strata | Classification application |
|---|---|---|---|---|---|---|---|---|---|
| State / kinematics | DMO describes local state evolution | Raw-close displacement, slope, curvature, efficiency, deviation | Sign/geometry concordance of DMO direction and realized slope/progress | Component-wise V/A/K mirror concordance and path error | All fixed; FMO coordinates | Positive concordance and compatible geometry | General block policy; per-horizon censoring | All transition strata | Standard four-level rule; zero-direction anchors inconclusive for direction |
| Strength | Stronger state has stronger realized expression | $|b|\times E$ and compatible-progress magnitude | Spearman association strength vs expression | Quintile ordering, stability by horizon | 5/15/30/60 and adaptive interval | Positive | General policy | Session/gap, uncertainty/coherence strata | Standard rule |
| Coherence | Aligned evidence yields consistent evolution | Path efficiency and inverse normalized deviation | Spearman coherence vs efficiency | Deviation ordering and continuation incidence | 5/15/30/60 | Positive efficiency; negative deviation | General policy | Session/gap, availability | Standard rule |
| Persistence | State remains recognizable longer | $T_{valid}$ | Censor-aware concordance between persistence and survival | Survival curves by predictor quintile | Full survival plus fixed/adaptive cuts | Higher persistence -> longer validity | Right/interval censoring mandatory | Session/gap, perturbation class | Standard rule using concordance null 0.5 |
| Uncertainty | Higher uncertainty means more ambiguity/error | $1-E$, normalized deviation, ambiguous incidence | Spearman uncertainty vs realized ambiguity index | Error calibration and instability incidence | 5/15/30/60 and adaptive | Positive | General policy | Session/gap, coherence | Standard rule |
| Reversal propensity | Higher propensity means nearer/more reversal | Reversal event and time-to-reversal | Censor-aware concordance with shorter reversal time | Horizon reversal incidence by quintile | Fixed plus forward interval | Higher propensity -> greater/nearer reversal | General survival support | Session/gap, perturbation class | Standard rule with direction adjusted for shorter time |
| Perturbation magnitude | Larger disturbance means larger transition | Maximum absolute raw-close displacement and slope change | Spearman magnitude vs realized transition magnitude | Horizon ordering and gap-separated results | 1/5/15/30/60 | Positive | General policy | Session/gap, class | Standard rule |
| Perturbation class | Class describes disturbance kind | Continuation/weakening/reversal/ambiguity geometry | Pre-registered class contrasts below | Class frequencies and transition matrix | 5/15/30 and forward interval | Distinguishable expected geometry | Per-class block support; rare -> inconclusive | Session/gap, magnitude | Categorical contract rule below |
| Observation half-life | Larger half-life means longer state relevance | $T_{valid}$ | Censor-aware concordance half-life vs survival | Validity at 0.5x/1x/2x; floor/ceiling strata | Adaptive observation HL | Positive ordering, not equality | Separate floor/ceiling; censoring | Session/gap, class | Standard rule |
| Forward half-life | Longer forward relevance means longer useful state | $T_{valid}$ and compatible path error | Concordance forward HL vs survival | Error at 0.5x/1x/2x | Adaptive forward HL | Positive survival; lower compatible error | General policy | Session/gap, uncertainty | Standard rule |
| Forward interval | Longer proposed interval means longer validity | $T_{valid}$ and compatible path error | Concordance interval vs survival | Error at 0.5x/1x/2x; emitted range diagnostic | Adaptive forward interval | Positive survival/discrimination | General policy | Session/gap, uncertainty | Standard rule; preserve range warning |

## 23. Perturbation-Class Evidence Contract

Expected realized geometry derives from the frozen semantic addendum:

- `NONE`: lower immediate realized transition magnitude than material classes; no directional profitability claim.
- `REINFORCING`: greater aligned progress/continuation and longer compatibility than `CONTRADICTING`/`REVERSING`.
- `CONTRADICTING`: more weakening and shorter compatibility than `REINFORCING`, without requiring every case to reverse.
- `REVERSING`: greater reversal incidence and shorter time-to-reversal than `REINFORCING`; reversal has semantic precedence.
- `STRUCTURAL/UNKNOWN`: greater ambiguous/data-structural incidence; no directional ordering requirement.

Primary contrasts are reinforcing versus contradicting on weakening/compatibility and reinforcing versus reversing on reversal/time-to-reversal. `NONE` magnitude and structural ambiguity are required secondary subclaims. `EMPIRICALLY_SUPPORTED` requires adequate support for both primary contrasts and expected intervals excluding null; mixed or limited subclaims yield partial; opposite decisive primary contrast yields unsupported; insufficient class support yields inconclusive. Equal class frequency is never required.

## 24. Half-Life Evidence Contract

Half-life is a temporal calibration claim, not an exact expiration forecast. Primary evidence is positive censor-aware concordance between emitted half-life and $T_{valid}$. Secondary evidence compares validity survival at 0.5x, 1.0x, and 2.0x emitted half-life.

Report observations at exact configured floor and ceiling separately; do not interpret those masses as ordinary interior calibration. Do not require realized survival to equal emitted half-life.

## 25. Forward-Interval Evidence Contract

Primary question:

> Does a larger emitted forward interval correspond to longer realized state validity?

Primary statistic is censor-aware concordance between emitted interval and $T_{valid}$. Secondary scores are compatible path error and continuation at 0.5x, 1.0x, and 2.0x interval.

`FORWARD_INTERVAL_RANGE_WARNING` is mandatory diagnostic context. If the emitted range is too compressed for adequate discrimination, classify interval validity `INCONCLUSIVE` or `UNSUPPORTED` according to support/effect rules. Never widen or retune the range during Stage 2.
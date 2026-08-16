# D01 Stage 2 Scoring Clarification v0.2.1 Consistency Review

## 1. Review Status

**Reviewed addendum:** `D01_STAGE_2_SCORING_CLARIFICATION_ADDENDUM_V0_2_1.md`  
**Implementation-facing extract:** `D01_STAGE_2_SCORING_CLARIFICATION_SPEC_V0_2_1.md`  
**Parent freeze:** `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2_FREEZE.json`  
**Review type:** scientific and experimental consistency, no implementation or historical execution

## 2. Frozen Authorities Compared

- `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`
- `D01_STAGE_2_REALIZED_STATE_OBSERVER_SPEC_V0_2.md`
- `D01_STAGE_2_EVIDENCE_CONTRACTS_V0_2.md`
- `D01_STAGE_2_SCORING_SPEC_V0_2.md`
- `D01_STAGE_2_INPUT_MAPPING_SPEC_V0_2.md`
- `D01_STAGE_2_CAUSAL_REPLAY_PROTOCOL_V0_2.md`
- `D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS.md`
- `D01_STAGE_2_IMPLEMENTATION_DESIGN_AMBIGUITY.md`

All parent hashes were verified before review. No parent authority was modified.

## 3. Scope Check

The addendum resolves only:

1. realized ambiguity-index aggregation and uncertainty primary statistic;
2. state/kinematics primary statistic, horizon, and null;
3. perturbation transition-magnitude scalar, horizon, and null;
4. perturbation-class co-primary effects and classification adjudication;
5. exact/right/interval-censored concordance comparability, orientation, and nulls.

It does not change input mapping, observer geometry, direction claim, realized categories, warm-up, horizon sets, session/gap strata, reserve boundary, support thresholds, bootstrap parameters, replay architecture, or D01.

**Result: PASS**

## 4. Realized Ambiguity Index

The parent evidence contract identifies exactly three ambiguity components: $1-E$, normalized deviation, and ambiguous incidence. The addendum bounds only the unbounded deviation using $D/(1+D)$ and combines all three with equal weights.

The formula is deterministic, bounded, monotone in each ambiguity component, parameter-free, and sign/mirror invariant. Unavailable components make the scalar unavailable rather than imputed. Spearman uncertainty association and null zero match the parent expected positive relationship and four-level classification framework.

No conflict exists with observer geometry or uncertainty semantics.

**Result: PASS**

## 5. State/Kinematics Concordance

The parent contract requires sign/geometry concordance between DMO direction and realized slope/progress. The addendum selects the realized slope sign for the primary directional statistic and retains endpoint progress, acceleration/curvature, efficiency, and deviation as secondary geometry diagnostics.

The 15-minute horizon is already in the frozen fixed set. Excluding zero-direction/zero-slope anchors is consistent with the parent rule that zero-direction anchors are directionally inconclusive. $C_{15}-0.5$ supplies the previously missing primary effect and null without changing the observer.

This is a state-geometry concordance measure and not a trading decision metric.

**Result: PASS**

## 6. Perturbation Transition Magnitude

The parent contract requires a scalar derived from independent raw-close displacement and slope change. $\sqrt{y^2+(hb)^2}$ combines two dimensionless horizon-scale displacement components with equal Euclidean geometry and no learned weights.

The formula is nonnegative and invariant under simultaneous sign mirroring. The 15-minute primary horizon is pre-registered. Spearman correlation and null zero match the frozen expected positive association.

No D01 perturbation output enters the future observable.

**Result: PASS**

## 7. Perturbation-Class Contrasts

The parent design already identifies reinforcing-versus-contradicting weakening/compatibility and reinforcing-versus-reversing reversal/time-to-reversal as primary class contrasts. The addendum avoids an arbitrary composite by selecting one categorical incidence outcome for each co-primary contrast at the pre-registered 15-minute horizon.

The expected signs derive directly from frozen class semantics. Requiring both contrasts for empirical support preserves the parent multi-contrast requirement. Rare classes remain inconclusive; equal class frequency and profitability remain irrelevant. `NONE` and `STRUCTURAL/UNKNOWN` stay required secondary subclaims.

No conflict exists with perturbation magnitude/type separation or reversal precedence.

**Result: PASS**

## 8. Censor-Aware Concordance

The addendum preserves exact, right, and interval censor states without midpoint imputation. Pair ordering is used only when exact or interval bounds make temporal ordering certain. Overlapping/touching uncertain intervals and two right-censored anchors are noncomparable.

This is consistent with the parent requirement to retain interval information and mark evidence inconclusive when support becomes inadequate. The orientation rule preserves positive expected effects for duration variables and reversal propensity. Null $C=0.5$ is already named for persistence and is consistently extended to all frozen duration contracts.

No censor type is silently converted, and reserve-boundary right censoring remains intact.

**Result: PASS**

## 9. Causality

Every clarified outcome uses only future raw-close observer geometry after an immutable anchor DMO. No future D01 state, fitted threshold, learned weight, historical optimization, or reserve value enters a score.

Canonical replay remains separate from scoring, so future data may score but cannot create a past state.

**Result: PASS**

## 10. Sign/Mirror Invariance

- $1-E$, normalized deviation, and ambiguous incidence are mirror invariant.
- State concordance depends on the product $d_tb_t$ and is mirror invariant when both directional coordinates reverse.
- Transition magnitude squares both directional components.
- Weakening/reversal categories inherit the frozen observer's mirror invariance.
- Duration concordance uses ordering rather than coordinate sign.

**Result: PASS**

## 11. Horizon Consistency

The addendum adds no horizon. It selects 15 minutes from the frozen 1/5/15/30/60 set only where the parent contract lacked one primary fixed horizon. Adaptive 0.5x/1.0x/2.0x coordinates remain unchanged.

**Result: PASS**

## 12. Support and Bootstrap Consistency

The addendum preserves:

- 1,800 elapsed-minute support blocks;
- adequate/limited/insufficient thresholds of 30 and 10 blocks;
- 1,800-minute chronological moving blocks;
- 2,000 deterministic replicates;
- two-sided 95% percentile intervals;
- seed derivation from the Stage 2 freeze identity.

Anchor records retain censor information and block identity during resampling. No IID uncertainty is introduced.

**Result: PASS**

## 13. Four-Level Classification Consistency

All clarified scalar effects use the parent four-level rules with explicit nulls. The class dimension's co-primary adjudication is a necessary specialization of the parent requirement that both primary contrasts be supported; it does not weaken support or interval requirements.

No global scientific PASS count or p-value criterion is introduced.

**Result: PASS**

## 14. Reserve and Data Policy

The addendum changes no dataset identity, partition, censor boundary, reserve hard stop, input mapping, or execution status. Primary outcomes and reserve observation values were not inspected.

**Result: PASS**

## 15. Canonical Clarification Extract

The implementation-facing spec reproduces the operative addendum sections for ambiguity, state concordance, transition magnitude, class contrasts, censor-aware concordance, horizons, and nulls. It declares the addendum controlling in any conflict and creates no independent scientific authority.

**Result: PASS**

## 16. Conflict Review

No conflict was found in:

- point-in-time causality;
- realized raw-close geometry;
- sign/mirror invariance;
- fixed or adaptive horizons;
- censoring and reserve boundary enforcement;
- support thresholds;
- moving-block bootstrap;
- multiplicity policy;
- four-level classification;
- perturbation magnitude/class semantics;
- canonical replay separation.

No silent repair or reinterpretation was required.

## 17. Final Decision

**DESIGN CONSISTENCY: PASS**

The scoring clarification addendum v0.2.1 is suitable for formal freeze. Stage 2 remains unimplemented and historical replay remains not started.
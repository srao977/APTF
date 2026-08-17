# D04 Deterministic Capturability Design v0.2

## 1. Purpose

Define the missing deterministic base-capturability mathematics for frozen D02 ReturnShape v0.2 and the existing `d04_trading_envelope` `CapturabilityModel` plug-in. This is design only: no implementation, replay, tuning, or freeze.

## 2. Authority

System authority v0.2, frozen D01/pre-Stage-3 authority, and frozen D02 design govern. Verified D02 freeze SHA256: `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`; all 14 referenced artifacts/authorities passed byte/hash checks. Existing D04 physical design, code, configuration, tests, and preservation artifacts define the integration target.

## 3. Original D04 capturability intent

Capturability is the present realizability of a supplied ReturnShape under the active causal envelope. It is not market prediction, expected return, profit probability, attractiveness, or a trade recommendation. Preserve:

$$
C_i(t)=H_i(t)\,B_i(t)\,G_i(t),
$$

where $H$ is hard eligibility/safety, $B$ is base shape capturability, and $G$ is the preserved feasibility bottleneck. For an eligible shape, $H=1$ and the original conceptual form remains $C=B\,G$.

## 4. Why V0 was provisional

V0/V0_2 used an experimentally weighted sum of synthetic `shape_quality`, `forward_support`, `magnitude_score`, `persistence_score`, inverse uncertainty/risk/decay, an equal blend with a soft context average, and an expected-lifetime ratio. Frozen D02 retires five of those scalar concepts and corrects temporal/reversal semantics. The weights and 30-second target were explicitly scaffolding, not authority.

## 5. Frozen D02 input

D04 receives all 17 canonical fields and validates the full seven-coordinate FMO path. Capturability mathematics uses:

- geometry: `terminal_displacement`, `maximum_absolute_displacement`;
- structure: `strength`, `coherence`, `persistence`;
- risk/degradation: `uncertainty`, `reversal_propensity`.

Lifecycle uses `entity_id`, `model_time`, and `projection_interval`. Remaining fields are retained for identity, provenance, validation, diagnostics, and future explicitly reviewed D04 use. No hidden score exists.

## 6. Capturability definition

Base capturability is the conjunction of:

1. a non-flat D01 projected path that ends consistently with its maximum excursion;
2. supported/coherent/persistent current D01 structure;
3. low current uncertainty and reversal propensity.

Operational feasibility is separate and cannot be compensated by shape quality.

## 7. Feasibility gate

Preserve existing V0_2:

$$
G=\min(g_1,\ldots,g_{10}),\qquad G\in[0,1],
$$

over `liquidity_quality`, `spread_quality`, `latency_quality`, `execution_feasibility`, `capital_available`, `portfolio_capacity`, `position_capacity`, `risk_capacity`, `broker_health`, and `data_integrity`.

Preserve gate warning threshold `0.50`, `FEASIBILITY_GATE_LOW`, and existing dimension-specific gate reason mappings. D04Context owns these causal values. `market_eligible` and critical `data_integrity` remain hard safety conditions in $H$.

## 8. Base capturability

Define:

$$
B=Q_G\,Q_S\,Q_R.
$$

This hierarchical product is parameter-free and strongly non-compensatory: geometric opportunity, structure, and risk quality are simultaneous requirements. No family can be fully offset by another.

## 9. Geometry quality

Let $D$ be signed terminal displacement and $M$ maximum absolute displacement.

$$
Q_G=\begin{cases}
0,&M=0,\\
\dfrac{|D|}{M},&M>0.
\end{cases}
$$

Frozen D02 guarantees $0\le |D|\le M$, hence $Q_G\in[0,1]$. It is scale-free endpoint efficiency: whether the projected path ends near its greatest excursion. It does not measure absolute profit or realized correctness. No non-arbitrary absolute-magnitude scale exists in frozen D02, so absolute magnitude is deliberately omitted from $B$ and remains available diagnostically.

## 10. Structural quality

For strength $s$, coherence $c$, and persistence $p$:

$$
Q_S=(s c p)^{1/3}.
$$

The unweighted geometric mean treats all three bounded structural coordinates equally without fitted weights and prevents one excellent coordinate from fully compensating for a zero coordinate.

`state_support_ratio` is omitted from $B$: it is derived from strength, persistence, uncertainty, and reversal propensity. Including a transform such as $r/(1+r)$ alongside those coordinates would double count the same evidence. The natural ratio remains an output diagnostic available to D04.

## 11. Risk quality

For uncertainty $u$ and reversal propensity $r$:

$$
Q_R=\sqrt{(1-u)(1-r)}.
$$

This is an unweighted geometric mean of two bounded quality complements. It is not a probability or calibrated confidence. It is monotone non-increasing in uncertainty and reversal propensity and reaches zero if either quality complement reaches zero.

## 12. Temporal quality — explicitly omitted

No soft temporal factor appears in $B$. `terminal_decay_factor` already affects projected strength, persistence, velocity, uncertainty, and reversal propensity in the frozen FMO; using both current/path-decayed semantics plus endpoint decay risks double counting. More importantly, projection validity is enforced as a hard lifecycle rule:

$$
\text{valid}\iff t_{eval}\le t_{model}+I_f.
$$

`terminal_decay_factor`, `forward_half_life`, and the full path remain diagnostics. No fake temporal component equal to one is emitted.

## 13. Aggregation

Aggregation is hierarchical multiplication:

$$
B=Q_G Q_S Q_R.
$$

Within $Q_S$ and $Q_R$, geometric means provide equal, parameter-free, partially non-compensatory treatment. Across families, product encodes jointly necessary conditions. Arithmetic weighting and the old soft envelope average are retired.

## 14. Final score

Define hard eligibility:

$$
H=\mathbf 1[\text{projection valid}]\,
\mathbf 1[\text{market eligible}]\,
\mathbf 1[\text{data integrity above critical threshold}]\,
\mathbf 1[\text{valid finite inputs}].
$$

Then:

$$
C=H\,B\,G.
$$

For hard-failure status, D04 reports $C=0$ and the corresponding safety reason. $B$ and raw $G$ may remain diagnostic if inputs are mathematically valid, but neither can make the event entry-eligible.

## 15. Mathematical properties

- Deterministic and causal: all variables are frozen D02 or current typed D04Context fields.
- Naturally bounded: $Q_G,Q_S,Q_R,B,G,H,C\in[0,1]$.
- Finite: valid inputs are finite; the only division has an explicit exact-zero branch.
- Monotonic: $B$ is non-decreasing in $Q_G,s,c,p$ and non-increasing in $u,r$.
- Parameter-free base: no weights, slopes, scales, thresholds, learned/fitted coefficients, or historical calibration.
- Defensive clamp: permitted only after computation to absorb floating-point roundoff; any material out-of-range value is invalid, not silently clipped.

## 16. Edge cases

| Case | Deterministic result |
|---|---|
| Flat path, excellent structure/context | $Q_G=B=C=0$; `ZERO_GEOMETRY` |
| Strong directional path, high uncertainty | Risk quality suppresses $B$ monotonically |
| Strong path, high reversal propensity | Risk quality suppresses $B$ monotonically |
| Strong shape, poor feasibility | $B$ may be high; $G$ suppresses $C$ |
| Weak/degenerate geometry, excellent envelope | Geometry suppresses $B$; context cannot compensate |
| High structure, zero geometry | $C=0$ |
| Low structure, coherent geometry | $Q_S$ suppresses $B$ |
| Valid shape with very low terminal decay | No direct soft penalty; lifecycle and already-projected coordinates govern |
| Stale shape | $H=0$, $C=0$, no new candidate |
| Market ineligible | $H=0$, $C=0$, immediate safety closure |
| Data at/below critical threshold | $H=0$, $C=0$, immediate safety closure |
| One hard feasibility bottleneck | $G$ equals bottleneck; $C=B G$ |

## 17. Reason codes

Preserve: `UNCERTAINTY_HIGH` at existing threshold `0.50`; rename `REVERSAL_RISK_HIGH` to `REVERSAL_PROPENSITY_HIGH` at existing threshold `0.50`; preserve feasibility warnings and dimension codes; preserve `MARKET_INELIGIBLE` and `DATA_INVALID`.

Add exact-condition codes: `ZERO_GEOMETRY`, `SHAPE_STALE`, `INVALID_RETURNSHAPE`, and `NO_VALID_RETURNSHAPE`.

Remove `SHAPE_QUALITY_LOW`, `FORWARD_SUPPORT_LOW`, `LIFETIME_SHORT`, and input-driven `SHAPE_EXPIRED`. No new structural/magnitude thresholds are introduced.

## 18. Output components

Emit exactly: `geometry_quality`, `structural_quality`, `risk_quality`, `base_capturability_score`, `feasibility_gate_score`, `capturability_score`, `gate_dimension_values`, `hard_eligibility`, `safety_status`, and `reason_codes`. Do not emit `shape_component`, `envelope_component`, or `lifetime_component` under misleading legacy semantics.

## 19. Lifecycle interaction

Newer same-entity shape supersedes immediately. Endpoint is inclusive; stale only afterward. A stale shape cannot create a new candidate. Detailed stale behavior for already-open envelope state remains a D04 lifecycle design issue outside the formula; hard eligibility is nevertheless defined.

## 20. Aperture/hysteresis compatibility

$C\in[0,1]$, so the preserved `ApertureModel` and `HysteresisController` interfaces remain compatible. Preserve their structures. Existing threshold numeric values `0.75/0.55` are not validated for the new score and require analytic/synthetic component-level revalidation before implementation, never outcome tuning.

## 21. Continuous/event-driven behavior

Evaluate on every new ReturnShape and on causal context events using the latest non-superseded, projection-valid shape. No window cadence or replay-specific behavior is introduced.

## 22. Replay/feed equivalence

Identical ordered ReturnShape/context events, initial D04 state, and fixed approved configuration produce identical components, scores, states, and events whether supplied by replay or future feeds.

## 23. Testing requirements

Implement the synthetic vectors in `D04_CAPTURABILITY_DETERMINISTIC_TEST_VECTORS_V0_2.json`; add property tests for bounds/monotonicity/zero branches; preserve gate/aperture/hysteresis regression intent; test stale and hard-failure precedence; verify formula schema lineage; retain all existing tests until adapted/replaced under the preservation plan.

## 24. Prohibited behavior

No learned/fitted weights, arbitrary scale, historical/reserve calibration, absolute-magnitude clipping, support-ratio duplication, temporal double counting, legacy meta-score recreation, future/observer/outcome input, probability claims, or trading decision.

## 25. Remaining open issues

Capturability mathematics has zero remaining scientific ambiguity. Separate D04 modernization issues remain: detailed stale-state response, candidate-ID protocol, final D04Context/output schema, and numeric hysteresis-threshold revalidation against synthetic formula behavior.

## 26. Freeze readiness

**D04 DETERMINISTIC CAPTURABILITY DESIGN: PASS.** The formula is fully determined and ready for human review. Do not implement or freeze it in this task.

## Integration acceptance answer

**YES — with exact modernization delta.** Frozen D02 ReturnShape v0.2 can enter the existing `d04_trading_envelope` by replacing the legacy ReturnShape model, implementing this formula inside the existing `CapturabilityModel` plug-in, adapting typed configuration/result fields, and updating lifecycle/identity/fixtures. Feasibility, aperture, hysteresis, state machine, event-driven loop, event bus, and audit mechanisms remain preserved.

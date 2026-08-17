# D04 Trading Envelope Modernization Design v0.2

## 1. Purpose

Modernize the existing D04 input/output boundary to consume frozen D02 ReturnShape v0.2 while preserving validated control machinery. This is design only, not implementation or freeze.

## 2. Existing D04 asset status

`d04_trading_envelope` is an executable physical prototype with 26 Python modules including package initializers, seven test files, seven deterministic scenarios, configuration, CLI, audit runtime, and 23/23 passing tests. It has no formal freeze/acceptance/hash manifest. Its scoring math is explicitly placeholder/experimental.

## 3. Authority hierarchy

System authority v0.2 governs frozen D01, frozen D02, existing D04 design/code/test evidence, and this modernization. Existing D04 authority remains historical/implementation evidence but cannot override frozen D02.

## 4. Preserved D04 architecture

Preserve D04 ownership of capturability, feasibility, aperture, hysteresis, envelope state, lifecycle safety, candidate formation/identity, and envelope events. Preserve modular plug-in boundaries and ordered processing. D04 does not infer an alternate market state or commit trades.

## 5. Frozen D02 input authority

Input ReturnShape is exactly the 17-field schema frozen by `D02_RETURNSHAPE_DESIGN_V0_2_FREEZE.json`, SHA256 `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`. Canonical identity is `(entity_id, model_time)`. Full FMO samples remain available.

## 6. Existing execution flow

Current flow is validation/version guard -> safety override -> shape/envelope/lifetime scoring -> feasibility gate -> hysteresis -> aperture -> transitions/candidate/continuation -> evaluation/events/audit. Exact formulas are recorded in `D04_EXISTING_EXECUTION_TRACE_V0_2.md`.

## 7. Modernized execution flow

```text
ReturnShape + D04Context event
  -> strict input/context validation
  -> identify latest shape by entity and model_time
  -> apply newer-shape supersession or context-only reevaluation
  -> derive projection-valid/stale lifecycle state
  -> safety gates
  -> deterministic geometric/state base capturability
  -> preserved context contribution and minimum feasibility gate
  -> hierarchical product base aggregation
  -> preserved hysteresis
  -> preserved aperture
  -> envelope transition/events
  -> optional D04-owned CandidateEnvelope on qualification
  -> audit/output for D03
```

## 8. Input contract

`D04Input_t = (ReturnShape_t, D04Context_t)`. ReturnShape is required and immutable. D04 validates all 17 fields, seven nested coordinates, deterministic views, identity, finite ranges, and projection consistency. Candidate, execution, outcome, observer, and reserve values are prohibited from ReturnShape.

## 9. Context contract

Modern `D04Context` has exactly 13 required typed fields. Remove untyped metadata.

| Field | Type/range | Ownership and purpose | Consumer |
|---|---|---|---|
| `evaluation_time` | finite float; timestamp seconds | D04 causal operational event time | Projection validity, output/events |
| `market_eligible` | bool | D04 causal operational eligibility | Hard eligibility $H$ |
| `data_integrity` | float `[0,1]` | D04 causal operational integrity | Hard eligibility and gate |
| `clock_event_quality` | float `[0,1]` | D04 causal operational synchronization quality | Diagnostic, not score-active |
| `liquidity_quality` | float `[0,1]` | D04 execution feasibility | Minimum gate |
| `spread_quality` | float `[0,1]` | D04 execution feasibility | Minimum gate |
| `latency_quality` | float `[0,1]` | D04 execution feasibility | Minimum gate |
| `execution_feasibility` | float `[0,1]` | D04 execution feasibility | Minimum gate |
| `broker_health` | float `[0,1]` | D04 execution feasibility | Minimum gate |
| `capital_available` | float `[0,1]` | D04 portfolio capacity | Minimum gate |
| `portfolio_capacity` | float `[0,1]` | D04 portfolio capacity | Minimum gate |
| `position_capacity` | float `[0,1]` | D04 portfolio capacity constraint, not a position decision | Minimum gate |
| `risk_capacity` | float `[0,1]` | D04 portfolio capacity | Minimum gate |

All fields are required, causal at evaluation, and identical in replay/feed operation. No typed field moves to D03 because each constrains present capturability; D03 still owns committed position/order/action state.

Classification counts:

- causal operational: 4;
- execution feasibility: 5;
- portfolio capacity: 4;
- moved to D03: 0;
- market-state duplicates: none found;
- future/prohibited: none in typed fields;
- obsolete: untyped metadata (1 retired legacy field).

## 10. Capturability semantics

Capturability remains realizability of the supplied projected shape under current causal envelope conditions. It is not market prediction or generic attractiveness. The modern deterministic base is defined by `D04_CAPTURABILITY_DETERMINISTIC_DESIGN_V0_2.md`; context feasibility and hard temporal validity remain separate.

## 11. Shape-component modernization

Retire the old seven-value weighted shape component. Replace it through the existing plug-in with the approved parameter-free product of endpoint efficiency, structural geometric mean, and risk-quality geometric mean. Full FMO remains accessible and no retired meta-score is recreated.

## 12. Magnitude handling

Use scale-free endpoint efficiency `abs(terminal_displacement) / maximum_absolute_displacement`, with exact zero-path handling. Absolute displacement remains diagnostic because frozen D02 supplies no non-arbitrary absolute scale.

## 13. Support handling

Retain natural unbounded `state_support_ratio` diagnostically but omit it from the scalar base to avoid double counting the strength, persistence, uncertainty, and reversal coordinates already used explicitly.

## 14. Decay handling

Retain decay coordinates diagnostically and omit a soft temporal factor from base capturability. Frozen FMO already expresses decay, and hard projection staleness governs validity; adding endpoint decay would double count time.

## 15. Reversal handling

`reversal_propensity` is bounded and non-probabilistic. Existing inverse treatment `1-reversal_propensity` is a transparent D04 penalty transform and can be preserved conceptually. Reason code names must say propensity, not probability/risk. Path-level propensity remains available if later explicitly selected.

## 16. Coherence, persistence, uncertainty handling

All are bounded D01 coordinates. Existing direct persistence and inverse uncertainty treatments are semantically aligned. Coherence can supply explicit agreement/regularity without a `shape_quality` meta-score. Whether/how these enter one aggregate, including weights, is part of the open base formula.

## 17. Aperture

Preserve `ApertureModel` and V0 exponential smoothing unchanged. It consumes only final bounded capturability. The upstream score changes, so expected numeric trajectories require regression review, but aperture mathematics does not.

## 18. Feasibility

Preserve causal context dimensions, minimum gate, dimension values, warning threshold mechanism, and reason-code mapping. The exact experimental envelope weighted component and 0.5 base blend are not frozen and must be reviewed with the base formula.

## 19. Hysteresis

Preserve states, threshold ordering, persistence counters, reset, and recovery unchanged. Threshold numeric values cannot be claimed valid for a newly scaled capturability score until the modern score range/distribution is analytically defined; do not tune them from outcomes.

## 20. Lifecycle/staleness

For each entity, newer `model_time` supersedes older immediately. Supersession invalidates any candidate sourced from the old shape, emits `SHAPE_SUPERSEDED` and `CANDIDATE_INVALIDATED` when applicable, then evaluates the new valid shape without forcing CLOSED solely because of supersession.

Same-shape context reevaluation is allowed. Validity is inclusive through `model_time + projection_interval`; stale only afterward. Staleness bypasses ordinary close persistence:

- `CLOSED`: remain CLOSED;
- `OPENING`, `OPEN`, or `CLOSING`: force CLOSED immediately;
- set aperture exactly to `0.0` without exponential smoothing;
- reset both hysteresis counters;
- invalidate any current candidate;
- emit `SHAPE_STALE`, plus `ENVELOPE_CLOSED` when prior state was not CLOSED, plus `CANDIDATE_INVALIDATED` when applicable;
- never emit a D03 exit/hold/reduce decision.

After stale closure, a new valid shape starts from CLOSED and must satisfy ordinary opening persistence. A context-only event first checks the latest shape's validity and applies this response if stale.

## 21. Candidate identity

D04 owns candidate formation. Evolve the existing `OpportunityEvent` concept into a minimal `CandidateEnvelope`; do not create a parallel candidate engine.

Candidate identity is:

```text
D04C|percent_encode_utf8(entity_id)|format17g(source_model_time)|format17g(qualified_at)
```

`percent_encode_utf8` uses uppercase percent-hex outside unreserved RFC 3986 characters. `format17g` is locale-independent binary64 formatting with 17 significant decimal digits. Identity is deterministic, replay-stable, auditable, contains no wall-clock creation time, and never enters capturability math.

CandidateEnvelope fields are `candidate_id`, `entity_id`, `source_return_shape_model_time`, `qualified_at`, and `status` (`QUALIFIED` or `INVALIDATED`). Create it when a valid shape's post-hysteresis envelope is OPEN and no current candidate exists for that source shape. Supersession or safety closure invalidates it. `candidate_rr` remains prohibited.

## 22. Envelope state machine

Preserve CLOSED/OPENING/OPEN/CLOSING and score-driven transitions. Safety can still force CLOSED. D04 state describes envelope capturability, not position or committed trade state.

## 23. Events

Preserve factual input, capturability, aperture, envelope-transition, candidate, and safety events. Canonical values are `RETURN_SHAPE_ACCEPTED`, `CONTEXT_REEVALUATED`, `CAPTURABILITY_EVALUATED`, `APERTURE_UPDATED`, `ENVELOPE_OPENING`, `ENVELOPE_OPENED`, `ENVELOPE_CLOSING`, `ENVELOPE_CLOSED`, `CANDIDATE_QUALIFIED`, `CANDIDATE_INVALIDATED`, `SHAPE_SUPERSEDED`, `SHAPE_STALE`, `MARKET_INELIGIBLE`, `DATA_INVALID`, `INVALID_RETURNSHAPE`, and `NO_VALID_RETURNSHAPE`.

Replace legacy ID/version payloads with entity/model-time and D04 candidate identity. Retire HOLD/REDUCE/MODIFY/EXIT commitment events from canonical D04 output; D03 owns those decisions.

## 24. Safety behavior

Preserve market-ineligible and invalid-data immediate safety closure. Replace input `active`/nonpositive lifetime with derived projection staleness. Every safety closure forces CLOSED, sets aperture to `0.0`, resets hysteresis, invalidates any candidate, and emits factual safety/closure events. Unknown/invalid canonical shape fails closed without imputation.

## 25. D03 output boundary

D04 emits exactly 23 top-level factual fields:

- identity/time (4): `evaluation_time`, `entity_id`, `return_shape_model_time`, `source_model_version`;
- capturability (7): `hard_eligibility`, `geometry_quality`, `structural_quality`, `risk_quality`, `base_capturability_score`, `feasibility_gate_score`, `capturability_score`;
- envelope state (4): `previous_envelope_state`, `new_envelope_state`, `aperture_before`, `aperture_after`;
- lifecycle/safety (4): `projection_valid`, `stale`, `safety_state`, `safety_reason`;
- candidate (1): optional `candidate_envelope` with five typed nested fields;
- diagnostics/events (3): `gate_dimension_values`, `reason_codes`, `events`.

D04 outputs no BUY/SELL/HOLD/ENTER/EXIT/REDUCE/REVERSE, local `position_open`, order state, position sizing, reward/risk decision, or trade recommendation. D03 receives factual state and owns action/control.

## 26. Continuous/event-driven operation

Evaluate every new ReturnShape and any causal context change against the latest projection-valid shape. No 15-minute scheduler, intra-window state, or inter-window state is introduced. Optional runtime sleeps remain presentation concerns only.

## 27. Replay/market-feed equivalence

Identical ordered ReturnShape/context events plus identical initial D04 state/configuration must emit identical evaluations, candidates, states, and events. No replay/live formula branch, future-outcome branch, profitability branch, or wall-clock scientific dependency is permitted.

## 28. Numerical behavior

Validate finite inputs, preserve natural units, never silently clip unbounded geometry/support, and clamp only quantities explicitly defined as bounded D04 scores. Deterministic iteration/order is required. Capturability formulas are fixed by the deterministic formula schema; hysteresis numeric thresholds require synthetic revalidation during implementation but do not reopen architecture.

## 29. Failure behavior

Malformed/inconsistent ReturnShape, noncausal entity time, invalid context, unknown fields, or nonfinite math fails closed with explicit reason. A context-only event without a latest valid shape cannot qualify a candidate. No stale, future, imputed, or hidden metadata value is accepted.

## 30. Configuration

Preserve runtime safety threshold, hysteresis structure, aperture alpha, gate mode/dimensions/warnings. Retire old shape weights and target lifetime unless rejustified. Modern capturability transforms, aggregation, scales, and associated thresholds require reviewed typed config only after open decisions close.

## 31. Preserved implementation

Preserve aperture, hysteresis, envelope states, minimum gate, event bus, scenario loader, ordered loop, audit mechanism, plug-in interfaces, safety principles, and most orchestration. See classification/delta artifacts for exact modules.

## 32. Required implementation changes

Future implementation changes: canonical ReturnShape model/adapter; final 13-field context; approved deterministic formula; typed config; entity/model-time state; safety-first staleness; deterministic CandidateEnvelope ID; final 23-field output/event/audit payloads; removal of local position commitments; fixture/CLI adaptation. No source change is authorized now.

## 33. Test preservation plan

Baseline is 23/23. Six tests should pass unchanged, 15 preserve intent with fixture adaptation, and two old interface tests become historical and require replacements. New schema, staleness, candidate, causality, and replay/feed equivalence tests are required.

## 34. Prohibited behavior

No independent market predictor, observer/outcome/reserve input, legacy meta-score recreation, reward/risk, trade decision, outcome-based tuning, silent normalization, hidden metadata, or replay-specific mathematics.

## 35. Open issues

Zero mathematical, representation, interface, protocol, lifecycle, ownership, or architecture issues remain. Implementation and test-construction work remains but does not block design freeze. `D04_MODERNIZATION_OPEN_ISSUES_V0_2.md` records the resolved ledger.

## 36. Implementation boundary

This design is eligible for freeze after schema and consistency validation. Freeze authorizes no source change; implementation requires a separate prompt.

# D04 Existing Execution Trace v0.2

## 1. Public boundary

The current primary entry point is:

```python
TradingEnvelope.process(return_shape: ReturnShape, context: EnvelopeContext) -> EnvelopeEvaluation
```

`RealtimeLoop.run()` supplies ordered synthetic observations. The CLI constructs all components from `config/default.yaml`.

## 2. Actual execution graph

```text
Scenario YAML
  -> load_scenario
  -> SyntheticGenerator
  -> Observation(ReturnShape, EnvelopeContext, scenario_time)
  -> RealtimeLoop.run
  -> TradingEnvelope.process
       1. capture previous state/aperture
       2. enforce same-shape increasing version
       3. append input-update events
       4. evaluate safety override
          - market ineligible
          - data integrity at/below critical threshold
          - inactive/nonpositive lifetime
       5a. safety: force zero capture, CLOSED, reset hysteresis, update aperture
       5b. normal: CapturabilityModel.evaluate
           a. shape weighted component
           b. envelope weighted component
           c. lifetime component
           d. base score
           e. V0_2 minimum feasibility gate
           f. final score and reasons
       6. HysteresisController.next_state(final score)
       7. ApertureModel.update(final score, state, prior aperture)
       8. map state transition event
       9. determine entry eligibility / qualified opportunity
      10. derive continuation signal from logical position flag
      11. return EnvelopeEvaluation
  -> publish Event objects
  -> AuditLogger JSONL
  -> console/summary
```

## 3. Existing formulas

Shape values:

```text
shape_quality
forward_support
magnitude_score
persistence_score
1 - uncertainty
1 - reversal_risk
1 - decay_score
```

With configured weights summing to one:

$$
S=\operatorname{clip}_{[0,1]}\left(\sum_k w_k x_k\right).
$$

Envelope values are eleven bounded context qualities, also weighted to one:

$$
E=\operatorname{clip}_{[0,1]}\left(\sum_j v_j c_j\right).
$$

Lifetime component:

$$
L=\operatorname{clip}_{[0,1]}\left(\frac{\text{expected_lifetime_seconds}}{\text{target_lifetime_seconds}}\right).
$$

Base and gated capturability:

$$
B=\operatorname{clip}_{[0,1]}((0.5S+0.5E)L),
$$

$$
G=\min(c_j: j\in\text{configured gate dimensions}),\qquad C=\operatorname{clip}_{[0,1]}(BG).
$$

Aperture:

$$
A_t=\operatorname{clip}_{[0,1]}(\alpha C_t+(1-\alpha)A_{t-1}).
$$

## 4. State and safety

The score-driven state machine is `CLOSED -> OPENING -> OPEN -> CLOSING -> CLOSED`, with recovery paths and independent open/close persistence counters. Safety overrides bypass ordinary close persistence, force `CLOSED`, reset hysteresis, and drive aperture toward zero.

## 5. Candidate and decision-adjacent behavior

On the first transition to `OPEN`, when no logical position is open, D04 emits `QUALIFIED_OPPORTUNITY` with legacy candidate/shape IDs. Optional config immediately sets a local `position_open` flag. `HOLD_ELIGIBLE`, `REDUCE_CANDIDATE`, and `EXIT_CANDIDATE` then derive from envelope state plus that flag. Under current system authority, candidate formation remains D04, but position ownership and committed continuation decisions belong to D03; this portion requires boundary modernization.

## 6. Event-driven status

Core processing is observation/event driven and contains no 15-minute cadence. Optional `RealtimeLoop` sleep uses scenario deltas only for presentation. With speed zero, identical ordered inputs produce deterministic state/event/score summaries. The scientific path therefore already supports dense or sparse event arrival and replay/feed equivalence.

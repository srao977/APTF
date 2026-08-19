# APTF Test 001 Row 10 Decision Causal Trace V0.1

Status: PASS / CODE-CAUSAL TRACE

## Backward Trace From Final Semantic Output

`NO_ACTION` appears in the complete E5 `PositionTransitionPlan` because:

1. Controller actual state was `FLAT` and D03 desired state was `FLAT`.
2. The frozen matrix key `(FLAT, FLAT)` maps to transition class `NO_CHANGE_FLAT` and ordered verbs `[NO_ACTION]`.
3. D03 transition intent was `NO_CHANGE`, so the plan is `NON_EXECUTABLE_NO_CHANGE` with `action_authorized=false`.

The actual position was `FLAT` because:

1. The unchanged real replay harness explicitly initialized `ActualPositionState(LONG, version=0, identity=INITIAL)` before data index 0.
2. Data indices 0-7 were processed only to establish prior causal state.
3. One authorized semantic-success advancement occurred in that warm-up, leaving harness-maintained `ActualPositionState(FLAT, version=1, identity=INITIAL)` immediately before target t.
4. This state is not broker sourced, not inferred from D03 desired state, and not internal controller memory.

D03 desired `FLAT` because:

1. Emergency flatten was false; system and trading were enabled, so R10/R20/R21 did not activate.
2. D04 safety was CLEAR, stale was false, and projection valid was true, so R30 did not activate.
3. D04 `new_envelope_state=CLOSED`, so R31 was the first applicable target rule.
4. R31 emitted desired `FLAT` with `primary_reason_code=ENVELOPE_CLOSED`.
5. Actual FLAT matched desired FLAT with no pending target, so T20 emitted `NO_CHANGE` and `POSITION_ALREADY_ALIGNED`.
6. Execution was available, so no authorization overlay activated.

D04 was CLOSED because:

1. Prior D04 state was CLOSED with aperture 0.2776088557247953 and zero open/close qualification counters.
2. Target capturability was 0.22050421416872243.
3. That score was below open threshold 0.75, so frozen hysteresis retained CLOSED.
4. No CandidateEnvelope was created because candidate qualification occurs only when state is OPEN.
5. Safety remained CLEAR and projection valid; closure here was the normal envelope-state result, not a safety closure.

Capturability 0.22050421416872243 came from:

- geometry quality = 1.0;
- structural quality = 0.6043625386410295;
- risk quality = 0.36485420599454843;
- base = geometry * structural * risk = 0.22050421416872243;
- feasibility gate = minimum of ten all-1.0 context dimensions = 1.0;
- hard eligibility = 1;
- final = hard * base * gate = 0.22050421416872243.

Those D04 inputs came from D02 ReturnShape:

- terminal displacement = +0.01978985584654247;
- maximum absolute displacement = 0.01978985584654247;
- path direction = UPWARD;
- strength = 0.8777636556469071;
- coherence = 0.4855782805501968;
- persistence = 0.5179117484872026;
- uncertainty = 0.3799587892055599;
- reversal propensity = 0.785306864585095.

UPWARD did not directly produce LONG. D04 had no qualified candidate because it was CLOSED, and D03 reached R31 before its candidate-direction rules R36/R40/R41.

D02 values came from D01:

- current level = -0.6571388532831072;
- terminal projected level = -0.6373489974365647;
- their difference = +0.01978985584654247;
- eight projected samples and DMO scores were copied/derived under the frozen builder.

D01 values arose from target t plus legitimate prior causal state:

- target close/price = 365.5;
- target volume = 4288.0;
- target quality = 1.0;
- prior adaptive reference = 366.0157352105078;
- prior adaptive scale = 0.7590324720175738;
- prior volume reference = 588.5134348690233;
- prior level/velocity = -0.6004159601978543 / -0.0035612763243195837;
- prior persistence/uncertainty and half-life state were recursively accumulated from data indices 0-7.

## Causal Conclusion

The final semantic output is a code-path consequence of target input, accumulated D01/D04 state, fixed integration context/configuration, and harness control state. It is not a post-hoc financial explanation and contains no future-price evidence.

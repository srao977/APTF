# APTF Test 010 Cockpit Control Architecture V0.1

**VISUAL/CONTROL ARCHITECTURE ONLY. NO LIVE OR PAPER EXECUTION.**

## Display

```text
PRICE ENGINE             VOLUME ENGINE
[GREEN/AMBER/RED]        [GREEN/AMBER/RED]

CONTROL
continuous metrics + concurrence/disagreement + INCONCLUSIVE

EXECUTION WINDOW
[BUY] [HOLD] [SELL]

AUTOPILOT
OFF / ARMED / ON

BROKER BOUNDARY
not implemented
```

Colors are not implemented and no thresholds are authorized. Future Price color candidates are continuous absolute P1/P2/J_P, state persistence, local P2 error estimate, condition number, and gap status. Future Volume color candidates are V_N, interval-15 dispersion/burst intensity/persistence, and V1/V2 observer-event persistence. Colors describe trajectory condition; GREEN is not BUY, AMBER is not HOLD, and RED is not SELL.

## Layer boundaries

Price Engine and Volume Engine remain independent. Control coordinates evidence without weighted mixing. BUY/HOLD/SELL remains the frozen downstream execution window. HOLD retains state-relative Test 007 semantics: preserve LONG or preserve FLAT.

## AutoPilot architecture

- OFF: human execution only.
- ARMED: execution may be prepared but not transmitted.
- ON: an independently authorized intent may be transmitted only if all future gates pass.

Prospective gate, not implemented:

```text
AutoPilot ON
AND Execution Window OPEN
AND valid Control execution intent
AND valid Position transition
AND broker available
-> order may be transmitted
```

AutoPilot cannot alter Price/Volume mathematics, local dynamics, RK state, or Control evidence. No AutoPilot state machine, broker adapter, or order exists in Test 010.

## Session behavior

- Observed source session: local 04:00 through available after-hours.
- Execution window: authoritative `is_regular_session=true`, local `[09:30,16:00)`.
- Session close: last observed row for local date; engine and Control states persist as evidence.
- Next session: preserve prior final state and elapsed gap, admit the next observed Price/Volume, prohibit blind integration through the gap, and re-estimate both engines.

Session close resets neither engine and never forces GREEN.
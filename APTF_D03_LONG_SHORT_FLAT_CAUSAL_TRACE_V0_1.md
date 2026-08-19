# APTF D03 LONG / SHORT / FLAT Causal Trace V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## LONG

LONG has two frozen sources.

### Ordinary enabled directional rule R40

$$
\neg emergency \land system\_enabled \land trading\_enabled
\land safety=CLEAR \land \neg stale \land projection\_valid
\land envelope=OPEN \land candidate\ne null
\land candidate.status=QUALIFIED
\land candidate.path\_direction=UPWARD
\Rightarrow desired=LONG.
$$

Every conjunction is required; together they are sufficient for R40 because earlier rules are excluded. Any higher-priority control/safety condition vetoes R40. Actual position, pending state, execution availability, scores, aperture, and events do not alter the LONG target after these conditions hold.

### Disabled preservation R20/R21

If system or trading is disabled and actual position is LONG, desired is LONG regardless of D04. This is control preservation, not a fresh analytical LONG.

## SHORT

SHORT is symmetric in the ordinary branch and also has disabled preservation.

### Ordinary enabled directional rule R41

The R40 conjunction applies with `candidate.path_direction=DOWNWARD`, producing SHORT. No additional asymmetric condition exists.

### Disabled preservation

If system or trading is disabled and actual position is SHORT, desired is SHORT regardless of D04.

## FLAT condition classes

| # | Condition | Component/source | Reason | Analytical FLAT? | Suppressed direction? | Control FLAT? | D02 may still be directional? |
|---:|---|---|---|---|---|---|---|
| 1 | emergency flatten | D03 control | `EMERGENCY_FLATTEN` | NO | overrides any | YES | YES |
| 2 | system disabled + actual FLAT | D03 control/actual | `SYSTEM_DISABLED` | NO | D04 ignored | YES | YES |
| 3 | trading disabled + actual FLAT | D03 control/actual | `TRADING_DISABLED` | NO | D04 ignored | YES | YES |
| 4 | D04 safety closed | D04 validity | `D04_SAFETY_CLOSED` | NO | YES | safety target | YES |
| 5 | D04 stale | D04 lifecycle | `D04_SAFETY_CLOSED` + detail | NO | YES | safety target | YES |
| 6 | D04 projection invalid | D04 lifecycle | `D04_SAFETY_CLOSED` | NO | YES | safety target | YES |
| 7 | envelope CLOSED | D04 state | `ENVELOPE_CLOSED` | NO | YES | NO | YES |
| 8 | envelope OPENING | D04 hysteresis | `ENVELOPE_NOT_QUALIFIED` | NO | YES/delayed | NO | YES |
| 9 | envelope CLOSING | D04 hysteresis | `ENVELOPE_CLOSING` | NO | candidate ceasing | NO | YES |
| 10 | OPEN, no candidate | D04 candidate | `NO_VALID_CANDIDATE` | NO | YES | NO | YES |
| 11 | OPEN, invalidated candidate | D04 candidate | `CANDIDATE_INVALIDATED` | NO | YES | NO | YES |
| 12 | OPEN, QUALIFIED, direction FLAT | D02 direction via D04 | `CANDIDATE_NON_DIRECTIONAL` | YES | NO | NO | NO; D02 is FLAT |

A defensive R34 fallback also returns FLAT/`NO_VALID_CANDIDATE` if no named branch returns. It is an implementation fallback, not a default at initialization and not an error recovery from invalid schema.

Invalid schema or `control_state_valid=false` produces no DecisionRecord, not FLAT.

## Actual, pending, and execution behavior

- Enabled ordinary target: actual position does not change LONG/SHORT/FLAT; it changes transition intent only.
- Disabled target: desired equals actual, so identical D04 input can yield different desired states.
- Pending target: never changes desired; it changes RETARGET versus NO_CHANGE.
- Execution unavailable: never changes desired; it changes actionable transition intent to BLOCKED.

## Minimum analytical content currently present

To express direction before broker execution, current components already contain:

- `ReturnShape.path_direction`;
- D04 candidate qualification status/existence;
- candidate `path_direction` when qualified.

The minimal sign information is `path_direction`. The current frozen D03 target additionally requires the D04 safety/state/candidate qualification facts and higher-priority D03 controls.

# APTF Fixed-Context Experiment Decision Point V0.1

Status: EXPERIMENTAL / DIAGNOSTIC. NOT FROZEN PRODUCTION AUTHORITY.

## Classification

**RESULT C: TWO-ROW PROOF FAILED.**

Exact first blocking boundary: **D04 -> D03**.

## Evidence

The fixed D04 context is legitimate for the controlled scenario:

- 11 fixed fields have legal, mechanically non-restrictive values.
- `evaluation_time` is current-row-derived.
- `data_integrity` is causally derived by the existing mapper.
- frozen critical threshold `0.2` and all other D04 defaults were unchanged.
- real D01, D02, and D04 executed on genuine sequential observations.

D03 could not be invoked legitimately. Its frozen `DecisionContext` requires an `actual_position_state` and additional position lineage, pending transition, execution availability, and system/trading/control state. The experiment explicitly excludes ActualPosition and permits artificial constants only for D04.

Supplying FLAT or any other position/control constants would add a second uncontrolled context not authorized by the experiment. No such values were invented.

## Consequences

- No D03 desired-position result exists for either target.
- The two-row success gate fails.
- The 100-row cycle was not run.
- The small-cycle CSV was not created.
- Position Controller, action verbs, broker simulation, and P&L were not used.

## Separate D04 observation

Both real D02 target shapes were UPWARD. Under frozen permissive D04 context, D04 remained CLOSED because the final capturability scores (`0.4814590392445292` and `0.3605075262704571`) were below the frozen open threshold `0.75`. This outcome was recorded without tuning.

## Human decision required

A future D03 desired-position experiment must explicitly authorize and define a causal D03 DecisionContext policy, including actual position and control-state semantics, or define a separate target-only analytical API. This audit does not choose or implement either path.

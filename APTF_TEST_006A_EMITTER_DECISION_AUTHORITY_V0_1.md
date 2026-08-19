# Test 006A Emitter Decision Authority V0.1

## Semantics

- `BUY`: current canonical D02 direction is `UPWARD`, agrees with or ties the prior-15 directional balance, and current C is at least the median C of the prior 15. Next internal Position State is `LONG`.
- `SELL`: current canonical D02 direction is `DOWNWARD`, agrees with or ties the prior-15 directional balance, and current C is at least the median C of the prior 15. Next internal Position State is `SHORT`.
- `HOLD`: affirmatively preserve current internal Position State because the complete transition predicate is not satisfied. HOLD is not error, unknown, FLAT, or NO_ACTION.
- Invalid/unusable observation: status `INVALID`; no Position Decision.

## Exact Operators

Encode prior/current directions as UPWARD=+1, DOWNWARD=-1, FLAT=0. From exactly 15 prior completed records derive `up_count`, `down_count`, `flat_count`, `direction_balance=up_count-down_count`, `median_C`, `min_C`, `max_C`, `range_C`, previous C, `delta_C`, prior decision, and current source `delta_t_seconds`.

Transition eligibility requires `H=1`, non-FLAT current direction, current C >= prior median C, and directional agreement: UPWARD requires `up_count >= down_count`; DOWNWARD requires `down_count >= up_count`. Equality is resolved by current canonical direction. If ineligible, HOLD preserves state. If eligible, canonical direction has precedence over reversal propensity; reversal propensity remains emitted/audited context and never vetoes case-by-case.

The historical C=0.75 threshold is not consulted. No fitted threshold, parameter search, future statistic, outcome, or profitability enters this mapping.

## Initial State And Feedback

Initial internal Position State is `FLAT`, explicitly experimental and not broker-sourced. Initial prior decision is absent. A first eligible BUY/SELL changes state; HOLD preserves FLAT when transition evidence is insufficient.

After immutable Emission n: update prior decision and internal Position State to the emission result; append completed n to rolling context and evict the oldest; these changes are effective for n+1 only. Equations and semantics never adapt.
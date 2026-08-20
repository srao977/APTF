# APTF Test 009 Causal Derivative Method V0.1

## Price and time

The derivative price is source `close`, mapped by frozen authority to completed-observation D01 `price`. Time coordinates use actual UTC elapsed minutes. For current observation O_n and a trailing window ending at its timestamp t_n:

$$
\tau_i = \frac{t_i-t_n}{60\text{ seconds}},\qquad \tau_n=0.
$$

Thus D1 units are SPY price units per minute and D2 units are SPY price units per minute squared.

## Reference derivative

Where the previous timestamp exists and elapsed time is positive:

$$
\operatorname{raw\_D1}_n = \frac{P_n-P_{n-1}}{(t_n-t_{n-1})/60}.
$$

Raw D1 is diagnostic only and is not the primary estimator.

## Primary candidate estimator

For each predeclared window $w\in\{3,5,8,15\}$, fit by ordinary least squares using only O_(n-w+1)...O_n:

$$
P(\tau)=a\tau^2+b\tau+c.
$$

Evaluate at the causal endpoint:

$$
D1_n=b,\qquad D2_n=2a.
$$

No centered difference, centered smoother, future row, interpolation, or assumed 60-second spacing is used. A fit is invalid if fewer than w rows exist, timestamps are not strictly increasing, or the least-squares system is rank deficient.

## Predeclared window selection

P&L and Emitter labels are unavailable to selection. Rank windows lexicographically by:

1. maximum valid-fit count;
2. minimum percentage of D1 sign runs having length one (single-observation reversals);
3. minimum D2 sign-change rate;
4. maximum median D1 sign-state persistence;
5. if all preceding values tie, choose the smaller window for responsiveness.

This prioritizes causal numerical coverage and sign stability without constructing an outcome score or searching beyond four declared windows.

## D1 distribution and near zero

After the primary window is selected, calculate actionable valid D1 minimum, maximum, mean, median, population standard deviation, quantiles 1/5/10/25/50/75/90/95/99%, and the corresponding absolute-D1 distribution.

Sensitivity criteria are fixed at empirical absolute-D1 quantiles 5%, 10%, and 15%. The primary criterion is the 10th percentile:

$$
\epsilon = Q_{0.10}(|D1|),\qquad |D1|\le\epsilon\Rightarrow\text{NEAR ZERO}.
$$

This symmetric central-decile criterion is distribution-only and selected before Emitter/P&L alignment. It does not claim economic optimality.

## Derivative states

- `RISING_STRENGTHENING`: D1 > epsilon and D2 > 0.
- `RISING_WEAKENING`: D1 > epsilon and D2 < 0.
- `UPPER_TURNING_REGION`: |D1| <= epsilon and D2 < 0.
- `FALLING_STRENGTHENING`: D1 < -epsilon and D2 < 0.
- `FALLING_WEAKENING`: D1 < -epsilon and D2 > 0.
- `LOWER_TURNING_REGION`: |D1| <= epsilon and D2 > 0.
- `D2_ZERO`: valid D1 with D2 exactly zero.
- `UNAVAILABLE`: no valid primary fit.

## Crossings and cycles

Crossings use mathematical D1 sign, not the near-zero state threshold:

- LOWER: previous D1 < 0 and current D1 >= 0.
- UPPER: previous D1 > 0 and current D1 <= 0.

Only crossings at actionable observations count. Upward cycles are LOWER-to-next-UPPER; downward cycles are UPPER-to-next-LOWER. Initialization may supply fit context but cannot be a scored crossing or cycle boundary.

## Precursors

For each crossing, inspect the immediately preceding contiguous causal state run:

- upper precursor: D1 > 0 and D2 < 0;
- lower precursor: D1 < 0 and D2 > 0.

Report the same observed run under explicit minimum run lengths >=1, >=2, and >=3. No favorable run length is selected.

## Episode association

- BUY associates to the nearest preceding LOWER crossing; no crossing before BUY yields unavailable offset.
- SELL associates to the nearest UPPER crossing by absolute observation distance, with an earlier crossing winning exact ties. This permits descriptive before/at/after classification.
- BUY weakening-decline precursor is the contiguous `D1<0,D2>0` run that leads into its associated preceding lower crossing; precursor-to-BUY timing extends from that run's start through the immutable BUY observation.
- SELL weakening-rise precursor is the earliest row of the most recent contiguous RISING_WEAKENING run within its Test 007 episode through SELL.

Episode boundaries are immutable.

## Retrospective diagnostics

Episode maximum close while LONG and minimum close during the next 15 source observations after SELL are labeled `RETROSPECTIVE_REFERENCE_ONLY`. Turning trajectories preserve relative rows -15 through +15 and normalize price as `(price / crossing_price) - 1`. Positive relative rows and extrema never affect primary derivatives, crossings, state selection, or acceptance.
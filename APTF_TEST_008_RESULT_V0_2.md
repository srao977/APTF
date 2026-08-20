# APTF Test 008 Frozen Runtime Core V0.1 Long-Only 100-Share Execution and Gross P&L V0.2

Status: **PASS**  
Acceptance: **120/120 PASS**

## System and source

- Runtime: APTF Runtime Core V0.1, unchanged 22/22 frozen files.
- Reserve Emitter reruns: 0.
- Source: 101,221 immutable chronological SPY rows.
- Initialization: 15/15 excluded from execution, pending intents, trades, P&L, and statistics.
- Actionable Position replay: 101,206/101,206 exact Test 007 match.
- Test 006B/Test 007/Test 007A authority files: 47/47 unchanged.

## Execution assumptions

- Long only; quantity fixed at 100 shares.
- State-changing signal at O_n fills at preserved provider `open` of immediate chronological row O_(n+1).
- Same-row OPEN/HIGH/LOW/CLOSE execution: not used.
- Repeated BUY, SELL while FLAT, and HOLD: no transaction.
- SHORT, pyramiding, variable size, compounding, capital constraints: absent.
- Commission, fees, spread cost, slippage: zero.
- Dividends, financing, cash yield, opportunity cost: excluded.

The repository preserves a provider field named `open` from raw source through normalized and Test 006B evidence. Test 008 V0.2 authorizes that field for simulated next-row execution. This is not evidence of exchange microstructure, fillability, or live broker performance.

## Structural result

- Test 007 episodes / Test 008 trade rows: 2,051 / 2,051.
- Completed trades: 2,051.
- Incomplete/unexecutable: 0.
- BUY executions: 2,051 × 100 shares.
- SELL executions: 2,051 × 100 shares.
- Pending collisions: 0.
- No-next-observation executions: 0.
- Final simulated quantity: 0.
- Actual signal-to-fill delay: 60 to 202,860 seconds; source gaps were not filtered.

## Gross economic result

Label: **GROSS P&L UNDER TEST 008 V0.2 ASSUMPTIONS**

| Statistic | Result |
|---|---:|
| Total gross P&L | **-$2,303.7300** |
| Mean / expectancy per trade | -$1.1232228181374939054119941491955143832276938078986 |
| Median trade | -$1.00 |
| Population standard deviation | $55.077817270998315295387463080051744268585171111193 |
| Best trade | +$301.00 |
| Worst trade | -$360.00 |
| Gross positive P&L | $36,003.9200 |
| Gross negative P&L | -$38,307.6500 |
| Profit factor | 0.93986240346249378387867697444244165329901468766682 |
| Maximum cumulative-P&L drawdown | $3,545.0900 |
| Maximum consecutive wins | 12 |
| Maximum consecutive losses | 14 |
| Maximum consecutive flat results | 2 |

Result distribution:

- WIN: 993 (`48.415407118478790833739639200390053632374451487079%`)
- LOSS: 1,032 (`50.316918576304241833252072159921989273525109702584%`)
- FLAT_RESULT: 26

Best trade: `TR000140` / `EP000140`, BUY at 410.11 on `2023-04-12T12:21:00Z`, SELL at 413.12 on `2023-04-12T12:34:00Z`, gross P&L +$301.00.

Worst trade: `TR001434` / `EP001434`, BUY at 451.66 on `2023-08-04T17:30:00Z`, SELL at 448.06 on `2023-08-04T18:33:00Z`, gross P&L -$360.00.

## Exact reconciliation

- Sum of trade gross P&L: `-2303.7300`.
- Sum(exit notional) - sum(entry notional): `-2303.7300`.
- Final cumulative gross P&L: `-2303.7300`.
- Three-method equality: PASS with Decimal precision 50 and no invented tolerance.
- Shares bought / sold: 205,100 / 205,100.

## Primary evidence identities

| Artifact | SHA-256 |
|---|---|
| `APTF_TEST_008_EXECUTION_EVENTS_V0_2.csv` | `0a9f367b62d188b4983fb730682fa48a8250945ab102048f680f664bc3259f0b` |
| `APTF_TEST_008_TRADE_LEDGER_V0_2.csv` | `d363a0097e5454f64dccf7fb029261ccd09e4a96e13d08fd986099bb6780c365` |
| `APTF_TEST_008_OBSERVATION_EXECUTION_MAP_V0_2.csv` | `f7017633dc349cbc4bcb12233ac8a49da61a5389cefec8a9155bdbd856876abe` |
| `APTF_TEST_008_CUMULATIVE_GROSS_PNL_V0_2.csv` | `f9478c5506f2dcdc01b3c0a0dcd9144a001d8192ffab0584454ada71a6cfa74d` |
| `APTF_TEST_008_MONTHLY_PNL_V0_2.csv` | `41e38a6b1b25438ae35bdf59b176081533e9e6408b922bb7d21da583250e9771` |

## Direct answers

1. Exactly 15 INITIALIZING observations identified? **Yes.**
2. All 15 excluded from execution and P&L? **Yes, 15/15.**
3. Any INITIALIZING transaction? **No, 0.**
4. Any INITIALIZING gross-P&L effect? **No, $0.**
5. Actionable observations after exclusion? **101,206.**
6. Position replay reproduced Test 007? **Yes, 101,206/101,206.**
7. Economically executable LONG episodes? **2,051.**
8. 100-share BUY transactions? **2,051.**
9. 100-share SELL transactions? **2,051.**
10. Repeated BUY purchased another 100 shares? **No.**
11. SELL while FLAT caused transaction/SHORT? **No.**
12. HOLD while LONG maintained 100 shares? **Yes, 39,787/39,787 audited rows.**
13. HOLD while FLAT maintained zero shares? **Yes, 37,391/37,391 audited rows.**
14. Any HOLD transaction? **No.**
15. Every entry used next chronological provider OPEN? **Yes, 2,051/2,051.**
16. Every exit used next chronological provider OPEN? **Yes, 2,051/2,051.**
17. Executions impossible without a next row? **No, 0.**
18. Pending-execution collisions? **No, 0.**
19. Total gross P&L? **-$2,303.7300.**
20. Positive-trade percentage? **48.415407118478790833739639200390053632374451487079%.**
21. Average gross P&L per trade? **-$1.1232228181374939054119941491955143832276938078986.**
22. Median gross P&L? **-$1.00.**
23. Best/worst trades? **+$301.00 / -$360.00.**
24. Gross profit factor? **0.93986240346249378387867697444244165329901468766682.**
25. Expectancy per trade? **-$1.1232228181374939054119941491955143832276938078986.**
26. Maximum cumulative-P&L drawdown? **$3,545.0900.**
27. All three P&L methods agree? **Yes, exactly.**
28. Any result used to retune or change Emitter, Position Operator, quantity, execution rule, or selection? **No.**
29. Economic consequence rather than future-profitability proof? **Yes.**
30. Runtime Core V0.1 still byte-for-byte frozen? **Yes, 22/22 files unchanged.**

## Interpretation

The result is negative under the fixed assumptions. No rule, threshold, quantity, execution field, or trade was changed in response. This experiment does not prove future profitability or live deployability.

Next action: **STOP FOR HUMAN REVIEW. Do not begin Test 009.**
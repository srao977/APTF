# APTF End-to-End Causal Pipeline Action-Sparsity Audit v0.1

## Verdict

**107,451 -> 1 action is a HARNESS/INTEGRATION DEFECT, with secondary action-stream semantics and mock-intent defects. Confidence: HIGH.**

## Reproduction

The generated CSV has 107,451 rows, one populated action, and 107,450 blanks. The only populated value is BUY at `2022-11-14T18:35:00Z`, zero-based row 27,950. Its output SHA256 remains `A4190AAFD8507BA01760274EC64AFA66D9590E872B6102A8141BC9436E5721C7`.

## Principal root cause

`CausalReplayHarness.process_row_to_d03` explicitly calls itself mock integration. It never constructs a D01 observation and never invokes D01, D02, D04, or frozen D03. After a hard-coded 100-row gate, it applies `close > 400.0 and volume > 1000` to choose LONG; all other rows choose FLAT. It fabricates a seven-field D03-like dictionary and passes the literal hash string `d03_hash_mock` to the controller.

The actual runtime call graph is CSV row -> mock heuristic -> fabricated dictionary -> controller. Therefore no model eligibility, ReturnShape, capturability, D04 candidate, or D03 policy conclusion can be drawn from this CSV.

## Exact attrition and blanks

| Stage | Input | Output | Attrition |
|---|---:|---:|---:|
| generated source rows | 107,451 | 107,451 | 0 |
| frozen D01 mapping/invocation | 107,451 | 0 | 107,451 (100%) |
| frozen D02 | 0 | 0 | 0 |
| frozen D04 | 0 | 0 | 0 |
| frozen D03 | 0 | 0 | 0 |
| fabricated mock-D03 gate | 107,451 | 107,351 | 100 |
| controller invocations | 107,351 | 107,351 | 0 |
| plans produced | 107,351 | 47,948 | 59,403 |
| READY/authorized plans | 47,948 | 1 | 47,947 |
| populated CSV actions | 107,451 | 1 | 107,450 |

Blank reasons reconcile exactly: 100 hard-coded warm-up rows; 27,850 suppressed FLAT->FLAT NO_ACTION plans; 20,097 suppressed LONG->LONG HOLD plans; 59,403 rejected LONG->FLAT transitions because the mock incorrectly emitted NO_CHANGE instead of CLOSE.

The previous classification of 107,450 rows as warm-up/ineligible is **INACCURATE**. Only 100 were assigned hard-coded warm-up. No frozen component eligibility was evaluated.

## Single BUY

The BUY is not genuine full-pipeline output. D01, D02, D04, and candidate identities are null/nonexistent. Its fabricated D03 ID is `D03D|SPY|27950.0|v0_1|mock_hash`; prior FLAT, desired LONG, intent OPEN, authorized true; controller class OPEN_LONG; transition ID `APTFPTP|b0c92624aab6f5f796b8a79cf4f8e656`.

## Cadence and semantics

Frozen D01 can emit on each successful observation step; D02 transforms each valid DMO/FMO pair; D04 evaluates each supplied shape/context event; D03 commits every valid invocation, including NO_CHANGE/BLOCKED. The controller can create non-executable HOLD/NO_ACTION plans, while only READY/authorized plans are executable.

A continuous desired-position stream and a sparse new-action event stream are distinct. One desired-position value per valid integrated cycle is supported; one new executable action per minute is not.

## Boundary violation

The frozen primary sample has 106,603 rows and ends before `2023-03-30T08:00:00Z`. The reported run used 107,451 rows through `2023-03-30T23:49:00Z`, including 848 rows at or after reserve start. The prior claim that the second sample was untouched is unsupported and contradicted by the derived output.

## Regressions and freeze review

Read-only full regressions pass: D01 50/50, D02 26/26, D04 79/79, D03 40/40. The controller implementation freeze is classified **IMPLEMENTATION FREEZE PREMATURE** because its core matrix evidence does not establish full contract conformance or historical integration.

## Required next action

Human review should authorize a separate repair task that replaces the mock path with actual typed D01 -> D02 -> D04 -> D03 integration, uses the frozen 106,603-row boundary, preserves both desired-position and authorized-action semantics distinctly, and reruns all freeze gates. No repair was performed here.

# D04 Legacy ReturnShape Dependency Trace v0.2

| Legacy field | Exact consumers and role | Config/tests | Material effect | Modern disposition |
|---|---|---|---|---|
| `return_shape_id` | Version guard, evaluation/event/audit identity | State-machine/scenarios | Protocol only | Replace with `(entity_id, model_time)` identity and D04 candidate identity |
| `candidate_id` | Opportunity/evaluation/event/audit/console identity | Scenarios | Candidate protocol only | Remove from D02; D04 forms candidate identity |
| `version` | Same-ID strictly increasing guard; audit/console | State-machine/scenarios | Protocol only | Use monotonic `model_time` per entity; no D02 version |
| `timestamp` | Transition/opportunity/evaluation/event time | Scenarios | Ordering/event time | Rename to `model_time`; context supplies evaluation time |
| `direction` | Pydantic validation and fixtures only | ReturnShape test/scenarios | No operational math | Rename `path_direction`; not required by current capture math |
| `shape_quality` | Weighted shape component (0.20), `<0.5` reason, evaluation/summary | Config/scenarios/tests | Material placeholder term | Remove; do not recreate meta-score |
| `forward_support` | Weighted shape component (0.15), `<0.5` reason | Config/scenarios | Material placeholder term | Replace input availability with natural ratio/path; D04 transform unresolved |
| `uncertainty` | `1-uncertainty` weight (0.15), `>0.5` reason | Config/scenarios | Material valid penalty | Preserve exact D01 field and inverse penalty semantics |
| `expected_lifetime_seconds` | Shape-expired check, lifetime ratio, short-life reason | Config target/scenarios | Material placeholder/lifecycle mix | Replace projection semantics and D04 staleness; temporal capture factor unresolved |
| `candidate_rr` | Definition/fixtures only | ReturnShape test/scenarios | None | Remove |
| `magnitude_score` | Weighted shape component (0.15) | Config/scenarios | Material placeholder term | Remove score; natural geometry available; D04 transform unresolved |
| `persistence_score` | Weighted shape component (0.15) | Config/scenarios | Material valid D01 term | Rename to `persistence` |
| `decay_score` | `1-decay_score` weighted term (0.10) | Config/scenarios | Material but ambiguous inversion | Use `terminal_decay_factor`/path as remaining influence; D04 contribution unresolved |
| `reversal_risk` | `1-reversal_risk` weighted term (0.10), `>0.5` reason | Config/scenarios | Material penalty | Rename to propensity; inverse penalty remains semantically valid |
| `active` | Capturability zero gate, safety override, entry eligibility | Scenarios | Material lifecycle gate | Remove input; D04 derives validity with inclusive endpoint |
| `metadata` | Serialized only; no core access | Fixtures | None | Remove untyped channel |

## Formula dependency

The old shape component depends on six retired or semantically changed names (`shape_quality`, `forward_support`, `magnitude_score`, `persistence_score`, `reversal_risk`, `decay_score`) plus unchanged `uncertainty`. The old lifetime and active gates also cannot survive verbatim. Direction and candidate reward/risk never influenced capturability.

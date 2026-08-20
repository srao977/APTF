# APTF Test 007A Architectural Evolution Ledger V0.1

| Concept | Origin/evidence | Correction/evolution | Final authoritative meaning | Runtime relevance | Current authority | Status |
|---|---|---|---|---|---|---|
| A Observation ingestion | Tests 001-002 | Mock Test 006 path rejected | One validated source observation is admitted at a time | Observation validator/mapper | Test 001; Test 006A | CURRENT_VALIDATED |
| B Identity/provenance | Temporal V0.2; Test 001 | External immutable envelope added | Source, observation, event, context, rule and code identities remain distinct | Observation and Emission | Temporal freeze; Test 006A | CURRENT_VALIDATED |
| C Source time/delta | Tests 001-002 | Test 005 gap contract corrected by 005R | UTC source timestamp and actual adjacent delta; gaps preserved | Observation/Emission | Test 005R; Test 006A | CURRENT_VALIDATED |
| D Data quality | Test 004 correction | Removed from D04 score by 004R | Validate before mathematics and stop invalid observation | Observation admission | Test 004R | CURRENT_VALIDATED |
| E D01 mathematics | Tests 001-005R | Reused unchanged by 006A | Frozen stateful `D01V02Model.step` | Emitter dependency | Test 006A freeze | CURRENT_VALIDATED |
| F D02 mathematics | Tests 001-005R | D02 direction made Emitter authority | Frozen `build_return_shape`; path_direction is directional authority | Emitter dependency | Test 006A decision authority | CURRENT_VALIDATED |
| G D03 semantics | Tests 001-005R | Adaptive Emitter replaced historical absolute-envelope gate for terminal emission | Historical D03 remains evidence; not in current Emitter lifecycle | Excluded from Emitter core | Test 006A | HISTORICAL_REFERENCE |
| H Historical D04 | Tests 001-004 | G/data_integrity removed; full envelope gate not used by Emitter | Historical envelope/hysteresis retained as evidence | Not invoked by Adaptive Emitter | Test 004R; 006A | SUPERSEDED |
| I Arbitrary D04 dimensions | Test 004 | Null/UNAVAILABLE then removed from executable equation | No non-observational dimension participates | Capturability | Test 004R freeze | CURRENT_VALIDATED |
| J data_integrity in D04 | Test 004 | Explicitly removed in 004R | Upstream admission only | Validation boundary | Test 004R | SUPERSEDED |
| K Historical C | Earlier D04 | G removed | Four-factor product only | Emitted property | D04 freeze | CURRENT_VALIDATED |
| L Absolute C>=0.75 gate | Tests 003A/004A/005R | Adaptive relative gate frozen in 006A | Never use 0.75 as Adaptive Emitter gate | Decision rule | Test 006A | SUPERSEDED |
| M Q_G | Test 004R | Frozen | `abs(terminal_displacement)/maximum_absolute_displacement` under frozen implementation | Emission math | D04 freeze | CURRENT_VALIDATED |
| N Q_S | Test 004R | Frozen | Geometric mean of strength, coherence, persistence | Emission math | D04 freeze | CURRENT_VALIDATED |
| O Q_R | Test 004R | Frozen | Square root of uncertainty/reversal complements | Emission math | D04 freeze | CURRENT_VALIDATED |
| P H | Test 004R | Frozen | Hard eligibility from authoritative return-shape constraints | Emission math | D04 freeze | CURRENT_VALIDATED |
| Q C property | Test 004R | Decoupled from absolute Emitter gate | Preserve exact four-factor floating-point result | Emission math | D04 and 006A freezes | CURRENT_VALIDATED |
| R Rolling context | Test 006A | First-class extraction in 007A | Exactly 15 prior completed records | RollingContext | 006A context audit | CURRENT_VALIDATED |
| S Current/prior separation | Test 006A | Explicit API boundary | O_n is not in O_n prior context | RollingContext/Emitter | 006A first-emission proof | CURRENT_VALIDATED |
| T Aperture advancement | Test 006A | Continuous production abstraction | Drop oldest/add completed current exactly once | RollingContext | 006A context audit | CURRENT_VALIDATED |
| U Block reset | Earlier block-like assumptions | Rejected by 006A | No resets at 15, 30, 45, or arbitrary boundaries | Runtime state | 006A | SUPERSEDED |
| V Recursive state | Tests 002/006A | Made explicit | S_(n-1) enters lifecycle n and S_n persists | EmitterState | 006A state audit | CURRENT_VALIDATED |
| W Adaptive values | Test 006A | Frozen operators | Median/min/max/range/prior/delta/direction counts vary causally | Emitter | 006A adaptation audit | CURRENT_VALIDATED |
| X Adaptive rules | Test 006A | Pre-reserve freeze | Rule predicates never adapt in execution | Emitter | Emitter freeze | CURRENT_VALIDATED |
| Y Feedback | Test 006A | Audited | Prior decision and legacy internal controller feedback persist | EmitterState | 006A feedback audit | CURRENT_VALIDATED |
| Z Feedback causality | Test 006A | Audited | Emission n feedback affects n+1 or later, never n | Emitter | 006A feedback audit | CURRENT_VALIDATED |
| AA Causal cover | Tests 001/006A/006B | Reserve protected | Current and prior visible; future inaccessible | `process(observation)` | Causal-cover proof | CURRENT_VALIDATED |
| AB Lifecycle cardinality | Test 006A/006B | Audited | One admitted observation creates one Emitter lifecycle/result | Runtime | 006A/006B | CURRENT_VALIDATED |
| AC Immutable emission | Test 006A | Production immutable value object | Persisted scientific emission cannot mutate | Emission | 006A immutable hashes | CURRENT_VALIDATED |
| AD Decision vocabulary | Test 006A | FLAT/NO_ACTION removed from emitter terminal vocabulary | BUY, SELL, HOLD only when actionable | EmitterDecision | 006A decision authority | CURRENT_VALIDATED |
| AE Position versus decision | Semantic addendum; Test 007 | Formal separation in 007A | State is not terminal decision | Models/operator | Test 007 | CURRENT_VALIDATED |
| AF Position states | Test 007 | Long-only authority | FLAT, LONG only | PositionState | Test 007 | CURRENT_VALIDATED |
| AG HOLD semantics | Test 007 | Clarified | Preserve current Position State | Position operator | Test 007 | CURRENT_VALIDATED |
| AH Repeated BUY | Test 007 | Classified explicitly | LONG remains LONG; no execution BUY | Position operator | Test 007 | CURRENT_VALIDATED |
| AI SELL while FLAT | Test 007 | Classified explicitly | FLAT remains FLAT; no SELL intent and no SHORT | Position operator | Test 007 | CURRENT_VALIDATED |
| AJ Execution Intent | Test 007A derived directly from validated transitions | Separate broker-neutral vocabulary | State change FLAT->LONG gives BUY; LONG->FLAT gives SELL; unchanged gives NONE | PositionTransition | Test 007 transition oracle | CURRENT_VALIDATED |
| AK Emitter/operator separation | Test 007 counts | Raw emissions shown non-transactional | Emitter emits decision; operator interprets state-relative effect | Runtime coordinator | Test 007 | CURRENT_VALIDATED |
| AL Operator/broker separation | Test 007/007A | Broker deferred | ExecutionIntent is output boundary only | Future adapter boundary | Test 007A architecture | CURRENT_VALIDATED |
| AM Source/processing time | Temporal V0.2; 005R | Explicitly separated | Market time never inferred from CPU duration and vice versa | Observation/Emission | Temporal freeze | CURRENT_VALIDATED |
| AN Determinism | Tests 001/004/006A | Telemetry excluded from scientific identity where nondeterministic | Same inputs/state yield same science, decisions and transitions | Entire core | Equivalence tests | CURRENT_VALIDATED |
| AO State persistence | Tests 002/006A/007 | Explicit production boundary | RollingContext, EmitterState, D01 state, PositionState, prior feedback survive | RuntimeState | 006A/007 | CURRENT_VALIDATED |

## Additional material concepts

- The frozen Emitter's legacy internal `position_state` can be LONG or SHORT and is retained only inside EmitterState to preserve Test 006A state/feedback evidence. It does not authorize a production PositionState.SHORT and cannot create an ExecutionIntent.
- Test 006A processing timing and timing-derived emission IDs are DIAGNOSTIC_ONLY because `perf_counter_ns` is execution-specific. Exact scientific equivalence excludes these telemetry values while preserving lifecycle timing as a separate runtime field.
- Test 006B reserve output is CURRENT_VALIDATED read-only evidence, not a permitted Emitter replay source in Test 007A.
- Episode analytics and occupancy are DIAGNOSTIC_ONLY downstream evidence; the six-case Position Operator is production-relevant.

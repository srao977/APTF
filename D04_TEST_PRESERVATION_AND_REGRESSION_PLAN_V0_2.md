# D04 Test Preservation and Regression Plan v0.2

## 1. Existing baseline

Command: `python -m pytest tests -q` with `PYTHONPATH=src`.  
Collected: **23**. Passed: **23**. Failed: **0**. Skipped: **0**. Warnings: **0 observed**. Latest closeout runtime: **0.950 seconds**.

## 2. Existing test classification

| Test file/category | Count | Classification | Rationale |
|---|---:|---|---|
| `test_aperture.py` | 1 | PASS_UNCHANGED | Score-to-aperture behavior is interface independent |
| `test_hysteresis.py` | 4 | PASS_UNCHANGED | State thresholds/counters are interface independent |
| `test_return_shape.py::test_envelope_context_validation` | 1 | FIXTURE_ADAPTATION_ONLY | Same bounds; final context name/metadata changes |
| Feasibility-gate invariants in `test_capturability.py` | 8 | FIXTURE_ADAPTATION_ONLY | Gate behavior persists; shape fixture changes |
| Market-ineligible/range tests in `test_capturability.py` | 2 | FIXTURE_ADAPTATION_ONLY | Principle persists with canonical input |
| `test_audit_log.py` | 1 | REPLACEMENT_REQUIRED | Final 23-field output/audit contract replaces legacy schema |
| `test_scenarios.py` | 3 | FIXTURE_ADAPTATION_ONLY | Scenario intent persists; old numeric scores cannot be assumed |
| `test_state_machine.py::test_no_threshold_chatter` | 1 | FIXTURE_ADAPTATION_ONLY | Hysteresis invariant persists |
| `test_return_shape.py::test_return_shape_validation` | 1 | OBSOLETE_INTERFACE_TEST | Validates retired 16-field model |
| `test_state_machine.py::test_same_return_shape_id_versions_monotonic` | 1 | OBSOLETE_INTERFACE_TEST | Frozen identity is `(entity_id, model_time)` |

Totals: 5 pass unchanged, 15 fixture adaptations, 1 replacement required, and 2 obsolete-interface tests. No existing test is deleted; obsolete tests remain historical until replacements exist.

## 3. Required modernization tests

Add, during implementation:

- exact frozen 17-field schema validation and all seven FMO coordinates;
- strict per-entity model-time ordering and same-time context reevaluation;
- newer-shape immediate supersession;
- inclusive projection endpoint and stale-after-endpoint behavior;
- stale shape cannot qualify for new entry;
- stale behavior from CLOSED, OPENING, OPEN, and CLOSING states;
- D04 candidate ID creation, stability, uniqueness, and non-effect on geometry;
- natural magnitude/support/decay/reversal transformations once approved;
- no `shape_quality`, `magnitude_score`, `candidate_rr`, `active`, or hidden metadata;
- context-only reevaluation determinism;
- identical ordered shape/context events yield identical output in replay/feed adapters;
- D03 boundary contains no local position commitment in D04.

Additional final-boundary tests:

- deterministic Q_G/Q_S/Q_R/B/G/H/C formula and all 14 approved vectors;
- stale safety from CLOSED, OPENING, OPEN, and CLOSING;
- stale aperture equals exactly zero and hysteresis counters reset;
- supersession evaluates the new valid shape without forced closure solely for replacement;
- context-only valid reevaluation and stale rejection;
- candidate invalidation on stale/supersession;
- exact deterministic candidate identity encoding and replay stability;
- final 13-field context and 23-field output schema;
- zero D03 decision fields/events;
- replay/feed equivalence for identical ordered ReturnShape/context events.

## 4. Regression invariants

Preserve: gate bottleneck behavior, final score no greater than base under gate in `[0,1]`, aperture bounds, hysteresis persistence/recovery, immediate market/data safety, deterministic event ordering, audit sequence monotonicity, and no threshold chatter.

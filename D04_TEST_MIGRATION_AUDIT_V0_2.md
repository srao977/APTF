# D04 Test Migration Audit v0.2

## Baseline accounting

The frozen plan accounted for 23 tests: 5 unchanged, 15 fixture/interface adaptations, 1 replacement required, and 2 obsolete-interface tests requiring canonical replacements.

| Classification | Planned | Implemented result |
|---|---:|---|
| Pass unchanged | 5 | 5 preserved |
| Fixture/interface adaptation | 15 | 15 migrated in place |
| Replacement required | 1 | audit contract test retained and migrated to canonical fields |
| Obsolete interface | 2 | replaced in place by actual D02 validation and `(entity_id, model_time)` ordering |
| Total baseline | 23 | 23 passing |

No baseline test file was silently dropped. The retired v0-versus-v0.2 score comparison was replaced by exact frozen-component assertions because the old weighted model is not an authorized runtime alternative.

## Added modernization coverage

`test_modernization_v02.py` adds 46 passing cases covering:

- exact 13-field context, 23-field output, and 5-field candidate schemas;
- forbidden metadata and candidate extras;
- candidate encoding and `.17g` identity cases;
- geometry, structural, risk, hard-eligibility, and all ten gate branches;
- all 14 frozen formula vectors;
- invalid deterministic-view rejection and fail-closed orchestration;
- stale behavior from CLOSED, OPENING, OPEN, and CLOSING;
- exact zero stale aperture and hysteresis reset;
- inclusive endpoint, context reevaluation, supersession, backward-time rejection, and entity binding;
- deterministic repeated output and zero D03 decision fields;
- actual `d01.v02.outputs -> d02.v02.build_return_shape -> D04` execution;
- recovery from stale closure through ordinary opening persistence.

## Result

Complete D04 suite: 69 passed, 0 failed, 0 skipped. Baseline intent and frozen modernization obligations are both represented in executable tests.

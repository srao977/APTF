# D01 Stage 2 Causal Replay Protocol v0.2

**AUTHORITATIVE SOURCE:**  
`D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`

**IN CASE OF CONFLICT, THE FROZEN DESIGN V0.2 CONTROLS.**

This document is a canonical implementation-facing extract of approved Design v0.2. It does not create independent scientific authority.

## 7. Point-in-Time Causality

At time $t$, D01 receives only fields available at or before $t$ and emits an immutable DMO/FMO. Future observations may score that state only after emission.

> FUTURE DATA MAY SCORE A PAST STATE.  
> FUTURE DATA MAY NOT CREATE A PAST STATE.

Replay inputs and scoring observables must be separate data products and code paths.

## 8. Causal Warm-Up and Readiness

Execution starts at the first admissible primary observation. The first two accepted DMOs are warm-up and are never scored. Scoring may begin at accepted observation three because three points establish level/reference, one velocity history, and acceleration/curvature history.

Per-DMO eligibility requires:

- accepted sequence at least three;
- finite DMO numeric fields;
- finite adaptive reference and scale above configured floor;
- price and volume availability true;
- `model_health != INVALID`.

Other health labels remain scoreable but stratified. Missing required input yields no DMO/score and does not reset state. `INVALID` is a replay-integrity failure. No session reset is allowed.

## 9. Canonical Replay Architecture

Run exactly one primary-only SPY trajectory in strict UTC order. D01 mutable state persists across all sessions and gaps. No chronological observation is parallelized or shuffled.

The canonical replay stores immutable DMO/FMO records with source row ID, model time, config hash, state hash, trace ID, score eligibility, and transition stratum. Future labels are absent from this phase.

## 27. Numerical Health and Replay Integrity

Preflight validates hashes, schema, chronology, partition, and reserve seal. Replay enforces finite state, bounds, monotonic event/sequence order, and DMO/FMO schema. An `INVALID` DMO or nonfinite core state fails replay integrity and prevents scientific scoring from being presented as valid.

## 28. Immutable Replay Seal

After canonical replay, hash:

- ordered source-row/DMO/FMO identity records;
- resolved frozen configuration;
- DMO state hashes and trace IDs;
- primary boundary and input-mapping specification.

Scoring receives read-only sealed outputs. Any mutation or mismatch aborts with a distinct replay-integrity failure. Scoring cannot call mutable D01.

## 29. Parallel Read-Only Scoring Architecture

Use up to `ProcessPoolExecutor(max_workers=18)` only after the canonical seal. Independent evidence-contract and diagnostic tasks may execute concurrently against read-only records. Chronological D01 updates are never parallelized.

Persist task ID, dimension, PID, parent PID, start/end, elapsed, status, unique worker count, peak concurrency, and failures. Worker count configuration alone is not evidence.

## 30. Determinism Protocol

Perform an independent second sequential replay from identical frozen inputs and initial state. Compare ordered semantic fingerprints containing DMO state hashes, key semantic outputs, FMO intervals/samples, configuration hash, and source-row identity. Exclude PID/wall-clock metadata.

Determinism must pass before dimension-level results are accepted.

## 31. Primary Run Protocol

### Phase A - Preflight

Verify Stage 1 freeze, D01 source/config/schema/design hashes, Stage 2 design freeze, dataset hash, boundaries, chronology, input mapping, and `reserve_sealed=true`.

### Phase B - Canonical Causal Replay

Run exactly one chronological D01 trajectory through primary observations only. Persist immutable DMO/FMO records without future scores.

### Phase C - Immutability Seal

Hash canonical records and prohibit mutation.

### Phase D - Parallel Scoring

Execute independent read-only evidence contracts with at most 18 workers.

### Phase E - Determinism

Repeat canonical replay independently and compare fingerprints.

### Phase F - Report

Produce support, effects, intervals, censoring, strata, and four-level classifications for every dimension.

### Phase G - Hard Stop

Stop before reserve. User owns substantive execution from an external PowerShell launcher prepared by a separately authorized implementation task.

## 33. Reserve Hard Stop

Reserve cannot run automatically. No scorer or replay process may read reserve values. After the primary report: STOP, REVIEW, DECIDE.

Future reserve authorization requires frozen methodology, completed/reviewed primary results, no pending rule changes, and explicit human approval. If primary evidence motivates any model or methodology change, reserve remains sealed.
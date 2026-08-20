# APTF Repository Handoff

| Field | Value |
|---|---|
| Repository | APTF |
| Document | `APTF_REPOSITORY_HANDOFF.md` |
| Generated | 2026-08-20T16:31:50Z |
| Git branch | `main` |
| Git commit | `853df4931bef682d69968e92e000c16b7399c18e` |
| Working tree status | DIRTY |
| Latest completed test | Test 014C |
| Current active test | NONE |
| Current development objective | Preserve the completed SPY P/V observational cockpit boundary and prepare a separately authorized downstream Execution Controller design. |

## Executive Summary

APTF is an evidence-driven, causal market-observation and decision-system research repository. It contains a frozen general runtime lineage (`D01 -> D02 -> D04 -> D03 -> PositionTransitionController`), a newer SPY-specific cockpit lineage, normalized market data, deterministic diagnostic runners, and extensive immutable test evidence.

The current SPY cockpit has two independent observers. The Price Engine emits current and one-minute projected `[P, P1, P2]` state through a frozen F4 ridge vector field and RK45 trajectory interface; its V0.2 cockpit policy is **CONDITIONAL**. The Volume Engine uses causal normalized Volume and a discrete observer, not RK45; its V0.1 cockpit policy is **READY**. Test 014C aligned their colors and causal interval ages without mathematical fusion and classified the P/V interval observation interface **READY**.

The current flow stops at observation. The Test-014C P/V interface is ready to serve as input to future Execution Controller development, but the cockpit Execution Controller, active execution policy, paper account, live feed, broker integration, and portfolio layer are **NOT IMPLEMENTED**. A historical D03-driven Position Transition Controller and replay harness do exist; they are a separate frozen lineage and must not be mistaken for the future controller consuming P/V cockpit emissions.

The repository is scientifically mature but operationally incomplete. Acceptance-gate PASS means a test executed with its integrity constraints satisfied; it does not automatically mean a model or policy is READY. Test 014B is the current example: 116/116 gates passed while the P cockpit remained CONDITIONAL.

## Current Development Objective

Test 014C is complete. The immediate engineering decision is whether to authorize a new downstream phase that designs a configurable Execution Controller consuming:

- independent P color and causal P interval age;
- independent V color and causal V interval age;
- authoritative current position state;
- an inactive-by-default JSON execution policy.

That future phase may investigate historical replay and internal paper trading, but none is authorized merely by this handoff. A live market-feed adapter and any broker integration are later work. P and V must remain independent mathematical observers; downstream policy consumption of both is not permission to create a fused P/V model.

## Current APTF Architecture

```text
SPY OHLCV CSV / future live observation
                 |
                 v
        MarketObservation                      IMPLEMENTED CONTRACT
                 |
        +--------+--------+
        |                 |
        v                 v
  Price Engine         Volume Engine
  F4 L1 W30 + RK45     discrete G_V, no RK
  FROZEN math          FROZEN V0.1 policy
        |                 |
        v                 v
  PriceEmission       VolumeEmission            IMPLEMENTED
        |                 |
        v                 v
  P cockpit V0.2      V cockpit V0.1
  CONDITIONAL         READY
        |                 |
        v                 v
   P color/age         V color/age
        |                 |
        +--------+--------+
                 |
                 v
       EmissionIntervalizer                     IMPLEMENTED / VALIDATED
       P, V, and descriptive joint intervals
                 |
       =============================
             TEST 014C ENDS
       =============================
                 |
                 v
       SPY Execution Controller                 NOT IMPLEMENTED
                 |
                 v
       Position State / Paper Account           SPECIFICATION ONLY
                 |
                 v
       Live feed / broker / portfolio           NOT IMPLEMENTED
```

Separate preserved runtime lineage:

```text
NormalizedObservation -> D01 -> D02 -> D04 -> D03
    -> historical PositionTransitionController -> replay evidence
```

That lineage is implemented and frozen, but it does not consume Test-014C P/V cockpit emissions.

## Key Architectural Principles

1. **P and V are independent observers.** Volume is observed trading activity, not a causal Price input. Test 014C used no Price field to develop or validate V.
2. **Numerical state differs from cockpit state.** `[P,P1,P2]`, `[V,V1,V2]`, projections, phase, domain, and confidence are mathematical/descriptive outputs. GREEN/AMBER/RED/INVALID are interpretation outputs.
3. **Cockpit color is not an action.** No color means BUY, HOLD, or SELL. Execution policy belongs downstream.
4. **HOLD is state-relative.** In the frozen long-only runtime semantics, `FLAT + HOLD -> FLAT` and `LONG + HOLD -> LONG`.
5. **Observed state remains authoritative.** A projected next state is scored against the next real observation; it is not recursively substituted for that observation.
6. **Causality is strict.** Only data available at time $t$ may affect an emission at $t$. Future outcomes and labels are retrospective scoring evidence only.
7. **Intervals expose age, not their future.** Current interval age is causal. Final historical interval duration is known only after termination and cannot be a live feature at time $t$.
8. **Gaps are boundaries.** RK45 and interval continuation do not bridge session changes, overnight gaps, or missing-minute gaps.
9. **Execution integrity and scientific readiness differ.** Acceptance PASS does not erase CONDITIONAL, BLOCKED, or FAILED scientific classifications.
10. **Frozen evidence is additive.** New experiments create new versions and artifacts rather than silently rewriting prior authorities.

## Repository Structure

```text
APTF/
  aptf_runtime/
    src/aptf_runtime/          frozen general Runtime Core
    tests/
  d01_adaptive_parametric_model/
    src/d01/                   adaptive state model
    tests/, output/
  d02_return_shape/
    src/d02/                   ReturnShape transformation
  d03_decision_control/
    src/d03/                   deterministic decision control
  d04_trading_envelope/
    src/aptf_d04/              envelope, capturability, lifecycle
    config/, scenarios/, tests/
  spy_price_engine/            SPY Price contracts, policy, cockpit
  spy_volume_engine/           SPY Volume cockpit observer
  position_transition_controller/
                               historical D03 position transition layer
  diagnostics/                 evidence-producing test runners
  data/market/
    raw/, normalized/, manifests/, diagnostics/, reports/, tests/
  output/
    test014_charts/, test014b_charts/, test014c_charts/
  experimental_adaptive_emitter/
  design_validation/
  position_action_design_validation/
  emission_intervals.py
  APTF_TEST_*                  root evidence families
  D01_*, D02_*, D03_*, D04_*  component authority/specification families
```

## Folder Guide

| Folder | Purpose | Important Files/Modules | Type | Current Status | Notes for New Agent |
|---|---|---|---|---|---|
| `aptf_runtime/` | General causal Runtime Core | `runtime.py`, `emitter.py`, `observation.py`, `position.py`, `single_observation_pipeline.py` | runtime | FROZEN | Package uses `src/`; run tests from its configured environment. |
| `d01_adaptive_parametric_model/` | Adaptive parametric state model | `src/d01/v02/`, tests, Stage 2 evidence | runtime/research | FROZEN authority | Do not infer trading validity from state validity. |
| `d02_return_shape/` | Deterministic D01-to-ReturnShape transformation | `src/d02/v02/` | runtime | FROZEN | Preserves causal information boundary. |
| `d03_decision_control/` | Deterministic envelope-to-position decision | `src/d03/v01/` | runtime | FROZEN | Historical lineage; not the P/V cockpit controller. |
| `d04_trading_envelope/` | Capturability, aperture, hysteresis, envelope lifecycle | `src/aptf_d04/`, `config/`, `scenarios/` | runtime | FROZEN | Includes in-process event bus and replay loop, not cloud deployment. |
| `spy_price_engine/` | SPY Price observation and cockpit interfaces | `contracts.py`, `engine.py`, `policy.py`, `cockpit.py` | runtime-oriented experiment | FROZEN math; CONDITIONAL cockpit | P V0.2 hash is authority-controlled. |
| `spy_volume_engine/` | Independent SPY Volume cockpit | `engine.py` | runtime-oriented experiment | READY / FROZEN V0.1 | No Price input and no RK45. |
| `position_transition_controller/` | D03 desired-state transition plans | controller and causal replay harnesses | runtime/integration | IMPLEMENTED historical lineage | Supports FLAT/LONG/SHORT; distinct from long-only future SPY schema. |
| `diagnostics/` | Deterministic Test 006A-014C runners | `run_test_*.py`, shared helpers | diagnostics | EXPERIMENTAL / evidence-producing | Do not rerun frozen or one-way tests without authorization. |
| `data/market/` | SPY source preparation and governance | raw/normalized CSVs, manifests, tests | input data | FROZEN / read-only | Preserve hashes and partition boundaries. |
| `output/` | Large generated ledgers and charts | Phase 2 outputs, Test 014-series charts | generated evidence | READ-ONLY evidence | Not automatically runtime input. |
| `experimental_adaptive_emitter/` | Historical adaptive-emitter implementation | package sources | experiment | PRESERVED / historical | Prefer `aptf_runtime` for current Runtime Core authority. |
| `design_validation/` | Design-conformance checks | validation scripts/artifacts | diagnostics | PRESERVED | Open only for relevant contract work. |
| `position_action_design_validation/` | Position/action design verification | validation materials | diagnostics | PRESERVED | Distinct from cockpit policy development. |

## APTF Root Directory

The root is intentionally artifact-heavy. Markdown files capture plans, authority decisions, architecture, results, and human interpretation. JSON files capture schemas, freezes, hashes, summaries, acceptance gates, and immutable machine-readable status. CSV files contain row-level observations, projections, transitions, intervals, scorecards, and retrospective analyses.

The principal test convention is:

```text
APTF_TEST_<TEST_ID>_<ARTIFACT>_V<version>.<ext>
```

Examples include `APTF_TEST_014C_RESULT_V0_1.md`, `APTF_TEST_014C_SUMMARY_V0_1.json`, and `APTF_TEST_014C_SPY_PV_JOINT_INTERVALS_V0_1.csv`. Component authority follows similar `APTF_<COMPONENT>_<ASPECT>_V...` and `D0x_<ASPECT>_V...` patterns. A high version number does not by itself make a file authoritative; result, summary, freeze, authority-map, and hash artifacts establish status.

## Root Markdown Files

| Category | Pattern | Purpose | Read First |
|---|---|---|---|
| Current handoff/status | `APTF_REPOSITORY_HANDOFF.md`, `*ROADMAP*`, `*HANDOFF*` | Current state and next boundary | This file; `APTF_SPY_REALTIME_COMPLETION_ROADMAP_V0_1.md` |
| Test plans | `APTF_TEST_*_PLAN_*.md` | Predeclared scope, prohibitions, metrics | Read only for the owning test. |
| Test results | `APTF_TEST_*_RESULT_*.md` | Human-readable authoritative findings | Latest result, then relevant ancestor. |
| Decisions/recommendations | `*_DECISION_*.md`, `*_NEXT_TEST_RECOMMENDATION_*.md` | Promotion or stop decisions | Use with result/summary, not alone. |
| Runtime architecture | `APTF_RUNTIME_*.md`, `APTF_TEMPORAL_*.md` | General runtime, identity, timing, position semantics | `APTF_RUNTIME_AUTHORITY_MAP_V0_1.md`, `APTF_RUNTIME_CORE_ARCHITECTURE_V0_1.md` |
| SPY cockpit specifications | `APTF_SPY_*.md` | Observation, cockpit, paper-account, roadmap boundaries | Cockpit spec and current roadmap. |
| Component design | `D01_*`, `D02_*`, `D03_*`, `D04_*` | Detailed component contracts and rationale | Current canonical design/freeze for component. |
| Historical phase handoffs | `APTF_PHASE_2_*` | Earlier integrated D01-D04/controller milestone | Read only when working on that lineage. |

## Root JSON Files

| Group | Typical Pattern | Use |
|---|---|---|
| Source authority | `*_SOURCE_AUTHORITY_*.json`, data manifests | Dataset identity, boundary, schema, hashes |
| Runtime authority | `*_RUNTIME_AUTHORITY_*.json`, `*_FREEZE_MANIFEST_*.json` | Owning implementation and mutation prohibition |
| Validation freeze | `*_VALIDATION_FREEZE_*.json`, `*_POLICY_FREEZE_*.json` | Pre-reveal model/policy definition |
| Policy configuration | `*_EMISSION_POLICY_*.json`, `APTF_SPY_EXECUTION_POLICY_SCHEMA_V0_1.json` | Frozen observer policy or inactive downstream schema |
| Summaries | `*_SUMMARY_*.json` | Machine-readable classifications and metrics |
| Acceptance gates | `*_ACCEPTANCE_GATES_*.json` | Integrity and contract checks |
| Immutability | `*_PRETEST_HASHES_*.json`, `*_RUNTIME_IMMUTABILITY_*.json` | Before/after authority protection |
| Artifact hashes | `*_ARTIFACT_HASHES_*.json` | Final evidence inventory |
| Interface contracts | `*_CONTRACT_*.json`, `*_SCHEMA_*.json` | Field-level interoperability |
| Position transitions | `APTF_POSITION_TRANSITION_*` | Historical matrix, vectors, and plan schema |

Current SPY contracts are `APTF_SPY_MARKET_OBSERVATION_CONTRACT_V0_1.json` and `APTF_SPY_PRICE_EMISSION_CONTRACT_V0_1.json`. Current cockpit policies are `APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json` and `APTF_TEST_014C_SPY_V_EMISSION_POLICY_V0_1.json`. `APTF_SPY_EXECUTION_POLICY_SCHEMA_V0_1.json` is explicitly inactive and defines no Test-014 rules.

## Root CSV Files

| Family | Role | Examples | Classification |
|---|---|---|---|
| External market inputs | Raw OHLCV | `QQQ_1min_firstratedata.csv`, `DIA_1min_firstratedata.csv` | INPUT / read-only |
| Derivative observations | Causal P/P1/P2 or V/V1/V2 states | `APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv` | INTERMEDIATE EVIDENCE |
| Engine emissions | Numerical and cockpit outputs | `APTF_TEST_014B_SPY_P_ENGINE_EMISSIONS_V0_2.csv`, `APTF_TEST_014C_SPY_V_ENGINE_EMISSIONS_V0_1.csv` | FINAL EVIDENCE |
| Projections | One-step/RK endpoints and stability | `APTF_TEST_011_PRICE_RK45_PROJECTIONS_V0_1.csv` | EXPERIMENTAL EVIDENCE |
| Scorecards | Candidate and validation comparisons | `*_SCORECARD_*.csv` | FINAL SUMMARY EVIDENCE |
| Transition analysis | Turns, crossings, lead/lag | `*_TRANSITION_*.csv`, `*_CROSSING_*.csv` | RETROSPECTIVE EVIDENCE |
| Interval analysis | P, V, joint intervals and reaction windows | `APTF_TEST_014C_SPY_*_INTERVALS_V0_1.csv` | FINAL EVIDENCE |
| Economic experiment | Trade ledger and gross P&L | `APTF_TEST_008_*_V0_2.csv` | HISTORICAL EXPERIMENT; not live account input |

## Input Data Sources

| File | Instrument | Granularity | Rows | Range in File | Schema | Role | Status |
|---|---|---:|---:|---|---|---|---|
| `data/market/raw/SPY_1min_firstratedata.csv` | SPY | 1 minute | 207,824 | 2022-09-30 04:00 to 2023-09-29 19:48 local source timestamps | OHLCV | Raw source | FROZEN / read-only |
| `data/market/normalized/SPY_1min_normalized_v0_1.csv` | SPY | 1 minute | 207,824 | 2022-09-30T08:00Z to 2023-09-29T23:48Z | 22-field normalized schema | Primary governed input | FROZEN / read-only |
| `QQQ_1min_firstratedata.csv` | QQQ | 1 minute | 210,482 | 2022-09-30 04:00 to 2023-09-29 19:47 | OHLCV | Test 013B external validation | FROZEN evidence input |
| `DIA_1min_firstratedata.csv` | DIA | 1 minute | 119,715 | 2022-09-30 04:00 to 2023-09-29 17:22 | OHLCV | Test 013C external replication | FROZEN evidence input |

No EEM or VXX dataset is present. The SPY normalized manifest defines a 106,603-row development/first-sample partition and 101,221-row reserve partition. Later tests used authorized subsets according to their own frozen contracts; do not infer that every post-boundary row remains globally untouched after completed reserve and cockpit tests.

## Market Data Schema

Raw external files use `timestamp, open, high, low, close, volume`. The normalized SPY file adds entity, UTC/local timestamps, timezone, returns/ranges, session type, regular-session flag, minute-of-session, source provenance, validity, and quality flags.

- Current P is the observed SPY `close` represented as `p` in Price emissions.
- Current V begins from source `volume`, preserved as `V_RAW`, then normalized to `V_N` by trailing-15-observation median.
- Normalized timestamps use UTC `Z` plus `America/New_York` local time.
- Session identity combines date and session label. Session changes and non-60-second gaps terminate intervals.

## Generated Evidence and Output Data

Generated evidence includes normalized observations, D01 state outputs, ReturnShapes, D04 evaluations, decisions, position episodes, gross-P&L experiments, derivative time series, Price/Volume model comparisons, RK projections, candidate scorecards, external-instrument replication, cockpit emissions, interval tables, transition timing, reaction windows, and charts.

These files are audit evidence, not a generic runtime database. Row-level CSVs are often large and should not be loaded unless a task requires their exact observations. Charts are human review evidence and must not become silent policy-retuning input. `output/SPY_APTF_position_actions_development_v0_2.csv` and its JSONL ledger belong to the older Phase 2 D01-D04 integration path, not the current P/V cockpit path.

## Runtime-Oriented Code

| Path | Main Interface | Responsibility | Status / Authority |
|---|---|---|---|
| `aptf_runtime/src/aptf_runtime/runtime.py` | `RuntimeCore.process(Observation)` | General frozen emitter/position runtime | FROZEN by Runtime Core manifest/Test 007A |
| `aptf_runtime/src/aptf_runtime/emitter.py` | `AdaptiveEmitter` | Historical adaptive BUY/SELL/HOLD emission | FROZEN |
| `aptf_runtime/src/aptf_runtime/context.py` | `RollingContext` | 15-observation causal context | FROZEN |
| `aptf_runtime/src/aptf_runtime/position.py` | `apply_position_decision` | Long-only state-relative position update | FROZEN |
| `aptf_runtime/src/aptf_runtime/single_observation_pipeline.py` | single-observation pipeline | D01-D04-D03-controller orchestration | IMPLEMENTED historical lineage |
| `spy_price_engine/contracts.py` | `MarketObservation`, `PriceEmission` | SPY cockpit input/output contracts | IMPLEMENTED / Test 014 |
| `spy_price_engine/engine.py` | `PriceEngine.observe` | Validates SPY observation and emits policy result from numerical trajectory | IMPLEMENTED |
| `spy_price_engine/policy.py` | `EmissionPolicy` | Test-014 V0.1 numerical-to-color policy | PRESERVED historical cockpit policy |
| `spy_price_engine/cockpit.py` | `PriceCockpitInterpreter.observe` | Test-014B V0.2 P cockpit refinement | CONDITIONAL / frozen policy |
| `spy_volume_engine/engine.py` | `VolumeEngine.observe` | Independent V activity/color emission | READY / Test 014C frozen policy |
| `emission_intervals.py` | `EmissionIntervalizer.observe` | Causal interval age and completed intervals | IMPLEMENTED / Test 014C validated |
| `position_transition_controller/position_transition_controller.py` | `PositionTransitionController.derive_transition_plan` | Historical D03 desired-state to canonical verbs | IMPLEMENTED / separate frozen lineage |
| `d01_adaptive_parametric_model/src/d01/v02/` | `D01V02Model.step` | Adaptive market-state computation | FROZEN |
| `d02_return_shape/src/d02/v02/` | `build_return_shape` | Deterministic ReturnShape construction | FROZEN |
| `d04_trading_envelope/src/aptf_d04/` | `TradingEnvelope.process` | Capturability, aperture, lifecycle | FROZEN |
| `d03_decision_control/src/d03/v01/` | `evaluate_decision` | Deterministic desired-position decision | FROZEN |

## SPY Price Engine

The numerical state is $X_P=[P,P1,P2]$: observed close, causal first derivative, and causal second derivative. The current cockpit evidence uses `F4_L1_W30`, a centered/scaled affine ridge vector field with ridge $\lambda=1$ and 30 contiguous targets. It is refit causally and propagated one minute with RK45 only across eligible intraday contiguous observations. The projected endpoint provides projected P/P1/P2 and deltas; the next real observation remains authoritative.

`PriceEmission` also records current/projected direction and acceleration, trajectory phase, turning tendency, domain/stability/confidence, color/reasons, RK success, condition number, Jacobian maximum-real eigenvalue, and perturbation amplification. `PriceEngine.observe` accepts a `MarketObservation`, a same-timestamp numerical trajectory, and policy state.

The mathematical Price emission and P cockpit interpretation are separate. Test 014B's `PriceCockpitInterpreter` creates a scale-aware zero-proximity and deceleration interpretation with direction-change AMBER bridging. Its frozen policy SHA-256 is `bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef`. Classification: **SPY_P_ENGINE_COCKPIT_CONDITIONAL**. It improved readability but retained weak turn recall and false-warning limitations.

## SPY Volume Engine

Tests 009V and 010 established Volume as an independent discrete observer. Test 014C added the cockpit runtime interface and froze `V_EMISSION_V0_1`.

- `V_RAW` is source `volume`.
- $V=V_N=V_RAW / median(last\ 15\ V_RAW)$, including the current observation.
- V1 and V2 are causal derivatives from a three-observation quadratic fit.
- Projected V is the discrete point observer's current V_N; projected V1/V2 are unsupported and remain `None`.
- No Volume ODE or RK45 is used.
- The selected cockpit uses the causal 15-row interval-mean V_N, thresholds 0.90/1.10, and two-observation confirmation.

GREEN means activity above the baseline band, RED below it, and AMBER near baseline or pending confirmation. V's frozen policy SHA-256 is `f719134f241b00888099e237c02f237a2db4b59f02b25ea5498c51006991bcd8`. On untouched Test-014C validation it produced 50.7278% GREEN, 40.8214% AMBER, 8.4508% RED, 0 INVALID, and a seven-minute overall median interval. Classification: **SPY_V_ENGINE_COCKPIT_READY**.

## Cockpit Emissions

A numerical emission carries continuous state, projection, diagnostics, and descriptive phase. A cockpit emission maps that evidence to GREEN, AMBER, RED, or INVALID plus reason codes. INVALID preserves failed or non-finite observations rather than forcing a market interpretation.

Colors are observational categories, never orders. Reason codes explain state, transition evidence, confirmation, domain caution, or invalidity. Causal interval age counts contiguous observations in the current color. Completed interval duration is retrospective.

## Emission Intervalization

`emission_intervals.py` implements bounded state for P, V, and descriptive joint streams. `EmissionIntervalizer.observe` continues an interval only when session, categorical state, and exact 60-second continuity all match. Color changes, session changes, and missing-minute gaps complete the old interval and start a new age at one.

`duration_minutes` is the observation count under one-minute contiguity. `elapsed_seconds` is end minus start and is therefore zero for a one-observation interval. Test 014C assigned all 55,199 combined observations exactly once in each P, V, and joint timeline with no overlap, omission, session crossing, or missing-minute bridging. The interval output supports visual/manual review of persistence and transition timing; it does not predict final duration.

## Execution Controller

The **future SPY cockpit Execution Controller is NOT IMPLEMENTED**. `APTF_SPY_EXECUTION_POLICY_SCHEMA_V0_1.json` is inactive and defines no Test-014 rules. Its intended inputs are independent P/V color-age observations, current long-only position state, and a versioned JSON policy. Intended outputs are a requested action and position transition, later consumable by a paper account.

The repository also contains an **implemented historical** `PositionTransitionController` that consumes committed D03 desired position plus FLAT/LONG/SHORT actual position and emits canonical verbs. It does not consume P/V cockpit emissions. Preserve this distinction when reusing code: compatibility must be designed and tested, not assumed.

## Position State Semantics

The frozen Runtime Core long-only truth table is:

| Before | Emission | After | Execution intent |
|---|---|---|---|
| FLAT | BUY | LONG | BUY |
| FLAT | HOLD | FLAT | NONE |
| FLAT | SELL | FLAT | NONE |
| LONG | BUY | LONG | NONE |
| LONG | HOLD | LONG | NONE |
| LONG | SELL | FLAT | SELL |

HOLD means no state change, not necessarily holding shares. The future SPY execution-policy schema is also long-only and sets `short_allowed: false`. In contrast, the historical D03 Position Transition Controller includes SHORT and six canonical verbs. This is a real contract difference, not an error to silently normalize.

## Paper Trading

Paper trading is **NOT IMPLEMENTED** for the current P/V cockpit. `APTF_SPY_PAPER_ACCOUNT_SPECIFICATION_V0_1.md` is an inactive specification for starting cash, cash, shares, average entry, market value, realized P&L, unrealized P&L, equity, and immutable trade log. P&L must never feed back into P or V mathematics.

Test 008 is a completed historical gross-P&L experiment, not a reusable paper account. Under fixed 100-share, zero-cost, next-row-open assumptions it produced 2,051 trades and total gross P&L of -$2,303.73. It neither proved profitability nor implemented live account state.

## Real-Time System

**Current:** deterministic historical CSV replay, causal streaming-compatible observer interfaces, monotonic timestamp checks, an in-process D04 event bus/realtime loop/audit logger, and bounded P/V interval state.

**Not implemented/deployed:** live market-data adapter, Azure Event Hub transport, Scala real-time engine, broker connection, account authority, portfolio service, or production monitoring deployment. Azure/Scala references in design documents are compatibility intent only. No external service is required for current evidence replay.

## How APTF Tests Work

APTF tests are evidence-producing experiments as well as conventional unit tests. A typical test:

1. Audits prior authority and source identity.
2. Records pre-test hashes and prohibited mutations.
3. Writes a plan/freeze contract before scoring.
4. Replays observations chronologically through a causal interface.
5. Uses development data for candidate comparison where authorized.
6. Freezes the selected model/policy before validation access.
7. Reveals untouched or external validation once.
8. Produces row-level evidence, scorecards, transition analyses, and charts.
9. Evaluates acceptance gates.
10. Verifies runtime/prior-authority immutability.
11. Writes result, summary, and artifact-hash inventory.
12. Stops at the authorized boundary.

Conventional unit tests live inside packages. Repository-wide `python -m pytest -q` currently cannot collect all packages from the root because of 16 existing import-path errors across areas including `aptf_runtime`, `d03`, and `d04`; use package-local environments/configurations until that engineering issue is addressed separately.

## Typical Sol Test Execution Flow

Sol-style work begins by reading the prompt and nearest authority, not scanning every artifact. It locates the owning runner and source, verifies hashes, adds an isolated diagnostic, compiles/checks it, runs development, freezes the candidate, then runs the validation stage once. Finalization creates evidence, verifies immutability, and stops. For one-way reserve or already-completed validation, rerun is prohibited unless explicitly authorized.

Typical commands used in the repository include:

```powershell
python -m py_compile diagnostics\run_test_014c_validation.py
python diagnostics\run_test_014c_v_development.py   # only when authorized
python diagnostics\run_test_014c_validation.py      # frozen one-shot; do not casually rerun
Get-FileHash -Algorithm SHA256 .\<authority-file>
git status --short
git diff --check
```

## Diagnostic/Test Runners

| Script | Test | Purpose | Inputs | Outputs | Safe to rerun? | Notes |
|---|---|---|---|---|---|---|
| `diagnostics/run_test_006b_reserve.py` | 006B | One-way reserve emission replay | Frozen SPY reserve/emitter | reserve emissions/audits | **NO** | Completed one-way authority. |
| `diagnostics/run_test_007_episode_reconstruction.py` | 007 | Reconstruct long-only episodes | Test 006B emissions | episodes/occupancy | Only with authorization | Deterministic retrospective transform. |
| `diagnostics/run_test_007a_validation.py` | 007A | Runtime extraction equivalence | frozen Runtime/test evidence | equivalence/gates | Only with authorization | Package authority. |
| `diagnostics/run_test_008_structural_gate.py`, `run_test_008_economic_consequence.py` | 008 | Structural gate and gross P&L | Test 007 episodes | ledger/P&L | **NO** by default | Historical economic experiment. |
| `diagnostics/run_test_009_derivative_analysis.py` | 009 | Causal Price derivatives | SPY evidence | derivative/crossing analysis | No need | Completed analysis. |
| `diagnostics/run_test_009v_volume_selection.py`, `run_test_009v_multivariate_analysis.py` | 009V | Volume normalization/derivatives | SPY Price/Volume | Volume authority | No need | Established separation. |
| `diagnostics/run_test_010_price_engine.py`, `run_test_010_volume_engine.py`, `run_test_010_control_analysis.py` | 010 | Identify two engines | Test 009/009V evidence | model comparisons/emissions | No need | Frozen foundation. |
| `diagnostics/run_test_011_rk45_price.py`, `run_test_011_control.py` | 011 | RK45 propagation/stability | Test 010 state | projections/failures | No need | Found structural instability. |
| `diagnostics/run_test_012_baseline_diagnosis.py`, `run_test_012_candidates*.py` | 012 | Stabilization candidates | Test 011 evidence | F4 comparison | No need | Candidate selection completed. |
| `diagnostics/run_test_013_validation.py` | 013 | Chronological validation | small SPY tail | blocked evidence | **NO** | Contract blocked on cover. |
| `diagnostics/run_test_013b_qqq_validation.py` | 013B | QQQ external validation | QQQ raw CSV | replication evidence | **NO** | Completed frozen external validation. |
| `diagnostics/run_test_013c_dia_replication.py` | 013C | DIA replication | DIA raw CSV | replication evidence | **NO** | Completed frozen replication. |
| `diagnostics/run_test_014_policy_development.py`, `run_test_014_validation.py` | 014 | P cockpit V0.1 | SPY split/F4 | policy/emissions | **NO** | Validation already revealed. |
| `diagnostics/run_test_014b_development.py`, `run_test_014b_validation.py` | 014B | P cockpit V0.2 | frozen Test 014 | refined policy/evidence | **NO** | Validation already revealed. |
| `diagnostics/run_test_014c_v_development.py`, `run_test_014c_validation.py` | 014C | V policy and P/V intervals | frozen P/V authorities | V emissions/intervals/charts | **NO** | Formally closed. |

## Test Lineage

| Test | Objective and Main Result | Current Significance | Frozen? | Primary Files |
|---|---|---|---|---|
| 006B | One-way reserve validation: 101,206 actionable emissions; 0 causal violations; 120/120 PASS. | Foundation that frozen adaptive emission generalized operationally, not economically. | YES | `APTF_TEST_006B_RESULT_V0_1.md`, `APTF_TEST_006B_RUN_SUMMARY_V0_1.json` |
| 007 | Reconstructed 2,051 complete long-only episodes and state-relative HOLD semantics. | Defines FLAT/LONG position behavior and filters raw emissions from execution intent. | YES | `APTF_TEST_007_RESULT_V0_1.md`, `APTF_TEST_007_EPISODE_SUMMARY_V0_1.json` |
| 007A | Extracted Runtime Core with exact emitter/position equivalence; 120/120 PASS. | Current general Runtime Core authority. | YES | `APTF_TEST_007A_RESULT_V0_1.md`, `APTF_RUNTIME_CORE_FREEZE_MANIFEST_V0_1.json` |
| 008 | Fixed 100-share next-row-open experiment returned -$2,303.73 gross over 2,051 trades; 120/120 PASS. | Showed structural correctness does not imply positive economics; motivated trajectory timing study. | YES | `APTF_TEST_008_RESULT_V0_2.md`, `APTF_TEST_008_PNL_SUMMARY_V0_2.json` |
| 009 | Causal Price derivative analysis selected trailing window 15; turning alignment was mixed; 73/73 PASS. | Established P/P1/P2 derivative evidence and transition questions. | YES | `APTF_TEST_009_RESULT_V0_1.md`, `APTF_TEST_009_SUMMARY_V0_1.json` |
| 009V | Evaluated Volume normalization/derivatives independently. | Established trailing-median normalized V and strict Price/Volume separation. | YES | `APTF_TEST_009V_RESULT_V0_1.md`, `APTF_TEST_009V_SUMMARY_V0_1.json` |
| 010 | Identified affine Price dynamics and discrete Volume point observer; 120/120 PASS, dual-engine foundation CONDITIONAL. | Created two-engine architecture; Volume RK rejected. | YES | `APTF_TEST_010_RESULT_V0_1.md`, `APTF_TEST_010_SUMMARY_V0_1.json` |
| 011 | One-minute RK45 exposed extreme P2 instability and worsened baseline; 140/140 integrity PASS. | Proved solver convergence did not cure vector-field instability. | YES | `APTF_TEST_011_RESULT_V0_1.md`, `APTF_TEST_011_SUMMARY_V0_1.json` |
| 012 | F4 L1 W30 materially stabilized P2 tails/Jacobians but remained a conditional candidate. | Current Price-model method authority later carried into cockpit evidence. | YES | `APTF_TEST_012_RESULT_V0_1.md`, `APTF_TEST_012_PRICE_VECTOR_FIELD_DECISION_V0_1.md` |
| 013 | Planned chronological tail validation was BLOCKED: 11 W30 rows and 0 W60 common cover. | F4 was neither validated nor failed by this SPY tail. | YES | `APTF_TEST_013_RESULT_V0_1.md`, `APTF_TEST_013_VALIDATION_DECISION_V0_1.md` |
| 013B | QQQ external validation reproduced F4 stabilization; 176/176 PASS, conditional external validation. | Supported method generalization without coefficient transfer. | YES | `APTF_TEST_013B_RESULT_V0_1.md`, `APTF_TEST_013B_SUMMARY_V0_1.json` |
| 013C | DIA replicated the three-instrument stabilization signature; 187/187 PASS, still conditional. | Strengthened cross-instrument evidence; did not authorize universality. | YES | `APTF_TEST_013C_RESULT_V0_1.md`, `APTF_TEST_013C_SUMMARY_V0_1.json` |
| 014 | Added SPY Price runtime contracts and V0.1 cockpit; 130/130 PASS but high AMBER/chatter and weak recall. | Established additive PriceEmission interface; classification CONDITIONAL. | YES | `APTF_TEST_014_RESULT_V0_1.md`, `APTF_TEST_014_SUMMARY_V0_1.json` |
| 014B | V0.2 reduced AMBER 62.56% to 17.03% and changes/session 134.49 to 112.38, while maxima/minima recall fell to 13.55%/13.80%; 116/116 PASS. | P cockpit remains `SPY_P_ENGINE_COCKPIT_CONDITIONAL`. | YES | `APTF_TEST_014B_RESULT_V0_1.md`, `APTF_TEST_014B_SUMMARY_V0_1.json` |
| 014C | Added independent V V0.1, causal P/V intervals, five charts; 139/139 PASS. V READY and P/V observation READY. | Completed observational boundary; no fusion or execution. | YES | `APTF_TEST_014C_RESULT_V0_1.md`, `APTF_TEST_014C_SUMMARY_V0_1.json` |

## Acceptance Gate System

`APTF_TEST_*_ACCEPTANCE_GATES_*.json` records contract-specific checks such as source identity, policy freeze, row/session counts, causality, interval invariants, prohibited features, deterministic replay, and immutability. `N/N PASS` means all declared checks passed. It does not mean the empirical model met READY criteria. Test 011 passed all execution gates yet found RK behavior inadequate; Test 014B passed 116/116 while classifying P CONDITIONAL.

## Test Classifications

- **READY:** evidence supports the stated observational use, not all downstream uses. Example: Test-014C V cockpit.
- **CONDITIONAL:** valid evidence with unresolved scientific limitations. Example: P V0.2 turn recall/false warnings.
- **FAILED:** a declared requirement was evaluated and failed.
- **BLOCKED:** the required evaluation could not validly occur. Test 013 was blocked by insufficient W60/multi-session cover.
- **PASS:** acceptance/integrity status, orthogonal to the scientific classification.

## Immutability and Hashing

Pre-test hashes establish the incoming authority. Freeze manifests record policy/model/configuration before validation. Runtime immutability artifacts compare prior files after execution. Artifact-hash inventories seal final evidence. Typical patterns are `*_PRETEST_HASHES_*.json`, `*_POLICY_FREEZE_*.json`, `*_RUNTIME_IMMUTABILITY_*.json`, and `*_ARTIFACT_HASHES_*.json`.

Current cockpit policy authorities:

- P V0.2: `bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef`.
- V V0.1: `f719134f241b00888099e237c02f237a2db4b59f02b25ea5498c51006991bcd8`.
- Test 014C: 139/139 acceptance gates and 27/27 final artifact hashes verified at formal closeout.

## Development and Validation Discipline

Development and validation are chronological or external according to a predeclared contract. Candidate thresholds are selected only on development data. The selected policy is serialized and hashed before validation is read. Validation is not used for retuning. External QQQ/DIA work refit local coefficients; it did not transfer SPY coefficients.

Retrospective outcomes, turns, final interval duration, and P&L may score prior emissions but cannot enter same-time causal behavior. This separation limits leakage and preserves the meaning of untouched validation.

## Causality Rules

- At time $t$, consume only observations at or before $t$ and prior bounded runtime state.
- Use trailing-only derivative windows; no centered future smoothers.
- Commit projections before revealing the next observation.
- Never replace the next real state with the prior projected state.
- Do not integrate RK through non-one-minute gaps or session boundaries.
- Reset state where the owning contract requires session reset.
- Never expose final interval duration as a live feature.
- Keep future turns, outcome labels, and P&L in retrospective evaluators.
- Keep P and V mathematical identification independent unless a new test explicitly changes authority.

## Frozen Authorities — Do Not Modify Casually

| Authority | Path | Status |
|---|---|---|
| SPY raw/normalized source | `data/market/` manifests and CSVs | FROZEN |
| Runtime Core | `aptf_runtime/src/aptf_runtime/`, `APTF_RUNTIME_CORE_FREEZE_MANIFEST_V0_1.json` | FROZEN |
| D01/D02/D03/D04 | package sources plus implementation freeze JSONs | FROZEN |
| Long-only runtime position semantics | `APTF_RUNTIME_POSITION_SEMANTICS_V0_1.md` | FROZEN |
| Historical transition controller | `position_transition_controller/` plus transition freezes | FROZEN lineage |
| P/P1/P2 and F4 L1 W30 evidence | Tests 009-014 authority/result files | FROZEN evidence |
| One-minute RK45 contract | Tests 011-014 method/authority files | FROZEN for cockpit evidence |
| MarketObservation/PriceEmission | `spy_price_engine/contracts.py` and root contracts | IMPLEMENTED authority |
| P cockpit V0.2 | `APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json` | FROZEN / CONDITIONAL |
| V cockpit V0.1 | `APTF_TEST_014C_SPY_V_EMISSION_POLICY_V0_1.json` | FROZEN / READY |
| Test evidence | `APTF_TEST_*` result/summary/hash families | IMMUTABLE |

## Conditional / Experimental Components

- P cockpit V0.2: lower AMBER and chatter, but poor turn recall and roughly 53-56% false candidate rates.
- F4 continuous field: materially stabilized and externally replicated, but strict local-domain exits remain near 45% and transition recall remains weak.
- RK45: acceptable as the frozen one-minute trajectory mechanism in the cockpit study, not general authorization for control propagation.
- Confidence/domain categories: deterministic caution labels, not calibrated probabilities.
- Historical D01-D04 real-integration replay: implemented evidence, not proof of live deployability or profitability.

## Not Yet Implemented

- P/V cockpit Execution Controller and active JSON policy.
- P/V-driven position interaction and internal paper account.
- Cost-aware current-cockpit historical replay.
- Live market-data vendor adapter.
- Azure Event Hub deployment and Scala real-time service.
- Broker/account integration, order management, and reconciliation.
- Portfolio/multi-instrument execution layer.
- Production telemetry/operations around the cockpit path.

## Fast Start for a New Agent

1. `APTF_REPOSITORY_HANDOFF.md` - current map and boundaries.
2. `APTF_SPY_REALTIME_COMPLETION_ROADMAP_V0_1.md` - current SPY status.
3. `APTF_TEST_014C_RESULT_V0_1.md` - latest human-readable result.
4. `APTF_TEST_014C_SUMMARY_V0_1.json` - latest machine-readable status.
5. `APTF_TEST_014C_ARTIFACT_HASHES_V0_1.json` - final evidence inventory.
6. `APTF_TEST_014B_RESULT_V0_1.md` - P cockpit limitations.
7. `APTF_TEST_014B_SUMMARY_V0_1.json` - exact P metrics/hash.
8. `APTF_TEST_014C_V_AUTHORITY_V0_1.json` - Volume mathematics.
9. `APTF_TEST_012_PRICE_VECTOR_FIELD_DECISION_V0_1.md` - F4 definition/caveats.
10. `APTF_RUNTIME_AUTHORITY_MAP_V0_1.md` - general runtime ownership.
11. `APTF_RUNTIME_CORE_ARCHITECTURE_V0_1.md` - historical runtime structure.
12. `APTF_RUNTIME_POSITION_SEMANTICS_V0_1.md` - long-only HOLD semantics.
13. `APTF_SPY_EXECUTION_POLICY_SCHEMA_V0_1.json` - inactive downstream boundary.
14. `APTF_SPY_PAPER_ACCOUNT_SPECIFICATION_V0_1.md` - inactive account boundary.
15. `spy_price_engine/contracts.py` - current observation/emission types.
16. `spy_price_engine/cockpit.py` - P cockpit interpreter.
17. `spy_volume_engine/engine.py` - V cockpit implementation.
18. `emission_intervals.py` - causal interval contract.

## Files Usually Safe to Skip Initially

Skip large row-level emissions/projection CSVs, historical trace JSONs, old candidate scorecards, chart images, and package output folders until a task names them. They remain immutable evidence and should be opened for exact authority or regression checks. Do not delete or consolidate them for tidiness.

## Current Working Set

Current work is documentation/decision preparation after Test 014C. The relevant set is this handoff, the SPY roadmap, Test-014B/014C result-summary-policy files, `spy_price_engine/`, `spy_volume_engine/`, `emission_intervals.py`, and inactive execution/paper specifications. Test 014C has no active runner process and must not be rerun merely to resume work.

## Common Commands

```powershell
# Inspect state
git branch --show-current
git status --short
git diff --check

# Verify an authority hash
Get-FileHash -Algorithm SHA256 .\APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json

# Compile a narrowly changed Python file
python -m py_compile path\to\changed_file.py

# Run package-local tests only when authorized and environment paths are configured
Push-Location aptf_runtime
python -m pytest -q
Pop-Location
```

Do not use a frozen diagnostic runner as a routine smoke test. Root-level pytest currently has 16 known collection errors due to monorepo import paths.

## Runtime / Development Dependencies

Python packages require Python `>=3.11`. Declared dependencies include Pydantic `>=2.8`, NumPy `>=1.26`, PyYAML `>=6.0`, Rich `>=13.0`, and package-local dependencies among D01-D04. Development extras use pytest `>=8.0` and, for `aptf_runtime`, jsonschema `>=4.0`.

Diagnostics also import SciPy for RK45 and Matplotlib for charts; these are used by evidence runners but are not declared in a root environment file. There is no single root `pyproject.toml`. Use package `pyproject.toml` and requirements files, and verify diagnostic dependencies before an authorized run.

## External Services and Integrations

**CURRENT:** none required; inputs are local CSV files and event routing is in-process.

**PLANNED/DESIGN ONLY:** live market-data vendor, Azure Event Hub compatibility, Scala real-time engine, broker interface, account-position authority, and production telemetry. Do not claim these are deployed.

## Current SPY Data Flow

```text
SPY normalized/raw CSV
  -> MarketObservation(close=P, volume=V_RAW)
  -> causal Price derivative state [P,P1,P2]
  -> F4 L1 W30 local field
  -> one-minute eligible RK45 projection
  -> PriceEmission
  -> PriceCockpitInterpreter V0.2
  -> P color + causal interval age

SPY volume
  -> trailing-15 median normalization V_N
  -> causal V1/V2 + discrete projected V_N
  -> VolumeEngine V0.1
  -> V color + causal interval age

P and V rows align by timestamp
  -> descriptive joint state/intervals
  -> STOP: no execution rule
```

## SPY Cockpit Status

| Component | Status | Authority | Notes |
|---|---|---|---|
| MarketObservation | IMPLEMENTED | root contract + `spy_price_engine/contracts.py` | SPY OHLCV/session/source |
| P Engine math | FROZEN / CONDITIONAL use | Tests 012-014 | F4 L1 W30, RK45 one minute |
| PriceEmission | IMPLEMENTED | Test 014 | Numerical/descriptive, not action |
| P cockpit color | CONDITIONAL | Test 014B | V0.2, weak turn recall |
| V Engine | READY / FROZEN | Test 014C | Discrete, no RK, no Price input |
| V emission | IMPLEMENTED | Test 014C | V/V1/V2 plus activity color |
| Contiguous intervals | READY | Test 014C | P, V, joint; exact assignment |
| Dual P/V display evidence | READY | Test 014C charts | Observational only |
| Execution Controller | NOT IMPLEMENTED | inactive schema | Next separately authorized layer |
| Position State | HISTORICAL IMPLEMENTATION; cockpit integration absent | Runtime semantics/controller | Contract distinction required |
| Paper Account | NOT IMPLEMENTED | specification only | Test 008 is not this account |
| Live Feed | NOT IMPLEMENTED | roadmap/design only | CSV replay current |

## Cross-Instrument Research

SPY is the active cockpit instrument. QQQ Test 013B and DIA Test 013C replicated F4 stabilization without transferring coefficients; both remained conditional and do not form part of the current SPY runtime. EEM and VXX replication was not performed because no datasets are present. Cross-instrument work is paused relative to the current SPY completion path.

## Terminology

| Term | Project Meaning |
|---|---|
| Observation | Timestamped causal market input available now. |
| Emission | Immutable output from an observer/runtime stage. |
| PriceEmission | Numerical P state, projection, diagnostics, and policy descriptors. |
| Cockpit emission | GREEN/AMBER/RED/INVALID plus reasons; not an order. |
| Trajectory | Current-to-projected one-minute Price state path. |
| Phase | Descriptive motion/activity regime from derivatives. |
| Turning tendency | Evidence of acceleration opposing current Price direction. |
| Domain | Whether projected state remains in the local fitted support. |
| Confidence | Deterministic caution category, not probability. |
| Interval | Maximal same-session, same-state, exactly one-minute-contiguous run. |
| Interval age | Number of observations elapsed in the active run; causal. |
| Final interval duration | Completed run length; retrospective only. |
| Execution policy | Downstream mapping of observations and position to requested action. |
| Position state | Current exposure state, e.g. FLAT/LONG; separate authority. |
| HOLD | Preserve current position state. |
| Paper trade | Simulated account event under explicit execution assumptions. |

## Known Issues / Open Questions

- P cockpit remains CONDITIONAL: reduced AMBER came with maxima/minima recall near 13.6%/13.8% and false candidate rates above 53%.
- F4 projections still have substantial strict local-domain exits and positive Jacobian concerns despite major stabilization.
- Test 013's SPY chronological validation remains BLOCKED; later external replication does not retroactively create W60 SPY tail cover.
- No execution policy has been scientifically designed for P/V colors/ages.
- No current-cockpit cost, fill, account, or P&L evidence exists.
- Position semantics differ between long-only cockpit schema and historical SHORT-capable D03 controller.
- Root pytest has 16 known import-path collection errors.
- Diagnostic dependencies lack a single root environment declaration.
- Working tree is DIRTY; inspect ownership before editing or committing.

## Why Historical Test Artifacts Are Preserved

The root evidence records scientific lineage, exact decisions, regressions, blocked paths, immutable hashes, and reproducible intermediate results. Preserving failed, conditional, and superseded evidence prevents hindsight rewriting and enables future agents to explain why an authority exists. Artifact volume is therefore intentional; it is not a cleanup backlog.

## Recommended Change Discipline

- Add a new test/version for changed behavior; do not overwrite frozen policy or result files.
- Hash authorities before and after an experiment.
- Separate runtime modules from diagnostic runners and generated evidence.
- Freeze policy/model configuration before validation reveal.
- Keep P/V observer work separate from execution-policy work.
- Commit coherent completed tests when authorized; do not mix unrelated dirty-tree changes.
- Use branch isolation for parallel agents and inspect `git status` before every edit.
- Stop at the prompt's test boundary.

## Instructions for AI Coding Agents

1. Read this file, the latest result, and latest summary first.
2. Do not rescan hundreds of artifacts unless an authority remains ambiguous.
3. Treat result, summary, freeze, hash, and authority-map files as a set.
4. Never infer READY from acceptance PASS.
5. Do not modify frozen tests, datasets, policies, or evidence without explicit versioned authorization.
6. Do not mix P and V mathematics or use one to retune the other.
7. Do not implement execution while an observer-only task forbids it.
8. Keep future duration, outcomes, and P&L out of causal inputs.
9. Distinguish the historical D03 controller from the future P/V cockpit controller.
10. Run only the narrow authorized check; one-way validation is not a regression test.
11. Preserve user/other-agent dirty-tree changes.
12. Stop at the declared stop condition and report unresolved conflicts.

## Human Handoff Checklist

- [ ] Pull or otherwise confirm the latest Git state.
- [ ] Confirm branch, commit, and dirty working tree.
- [ ] Read this handoff and current SPY roadmap.
- [ ] Read the latest completed result and summary.
- [ ] Identify the owning test for proposed work.
- [ ] Verify frozen hashes before changing behavior.
- [ ] Confirm allowed edit scope and validation access.
- [ ] Separate historical evidence from current runtime code.
- [ ] Record environment/package paths before running tests.
- [ ] Use a separate branch/worktree for parallel Copilot, Cursor, machine, or engineer activity.

## Current Next Step

Test 014C recommends human review of the five full-session charts, short-interval tails, joint-state persistence, and descriptive transition separation before defining execution policy. The P/V observation interface is ready to serve as input to Execution Controller development. The next action is therefore a **separately authorized Execution Controller design/freeze task**, not immediate BUY/SELL rule implementation, backtesting, paper trading, or broker work.

## Appendix A — Important File Index

| File | Category | Role | Read Priority | Frozen? | Notes |
|---|---|---|---:|---|---|
| `APTF_REPOSITORY_HANDOFF.md` | handoff | Current repository map | 1 | No | Update only for current status. |
| `APTF_SPY_REALTIME_COMPLETION_ROADMAP_V0_1.md` | status | SPY completion state | 2 | Current doc | 014C formally closed. |
| `APTF_TEST_014C_RESULT_V0_1.md` | result | Latest human authority | 3 | YES | V/PV READY. |
| `APTF_TEST_014C_SUMMARY_V0_1.json` | summary | Latest machine status | 4 | YES | Exact metrics/invariants. |
| `APTF_TEST_014C_ARTIFACT_HASHES_V0_1.json` | hashes | 27-file final inventory | 5 | YES | Verify before relying on evidence. |
| `APTF_TEST_014C_ACCEPTANCE_GATES_V0_1.json` | gates | 139 integrity gates | 6 | YES | PASS is not trading readiness. |
| `APTF_TEST_014B_RESULT_V0_1.md` | result | P cockpit decision | 7 | YES | Conditional limitations. |
| `APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json` | policy | Current P cockpit | 8 | YES | Do not edit. |
| `APTF_TEST_014C_SPY_V_EMISSION_POLICY_V0_1.json` | policy | Current V cockpit | 8 | YES | Do not edit/create V0.2 casually. |
| `APTF_TEST_014C_V_AUTHORITY_V0_1.json` | authority | V/V1/V2 definitions | 8 | YES | Confirms no RK/Price input. |
| `APTF_TEST_012_PRICE_VECTOR_FIELD_DECISION_V0_1.md` | authority | F4 definition/caveats | 9 | YES | Read with later tests. |
| `APTF_RUNTIME_AUTHORITY_MAP_V0_1.md` | authority | General runtime ownership | 9 | YES | Historical runtime map. |
| `APTF_RUNTIME_CORE_FREEZE_MANIFEST_V0_1.json` | freeze | Runtime Core identity | 10 | YES | 007A lineage. |
| `APTF_RUNTIME_POSITION_SEMANTICS_V0_1.md` | contract | Long-only HOLD/state rules | 10 | YES | Cockpit-compatible semantics. |
| `APTF_SPY_MARKET_OBSERVATION_CONTRACT_V0_1.json` | contract | Market input schema | 10 | YES | SPY cockpit. |
| `APTF_SPY_PRICE_EMISSION_CONTRACT_V0_1.json` | contract | Price output schema | 10 | YES | Test 014. |
| `APTF_SPY_EXECUTION_POLICY_SCHEMA_V0_1.json` | schema | Future inactive policy | 11 | Design only | No active rules. |
| `APTF_SPY_PAPER_ACCOUNT_SPECIFICATION_V0_1.md` | spec | Future paper account | 11 | Design only | Not implemented. |
| `D01_STAGE_2_DATA_PARTITION_MANIFEST.json` | data authority | SPY partitions | 11 | YES | Preserve boundaries. |
| `APTF_PHASE_2_REAL_INTEGRATION_HANDOFF.md` | historical handoff | D01-D04/controller integration | 12 | Historical | Not current cockpit status. |

## Appendix B — Test Index

| Test | Status | Classification | Primary Result | Primary Summary | Key Contribution |
|---|---|---|---|---|---|
| 006B | COMPLETE | GENERALIZATION_VALIDATED | `APTF_TEST_006B_RESULT_V0_1.md` | `APTF_TEST_006B_RUN_SUMMARY_V0_1.json` | One-way reserve emission validation |
| 007 | COMPLETE | STRUCTURAL_RECONSTRUCTION_VALIDATED | `APTF_TEST_007_RESULT_V0_1.md` | `APTF_TEST_007_EPISODE_SUMMARY_V0_1.json` | HOLD/position episodes |
| 007A | COMPLETE | PRODUCTION_CORE_VALIDATED | `APTF_TEST_007A_RESULT_V0_1.md` | acceptance/equivalence JSONs | Runtime Core extraction |
| 008 | COMPLETE | PASS / negative economic result | `APTF_TEST_008_RESULT_V0_2.md` | `APTF_TEST_008_PNL_SUMMARY_V0_2.json` | Fixed-assumption gross P&L |
| 009 | COMPLETE | EMPIRICAL_ANALYSIS | `APTF_TEST_009_RESULT_V0_1.md` | `APTF_TEST_009_SUMMARY_V0_1.json` | Price derivatives |
| 009V | COMPLETE | EMPIRICAL_ANALYSIS | `APTF_TEST_009V_RESULT_V0_1.md` | `APTF_TEST_009V_SUMMARY_V0_1.json` | Volume separation |
| 010 | COMPLETE | DUAL_ENGINE_FOUNDATION_CONDITIONAL | `APTF_TEST_010_RESULT_V0_1.md` | `APTF_TEST_010_SUMMARY_V0_1.json` | P/V engine architecture |
| 011 | COMPLETE | CONDITIONAL_EXPERIMENTAL_RK_VALIDATION | `APTF_TEST_011_RESULT_V0_1.md` | `APTF_TEST_011_SUMMARY_V0_1.json` | RK instability discovery |
| 012 | COMPLETE | CONDITIONAL_STABILIZED_CANDIDATE_FOUND | `APTF_TEST_012_RESULT_V0_1.md` | `APTF_TEST_012_SUMMARY_V0_1.json` | F4 stabilization |
| 013 | BLOCKED | VALIDATION_BLOCKED | `APTF_TEST_013_RESULT_V0_1.md` | `APTF_TEST_013_SUMMARY_V0_1.json` | Insufficient SPY tail cover |
| 013B | COMPLETE | CONDITIONALLY_EXTERNALLY_VALIDATED | `APTF_TEST_013B_RESULT_V0_1.md` | `APTF_TEST_013B_SUMMARY_V0_1.json` | QQQ replication |
| 013C | COMPLETE | SECOND_EXTERNAL_REPLICATION_CONDITIONAL | `APTF_TEST_013C_RESULT_V0_1.md` | `APTF_TEST_013C_SUMMARY_V0_1.json` | DIA replication |
| 014 | COMPLETE | SPY_P_ENGINE_EMISSION_CONDITIONAL | `APTF_TEST_014_RESULT_V0_1.md` | `APTF_TEST_014_SUMMARY_V0_1.json` | PriceEmission/cockpit V0.1 |
| 014B | COMPLETE | SPY_P_ENGINE_COCKPIT_CONDITIONAL | `APTF_TEST_014B_RESULT_V0_1.md` | `APTF_TEST_014B_SUMMARY_V0_1.json` | P cockpit V0.2 refinement |
| 014C | COMPLETE | V READY / P-V OBSERVATION READY | `APTF_TEST_014C_RESULT_V0_1.md` | `APTF_TEST_014C_SUMMARY_V0_1.json` | Independent V and intervals |

## Appendix C — Data File Index

| File | Instrument | Input/Output | Rows | Role | Frozen? |
|---|---|---|---:|---|---|
| `data/market/raw/SPY_1min_firstratedata.csv` | SPY | Input | 207,824 | Raw OHLCV | YES |
| `data/market/normalized/SPY_1min_normalized_v0_1.csv` | SPY | Input | 207,824 | Governed normalized OHLCV | YES |
| `QQQ_1min_firstratedata.csv` | QQQ | Input | 210,482 | Test 013B external validation | YES |
| `DIA_1min_firstratedata.csv` | DIA | Input | 119,715 | Test 013C external replication | YES |
| `APTF_TEST_014B_SPY_P_ENGINE_EMISSIONS_V0_2.csv` | SPY | Output | 55,199 | Frozen P cockpit emissions | YES |
| `APTF_TEST_014C_SPY_V_ENGINE_EMISSIONS_V0_1.csv` | SPY | Output | 55,199 | Frozen V cockpit emissions | YES |
| `APTF_TEST_014C_SPY_PV_ALIGNED_EMISSIONS_V0_1.csv` | SPY | Output | 55,199 | Causal color/age alignment | YES |
| `APTF_TEST_014C_SPY_PV_JOINT_INTERVALS_V0_1.csv` | SPY | Output | 18,561 intervals | Descriptive joint intervals | YES |
| `output/SPY_APTF_position_actions_development_v0_2.csv` | SPY | Output | 106,603 | Historical D01-D04 integration | YES |
| `output/SPY_APTF_position_ledger_v0_2.jsonl` | SPY | Output | 106,603 | Historical position audit | YES |

## Appendix D — Runtime Module Index

| Path | Class/Function | Responsibility | Current Status | Owning Authority |
|---|---|---|---|---|
| `aptf_runtime/src/aptf_runtime/runtime.py` | `RuntimeCore` | General observation processing | FROZEN | Test 007A |
| `aptf_runtime/src/aptf_runtime/emitter.py` | `AdaptiveEmitter` | Historical decision emission | FROZEN | Tests 006B/007A |
| `aptf_runtime/src/aptf_runtime/context.py` | `RollingContext` | Causal 15-row context | FROZEN | Runtime Core |
| `aptf_runtime/src/aptf_runtime/position.py` | `apply_position_decision` | FLAT/LONG state update | FROZEN | Test 007/007A |
| `aptf_runtime/src/aptf_runtime/single_observation_pipeline.py` | pipeline functions | D01-D04-D03 integration | IMPLEMENTED | Temporal/Phase 2 authority |
| `d01_adaptive_parametric_model/src/d01/v02/` | `D01V02Model.step` | Adaptive state | FROZEN | D01 freezes |
| `d02_return_shape/src/d02/v02/` | `build_return_shape` | ReturnShape | FROZEN | D02 freeze |
| `d04_trading_envelope/src/aptf_d04/` | `TradingEnvelope.process` | Envelope lifecycle | FROZEN | D04 freeze |
| `d03_decision_control/src/d03/v01/` | `evaluate_decision` | Desired position decision | FROZEN | D03 freeze |
| `position_transition_controller/position_transition_controller.py` | `PositionTransitionController` | D03-to-verbs plan | IMPLEMENTED historical | Position freezes |
| `spy_price_engine/contracts.py` | `MarketObservation`, `PriceEmission` | SPY contracts | IMPLEMENTED | Test 014 |
| `spy_price_engine/engine.py` | `PriceEngine.observe` | Price interface | IMPLEMENTED | Test 014 |
| `spy_price_engine/policy.py` | `EmissionPolicy.emit` | P V0.1 interpretation | HISTORICAL | Test 014 |
| `spy_price_engine/cockpit.py` | `PriceCockpitInterpreter.observe` | P V0.2 cockpit | CONDITIONAL | Test 014B |
| `spy_volume_engine/engine.py` | `VolumeEngine.observe` | V V0.1 cockpit | READY | Test 014C |
| `emission_intervals.py` | `EmissionIntervalizer.observe` | Causal intervals | READY | Test 014C |

# Resume Work Here

1. **What is complete.** Test 014C is formally complete: V cockpit READY, P/V interval observation READY, 139/139 gates PASS, five charts generated, and 55,199 observations assigned exactly once in P/V/joint timelines.
2. **What is frozen.** Runtime Core and D01-D04 authorities, source datasets, historical test evidence, F4 cockpit trajectory authority, P V0.2 policy, V V0.1 policy, Test-014C outputs, and causal interval-age semantics.
3. **What is currently being worked on.** No test is active. The repository is at the decision boundary before separately authorized P/V Execution Controller design.
4. **What must not be changed.** Frozen source/evidence/policies; P/V independence; observed-state authority; one-minute/session/gap causality; the distinction between causal age and retrospective duration; P's CONDITIONAL status.
5. **What the next agent should do first.** Confirm branch/dirty-tree ownership, read this handoff plus Test-014C result/summary, verify P/V hashes, and obtain explicit scope for the next design task.
6. **What the next agent should NOT do.** Do not rerun 014C, retune P or V, create V0.2, infer trading rules from colors, implement execution/paper trading without authorization, access validation for tuning, or connect a broker.
7. **Which files to open first.** `APTF_REPOSITORY_HANDOFF.md`, `APTF_SPY_REALTIME_COMPLETION_ROADMAP_V0_1.md`, `APTF_TEST_014C_RESULT_V0_1.md`, `APTF_TEST_014C_SUMMARY_V0_1.json`, `APTF_TEST_014B_RESULT_V0_1.md`, the two frozen policy JSONs, `spy_price_engine/cockpit.py`, `spy_volume_engine/engine.py`, and `emission_intervals.py`.
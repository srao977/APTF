# D04 Existing Asset Inventory v0.2

## 1. Scope and status

**Status:** PRESERVATION AUDIT; DESIGN ONLY; NOT FROZEN

The complete `d04_trading_envelope` tree was inventoried without modifying source, tests, scenarios, configuration, or generated outputs. Generated JSONL contents and historical/reserve data were not inspected.

## 2. Authority hierarchy

```text
APTF Integrated System Design Authority v0.2
  -> frozen D01 / Q_t
  -> frozen D02 ReturnShape v0.2
  -> existing D04 physical prototype/design/test evidence
  -> proposed D04 modernization design v0.2
```

D04 has no freeze manifest, hash manifest, implementation freeze, or formal acceptance manifest. `D04_PHYSICAL_DESIGN_V0_1.md` is the principal local design reference; `README.md` is operational documentation. Both explicitly call scoring mathematics placeholder/experimental. Existing tests and scenarios are regression evidence, not frozen scientific authority.

## 3. Inventory counts

| Category | Count | Notes |
|---|---:|---|
| Relevant files excluding caches | 57 | Includes generated output artifacts |
| Design/documentation artifacts | 2 | Physical design and README |
| Python source modules including `__init__.py` | 26 | 18 non-`__init__` implementation modules |
| Test files | 7 | 23 collected tests |
| Scenario fixtures | 7 | Deterministic YAML |
| Configuration YAML files | 2 | Runtime/default and scenario registry |
| Output artifacts | 10 | `.gitkeep`, 8 ignored JSONL files, one text summary |
| Freeze/manifest/acceptance artifacts | 0 | None found |

## 4. Artifact inventory

| Relative path/group | Type | Purpose/status | Executable/tested | Dependencies | Modernization relevance |
|---|---|---|---|---|---|
| `D04_PHYSICAL_DESIGN_V0_1.md` | Physical design | Principal D04 design reference; prototype and v0.2 gate notes; not frozen | N/A | Existing source | Preserve as historical authority; modernization supersedes only interface/scoring deltas |
| `README.md` | Instructions/design summary | Prototype capabilities, limitations, commands | N/A | Entire package | Update only during implementation, not this task |
| `pyproject.toml`, `requirements.txt` | Project metadata | Python >=3.11, Pydantic, YAML, Rich, pytest | YES | Toolchain | Preserve |
| `config/default.yaml` | Configuration | Safety, hysteresis, old shape/envelope weights, gate, aperture | Loaded/tested | `configuration.py` | Shape weights/lifetime target require modernization; other sections mostly preserve |
| `config/scenarios.yaml` | Scenario registry | Seven synthetic scenario names | Loaded/tested | CLI | Preserve with fixture updates |
| `src/aptf_d04/configuration.py` | Typed config | Validates thresholds, weights, gate, aperture | YES/tested | YAML | Preserve structure; modernize old shape config |
| `src/aptf_d04/models/return_shape.py` | Public input model | Legacy 16-field synthetic ReturnShape | YES/tested | Pydantic/enums | Replace boundary with frozen 17-field D02 schema during implementation |
| `src/aptf_d04/models/envelope_context.py` | Public context model | Causal operational/execution/portfolio qualities | YES/tested | Pydantic | Preserve fields except untyped metadata; clarify evaluation time |
| `src/aptf_d04/models/capturability.py` | Result model | Components, gate, final score, reasons | YES/tested | Pydantic | Preserve score/gate concepts; component semantics/names need review |
| `src/aptf_d04/models/aperture.py` | Result model | Aperture result type | YES | Pydantic | Preserve |
| `src/aptf_d04/models/envelope_state.py` | Public output model | Evaluation/state transition contract | YES/tested indirectly | Pydantic/models | Modernize identity, retired shape echo, position/decision fields |
| `src/aptf_d04/models/events.py` | Generic event | Typed event with optional IDs/payload | YES/tested indirectly | Enums | Preserve event mechanism; align identity/payload |
| `src/aptf_d04/models/opportunity.py` | Candidate event | Qualified opportunity identity/reasons | YES/tested | Enums | Natural starting point for CandidateEnvelope; ownership remains D04 |
| `src/aptf_d04/models/enums.py` | Enums | Direction, envelope states, continuation, event types | YES/tested | None | Envelope state/event enums preserve; legacy direction and continuation semantics change |
| `src/aptf_d04/envelope/capturability_model.py` | Core math plug-in | Old shape weighted sum, envelope weighted sum, lifetime, minimum gate | YES/10 tests | Models/config | Preserve interface and gate; redesign shape/lifetime calculation |
| `src/aptf_d04/envelope/aperture_model.py` | Core math plug-in | Exponential smoothing of capturability | YES/1 test | Envelope state | Preserve unchanged |
| `src/aptf_d04/envelope/hysteresis.py` | Stateful controller | Four-state asymmetric threshold/persistence logic | YES/4 tests | Envelope state | Preserve unchanged |
| `src/aptf_d04/envelope/lifecycle.py` | Mapping helpers | State events and position-oriented continuation signals | YES/tested | Enums | Preserve transition mapping; move position decisions to D03 |
| `src/aptf_d04/envelope/trading_envelope.py` | Primary entry point | Safety, capture, hysteresis, aperture, state/events/candidate | YES/scenarios | All core modules | Preserve orchestration order with boundary/lifecycle/output adaptation |
| `src/aptf_d04/runtime/event_bus.py` | Runtime | In-process typed publish/subscribe | YES/tested indirectly | Events | Preserve unchanged |
| `src/aptf_d04/runtime/audit_log.py` | Runtime | JSONL audit record | YES/1 test | Models | Preserve mechanism; adapt schema, remove wall-clock from deterministic identity |
| `src/aptf_d04/runtime/realtime_loop.py` | Runtime | Ordered processing, event publication, audit, optional sleep | YES/scenarios | Envelope/runtime | Preserve event ordering; adapt fields and keep sleep outside science |
| `src/aptf_d04/inputs/scenario_loader.py` | Test/input utility | YAML loading | YES/tested | PyYAML | Preserve unchanged |
| `src/aptf_d04/inputs/synthetic_generator.py` | Test fixture adapter | Builds typed legacy shape/context observations/checksum | YES/scenarios | Models | Preserve utility concept with fixture adaptation |
| `src/aptf_d04/cli/main.py` | CLI/assembly | Builds component, runs/validates scenarios, benchmark | YES/scenarios | Entire package | Preserve assembly/runner pattern; adapt interface/config |
| `tests/test_*.py` | Regression suite | 23 unit/component/scenario tests | YES; 23/23 baseline | Source/scenarios | Preserve tests according to migration plan |
| `scenarios/*.yaml` | Fixtures | Seven deterministic behavior cases | YES | Generator/CLI | Preserve scenario intent with canonical fixtures |
| `output/*.jsonl` | Generated audit output | Prior scenario/benchmark logs | Generated; not authority | Runtime | Do not treat as design evidence; not inspected |
| `output/run_all_v02.txt` | Generated summary | Prior run-all console output | Generated; not frozen | CLI | Historical regression metadata only |

## 5. Existing authority conclusion

The repository contains a substantial executable physical prototype with passing deterministic tests, but no frozen D04 design or implementation authority. The existing design governs preservation intent only where it remains consistent with system authority and frozen D02. The proposed modernization must not silently rewrite the preserved implementation.

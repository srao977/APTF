# D02 D01-to-D04 ReturnShape Mapping v0.1

## 1. Decision status

**Status:** DESIGN AMBIGUITY; NOT FREEZE-READY  
**Machine-readable companion:** `D02_D01_TO_D04_RETURNSHAPE_MAPPING_V0_1.json`

The mapping uses only frozen Q_t fields and the concrete D04 `ReturnShape` model. A classification does not authorize a trading claim or override Stage 2 evidence status.

## 2. Classification summary

| Classification | Count |
|---|---:|
| DIRECT | 3 |
| DETERMINISTIC_TRANSFORMATION | 2 |
| FMO_GEOMETRY_DERIVATION | 0 |
| CONSTANT_OR_CONFIGURATION | 1 |
| CONTEXT_NOT_D02 | 1 |
| GENUINE_D02_MATHEMATICAL_GAP | 8 |
| OBSOLETE_OR_DUPLICATIVE | 1 |
| **Total** | **16** |

No mandatory D04 scalar is classified as `FMO_GEOMETRY_DERIVATION` because no complete, already-authorized path-to-scalar formula exists. FMO samples contain useful geometry, but selecting horizons, normalizations, aggregation rules, and neutral/validity boundaries would introduce new scientific choices.

## 3. Field-by-field mapping

| D04 field | Classification | D01 source(s) | Defined mapping or missing choice | Causal | Information loss | Evidence | Recommendation |
|---|---|---|---|---:|---|---|---|
| `return_shape_id` | DETERMINISTIC_TRANSFORMATION | `entity_id`, `model_version` | Stable stream ID; serialization protocol not yet fixed | YES | None | N/A | Define collision-safe engineering identity |
| `candidate_id` | CONTEXT_NOT_D02 | None | Candidate/control identity is absent from Q_t | YES if supplied causally | N/A | N/A | Place in D04/D03 control boundary |
| `version` | DETERMINISTIC_TRANSFORMATION | causal emission order, `model_time` | Per-shape emission ordinal; protocol state not yet fixed | YES | None | N/A | Deterministic counter, never wall-clock arrival order |
| `timestamp` | DIRECT | `model_time` | `timestamp = model_time` | YES | None | N/A | Transfer unchanged |
| `direction` | GENUINE_D02_MATHEMATICAL_GAP | `state_level`, `forward_interval`, FMO levels | Horizon/sample and scale-aware NEUTRAL boundary absent | YES | Sign projection | UNSUPPORTED | Clarify geometry projection; no trading semantics |
| `shape_quality` | GENUINE_D02_MATHEMATICAL_GAP | `coherence`, `strength`, `uncertainty`, FMO | Meaning and aggregation absent | YES | Scalar aggregation | MIXED | Define quality independently of D04 placeholder weights |
| `forward_support` | GENUINE_D02_MATHEMATICAL_GAP | `state_support_ratio`, state/FMO support coordinates | Unbounded-to-bounded and path aggregation absent | YES | Normalization/path compression | MIXED | Clarify current vs forward support and normalization |
| `uncertainty` | DIRECT | `uncertainty` | Direct current score | YES | Forward path omitted | INCONCLUSIVE | Transfer without validation claim |
| `expected_lifetime_seconds` | GENUINE_D02_MATHEMATICAL_GAP | `forward_half_life`, `forward_interval`, FMO | Interval vs half-life vs threshold-crossing meaning absent | YES | Temporal selection | INCONCLUSIVE | Clarify validity duration |
| `candidate_rr` | OBSOLETE_OR_DUPLICATIVE | None | Trade reward/risk is absent and field is unused by D04 core | NO authorized source | N/A | N/A | Remove/relocate in separately authorized D04 revision |
| `magnitude_score` | GENUINE_D02_MATHEMATICAL_GAP | `state_level`, FMO levels, interval, strength | Path statistic and causal scale normalization absent | YES | Geometry-to-score | MIXED | Do not substitute perturbation magnitude |
| `persistence_score` | DIRECT | `persistence` | Direct bounded score | YES | Forward path omitted | UNSUPPORTED | Transfer with unsupported label preserved |
| `decay_score` | GENUINE_D02_MATHEMATICAL_GAP | `forward_half_life`, interval, FMO paths | Coordinate, reference horizon, scalar summary absent | YES | Path-to-scalar | MIXED | Reuse D01 decay path only after scalar meaning is fixed |
| `reversal_risk` | GENUINE_D02_MATHEMATICAL_GAP | `reversal_propensity`, FMO, perturbation class | Propensity-to-risk semantics/path aggregation absent | YES | Semantic conversion | INCONCLUSIVE | Do not call a probability without authority |
| `active` | GENUINE_D02_MATHEMATICAL_GAP | `model_time`, interval, half-life | Context-only reevaluation and expiration rule absent | YES | Validity state | INCONCLUSIVE | Define causal expiry lifecycle |
| `metadata` | CONSTANT_OR_CONFIGURATION | None | Empty mapping | YES | None | N/A | Keep empty; prohibit hidden inputs |

## 4. Geometry available from FMO

The following geometry is causally available but is not yet a complete D04 mapping:

- temporal coordinates `tau_j` in `(0, forward_interval]`;
- projected level path `level_j`;
- projected velocity path `velocity_j`;
- projected uncertainty, strength, persistence, and reversal-propensity paths;
- current `state_level` for displacement reference;
- a terminal sample at the configured forward interval under the accepted sampler.

D01 already computes:

$$
\hat L_t(\tau)=L_t+V_t\tau+\frac{1}{2}A_t\tau^2
$$

and decay:

$$
d_t(\tau)=2^{-\tau/H_{f,t}}.
$$

This supports deterministic calculation of signed displacement, segment slopes, path extent, and coordinate-wise decay. It does not define which statistic, horizon, normalization, or scalar semantics D04 requires. Stage 2 observer path length, efficiency, realized displacement, and other realized coordinates are prohibited inputs; their names do not authorize equivalent D02 formulas.

## 5. Stage 2 evidence lineage

- `strength`: SUPPORTED, but not validated as a directional or profitable signal.
- `perturbation_magnitude`: SUPPORTED for subsequent transition magnitude; it is not expected-return magnitude.
- `coherence`: PARTIALLY_SUPPORTED.
- `uncertainty`, `reversal_propensity`, `perturbation_class`, both half-lives, and `forward_interval`: INCONCLUSIVE.
- State/kinematics and `persistence`: UNSUPPORTED under frozen Stage 2 semantics.
- `state_support_ratio` and the FMO list as a structured whole: not independently tested.

Every composite shape field therefore has `MIXED`, `INCONCLUSIVE`, or `UNSUPPORTED` lineage unless it is identity/protocol metadata. No weighting, deletion, zeroing, or confidence adjustment is authorized by these labels.

## 6. Coverage and outcome

The current D04 model has 14 mandatory fields. Only 5 mandatory fields can presently be supplied by D02 without unresolved science or misplaced responsibility: `return_shape_id`, `version`, `timestamp`, `uncertainty`, and `persistence_score`. This is **5/14 mandatory coverage**.

The interface is not implementation-ready and not freeze-ready.

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np

from aptf_d01.conditioning import ConditionedFeature, FeatureScalingRegistry, ScalingPolicy
from aptf_d01.model.feature_contract import (
    BASE_FEATURE_SPECS,
    build_active_channel_map,
    derive_admissible_base_features,
)
from aptf_d01.model.relationship_model import directional_coherence
from aptf_d01.model.state_estimator import bounded_tanh
from aptf_d01.model.transition_model import reversal_tendency
from aptf_d01.model.frozen_basis_contract import (
    FROZEN_BASIS_MUTATION_ATTEMPT,
    canonical_basis_hash,
    evaluate_frozen_basis,
    validate_basis_contract,
)
from aptf_d01.models.current_state import CurrentState
from aptf_d01.models.dynamic_model_output import DynamicModelOutput
from aptf_d01.models.forward_model_output import ForwardModelOutput
from aptf_d01.models.normalized_observation import NormalizedObservation
from aptf_d01.models.parameter_state import ParameterState
from aptf_d01.models.volume_state import VolumeState
from aptf_d01.parametric.basis import polynomial_basis
from aptf_d01.parametric.interactions import add_allowed_interactions
from aptf_d01.parametric.multi_output_model import MultiOutputConfig, MultiOutputModel
from aptf_d01.providers.observation_capabilities import ObservationCapabilities, from_mapping
from aptf_d01.signals.mass import effective_mass_m0, effective_mass_m1
from aptf_d01.signals.perturbation_detector import PerturbationDetector, PerturbationThresholds
from aptf_d01.signals.reinforcement import reinforcement_score
from aptf_d01.signals.signal_estimator import AdaptiveSignalEstimator
from aptf_d01.temporal.adaptive_half_life import AdaptiveHalfLife
from aptf_d01.temporal.half_life import HalfLifeState
from aptf_d01.temporal.temporal_relevance import TemporalRelevanceModel
from aptf_d01.volume.relative_volume import RelativeVolumeEstimator
from aptf_d01.volume.volume_density import volume_density
from aptf_d01.volume.volume_direction import directional_volume
from aptf_d01.volume.volume_movement import volume_movement_abs, volume_movement_signed


REQUIRED_OUTPUTS = [
    "direction_state",
    "magnitude_state",
    "strength",
    "persistence",
    "observation_half_life",
    "forward_half_life",
    "reinforcement",
    "uncertainty",
    "reversal_tendency",
    "perturbation_state",
]


@dataclass
class ModelConfig:
    entity_id: str
    model_instance_id: str
    model_definition_version: str
    polynomial_order: int
    include_volume: bool
    include_volume_interactions: bool
    adaptive_half_life: bool
    perturbation_responsive_half_life: bool
    learning_rate: float
    l2_regularization: float
    weight_clip: float
    observation_interval_seconds: float
    forward_interval_seconds: float
    half_life_min: float
    half_life_default: float
    half_life_max: float
    perturbation_shorten_factor: float
    reinforcement_lengthen_factor: float
    volume_baseline_method: str
    volume_baseline_window: int
    volume_half_life_seconds: float
    interaction_allowlist: list[str]
    interaction_max_order: int
    use_conditioning: bool
    thresholds: PerturbationThresholds
    scaling_min_warmup_observations: int
    scaling_epsilon: float
    scaling_lower_bound: float
    scaling_upper_bound: float
    output_overrides: dict[str, dict[str, float]]
    observation_capabilities: dict[str, object] | None = None
    frozen_basis_feature_names: list[str] | None = None
    frozen_basis_sha256: str | None = None
    frozen_basis_experiment_id: str | None = None


class AdaptiveParametricModel:
    def __init__(self, cfg: ModelConfig) -> None:
        self.cfg = cfg
        self.frozen_basis_enabled = bool(cfg.frozen_basis_feature_names)
        self.frozen_basis_experiment_id = str(cfg.frozen_basis_experiment_id or cfg.entity_id)
        self.frozen_basis_feature_names = list(cfg.frozen_basis_feature_names or [])
        self.frozen_basis_sha256 = str(cfg.frozen_basis_sha256 or "")
        self.parameter_state_version = 1
        self.previous_observation: NormalizedObservation | None = None
        self.previous_direction = 0.0
        self.previous_velocity = 0.0
        self.previous_timestamp: float | None = None
        self.sequence = 0
        self.last_half_life = cfg.half_life_default
        self.latest_conditioning_records: list[ConditionedFeature] = []
        self.conditioning_bound_hit_count = 0
        self.parameter_bound_hit_count = 0
        self.learning_active = False

        self.obs_half_life = AdaptiveHalfLife(
            HalfLifeState.from_bounds(cfg.half_life_min, cfg.half_life_default, cfg.half_life_max),
            perturbation_shorten_factor=cfg.perturbation_shorten_factor,
            reinforcement_lengthen_factor=cfg.reinforcement_lengthen_factor,
        )
        self.fwd_half_life = AdaptiveHalfLife(
            HalfLifeState.from_bounds(cfg.half_life_min, cfg.half_life_default, cfg.half_life_max),
            perturbation_shorten_factor=cfg.perturbation_shorten_factor,
            reinforcement_lengthen_factor=cfg.reinforcement_lengthen_factor,
        )

        self.rv = RelativeVolumeEstimator(
            method=cfg.volume_baseline_method,
            window=cfg.volume_baseline_window,
            half_life_seconds=cfg.volume_half_life_seconds,
        )
        self.detector = PerturbationDetector(cfg.thresholds)
        self.signal_estimator = AdaptiveSignalEstimator()
        self.volume_queue: deque[tuple[float, float]] = deque(maxlen=200)

        caps = from_mapping(cfg.observation_capabilities) if cfg.observation_capabilities else None
        if caps is None:
            caps = ObservationCapabilities(provider="UNKNOWN", entity=cfg.entity_id)
        self.observation_capabilities = caps
        self.active_channel_map = build_active_channel_map(caps)

        self.candidate_base_feature_names = [spec.name for spec in BASE_FEATURE_SPECS]
        self.base_feature_names, self.feature_admissibility = derive_admissible_base_features(
            capabilities=caps,
            include_volume=cfg.include_volume,
        )
        self.inactive_base_feature_reasons = {
            d.feature_name: d.reason for d in self.feature_admissibility if not d.active
        }

        self.feature_units = {
            "price_displacement": "fraction",
            "price_velocity": "fraction_per_second",
            "price_acceleration": "fraction_per_second2",
            "spread": "dollars",
            "spread_change": "dollars",
            "relative_volume": "ratio",
            "volume_log": "log_ratio",
            "volume_density": "shares_per_second",
            "directional_volume": "signed_log_ratio",
            "volume_movement_abs": "interaction_unit",
            "volume_movement_signed": "interaction_unit",
        }

        self.scaling_registry = FeatureScalingRegistry(
            policies={
                k: ScalingPolicy(method="RUNNING_ZSCORE", units=self.feature_units[k])
                for k in self.base_feature_names
            },
            minimum_warmup_observations=cfg.scaling_min_warmup_observations,
            epsilon=cfg.scaling_epsilon,
            lower_bound=cfg.scaling_lower_bound,
            upper_bound=cfg.scaling_upper_bound,
        )

        if self.frozen_basis_enabled:
            self.feature_names = list(self.frozen_basis_feature_names)
            if not self.frozen_basis_sha256:
                self.frozen_basis_sha256 = canonical_basis_hash(self.feature_names)
            self.active_interaction_features = sorted(k for k in self.feature_names if "_x_" in k)
            self._assert_frozen_basis(stage="init")
        else:
            seed_features = {k: 0.0 for k in self.base_feature_names}
            seed_features = add_allowed_interactions(seed_features, cfg.interaction_allowlist)
            self.active_interaction_features = sorted(k for k in seed_features if "_x_" in k)
            basis = polynomial_basis(seed_features, cfg.polynomial_order, interaction_max_order=cfg.interaction_max_order)
            self.feature_names = list(basis.keys())
        self.intercept_name = "bias"
        self.intercept_collision_count = 0
        self.feature_lineage = self._build_feature_lineage()

        self.mimo = MultiOutputModel(
            outputs=REQUIRED_OUTPUTS,
            feature_names=self.feature_names,
            config=MultiOutputConfig(
                learning_rate=cfg.learning_rate,
                l2_regularization=cfg.l2_regularization,
                weight_clip=cfg.weight_clip,
                output_overrides=cfg.output_overrides,
            ),
        )

    def _assert_frozen_basis(self, stage: str) -> dict[str, bool]:
        if not self.frozen_basis_enabled:
            return {"count_match": True, "ordered_names_match": True, "hash_match": True}
        return validate_basis_contract(
            experiment_id=self.frozen_basis_experiment_id,
            approved_feature_names=self.frozen_basis_feature_names,
            approved_basis_sha256=self.frozen_basis_sha256,
            runtime_feature_names=list(self.feature_names),
            error_code=FROZEN_BASIS_MUTATION_ATTEMPT,
            stage=stage,
        )

    def _build_feature_lineage(self) -> list[dict[str, object]]:
        spec_by_name = {spec.name: spec for spec in BASE_FEATURE_SPECS}
        rows: list[dict[str, object]] = []
        for dec in self.feature_admissibility:
            rows.append(
                {
                    "feature_name": dec.feature_name,
                    "feature_type": "base",
                    "source_observations": list(dec.requires),
                    "availability_requirements": list(dec.requires),
                    "base_feature": dec.feature_name,
                    "polynomial_order": 1,
                    "interaction_parents": [],
                    "admissibility_reason": dec.reason,
                    "active": dec.active,
                }
            )

        for name in self.feature_names:
            if name == self.intercept_name:
                rows.append(
                    {
                        "feature_name": name,
                        "feature_type": "intercept",
                        "source_observations": [],
                        "availability_requirements": [],
                        "base_feature": "",
                        "polynomial_order": 0,
                        "interaction_parents": [],
                        "admissibility_reason": "ACTIVE_INTERCEPT",
                        "active": True,
                    }
                )
                continue

            base_name = name
            poly_order = 1
            if "^" in name:
                base_name, p = name.split("^", 1)
                poly_order = int(p)

            parents = base_name.split("_x_") if "_x_" in base_name else []
            source_observations: list[str] = []
            if base_name in spec_by_name:
                source_observations = list(spec_by_name[base_name].requires)
            elif parents:
                req: set[str] = set()
                for p in parents:
                    if p in spec_by_name:
                        req.update(spec_by_name[p].requires)
                source_observations = sorted(req)

            rows.append(
                {
                    "feature_name": name,
                    "feature_type": "derived",
                    "source_observations": source_observations,
                    "availability_requirements": source_observations,
                    "base_feature": base_name,
                    "polynomial_order": poly_order,
                    "interaction_parents": parents,
                    "admissibility_reason": "ACTIVE_DERIVED_FROM_ADMISSIBLE_BASE",
                    "active": True,
                }
            )
        return rows

    def get_feature_manifest(self) -> dict[str, object]:
        runtime_basis_sha256 = canonical_basis_hash(self.feature_names)
        return {
            "provider_capabilities": self.observation_capabilities.to_dict(),
            "active_channel_map": self.active_channel_map.to_dict(),
            "candidate_base_features": list(self.candidate_base_feature_names),
            "active_base_features": list(self.base_feature_names),
            "inactive_base_features": [d.feature_name for d in self.feature_admissibility if not d.active],
            "inactive_reasons": dict(self.inactive_base_feature_reasons),
            "polynomial_order": self.cfg.polynomial_order,
            "interaction_max_order": self.cfg.interaction_max_order,
            "interaction_allowlist": list(self.cfg.interaction_allowlist),
            "interaction_features": list(self.active_interaction_features),
            "intercept": {
                "present": self.intercept_name in self.feature_names,
                "name": self.intercept_name,
                "collision_count": self.intercept_collision_count,
            },
            "final_feature_count": len(self.feature_names),
            "feature_names": list(self.feature_names),
            "feature_basis_sha256": runtime_basis_sha256,
            "frozen_basis_enabled": self.frozen_basis_enabled,
            "frozen_basis_experiment_id": self.frozen_basis_experiment_id,
            "frozen_basis_expected_sha256": self.frozen_basis_sha256 if self.frozen_basis_enabled else "",
            "feature_lineage": list(self.feature_lineage),
        }

    def reset_observation_continuity_state(self) -> None:
        self.previous_observation = None
        self.previous_velocity = 0.0
        self.previous_direction = 0.0
        self.previous_timestamp = None
        self.volume_queue.clear()
        self.rv = RelativeVolumeEstimator(
            method=self.cfg.volume_baseline_method,
            window=self.cfg.volume_baseline_window,
            half_life_seconds=self.cfg.volume_half_life_seconds,
        )

    def reset_scaling_state(self) -> None:
        self.scaling_registry.reset()
        self.conditioning_bound_hit_count = 0

    def reset_all_state(self) -> None:
        self.reset_observation_continuity_state()
        self.reset_scaling_state()

    def _build_features(self, obs: NormalizedObservation, model_time: float) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
        prev = self.previous_observation
        bid_now = obs.bid if obs.bid is not None else float("nan")
        ask_now = obs.ask if obs.ask is not None else float("nan")
        bid_prev = prev.bid if (prev is not None and prev.bid is not None) else float("nan")
        ask_prev = prev.ask if (prev is not None and prev.ask is not None) else float("nan")
        if prev is None:
            dt = 1.0
            delta_price = 0.0
            velocity = 0.0
            acceleration = 0.0
            spread_change = 0.0
        else:
            dt = obs.exchange_timestamp - prev.exchange_timestamp
            if dt <= 0.0:
                raise ValueError("INVALID_TEMPORAL_ORDER")
            delta_price = (obs.price - prev.price) / max(prev.price, 1e-9)
            velocity = delta_price / dt
            acceleration = (velocity - self.previous_velocity) / dt
            if math.isfinite(bid_now) and math.isfinite(ask_now) and math.isfinite(bid_prev) and math.isfinite(ask_prev):
                spread_change = (ask_now - bid_now) - (ask_prev - bid_prev)
            else:
                spread_change = float("nan")

        rv, vlog = self.rv.update(obs.exchange_timestamp, obs.volume)
        self.volume_queue.append((obs.exchange_timestamp, obs.volume))
        min_ts = self.volume_queue[0][0]
        max_ts = self.volume_queue[-1][0]
        total_vol = sum(v for _, v in self.volume_queue)
        v_density = volume_density(total_vol, max(1e-6, max_ts - min_ts))
        dvol = directional_volume(delta_price, vlog)
        vm_abs = volume_movement_abs(vlog, delta_price)
        vm_signed = volume_movement_signed(vlog, delta_price)

        raw_candidate_features = {
            "price_displacement": delta_price,
            "price_velocity": velocity,
            "price_acceleration": acceleration,
            "spread": (ask_now - bid_now) if math.isfinite(ask_now) and math.isfinite(bid_now) else float("nan"),
            "spread_change": spread_change,
            "relative_volume": rv if self.cfg.include_volume else 0.0,
            "volume_log": vlog if self.cfg.include_volume else 0.0,
            "volume_density": v_density if self.cfg.include_volume else 0.0,
            "directional_volume": dvol if self.cfg.include_volume else 0.0,
            "volume_movement_abs": vm_abs if self.cfg.include_volume else 0.0,
            "volume_movement_signed": vm_signed if self.cfg.include_volume else 0.0,
        }
        raw_features = {k: float(raw_candidate_features[k]) for k in self.base_feature_names}

        conditioned: dict[str, float] = {}
        self.latest_conditioning_records = []
        if self.cfg.use_conditioning:
            for k in self.base_feature_names:
                c = self.scaling_registry.transform(k, float(raw_features[k]), model_time=model_time)
                conditioned[k] = c.model_value
                self.latest_conditioning_records.append(c)
                if c.bound_hit:
                    self.conditioning_bound_hit_count += 1
        else:
            for k in self.base_feature_names:
                conditioned[k] = float(raw_features[k])

        if self.cfg.include_volume_interactions and (not self.frozen_basis_enabled):
            conditioned = add_allowed_interactions(conditioned, self.cfg.interaction_allowlist)

        derived = {
            "dt": dt,
            "delta_price": delta_price,
            "velocity": velocity,
            "acceleration": acceleration,
            "spread_change": spread_change,
            "rv": rv,
            "vlog": vlog,
            "v_density": v_density,
            "dvol": dvol,
            "vm_abs": vm_abs,
            "vm_signed": vm_signed,
        }
        return conditioned, derived, raw_features

    def _targets(self, features: dict[str, float], perturb_mag: float, reinforcement: float, current_h: float, forward_h: float) -> dict[str, float]:
        direction = bounded_tanh(features.get("price_velocity", 0.0), scale=0.005)
        magnitude = abs(features.get("price_displacement", 0.0))
        strength = min(1.0, 0.6 * abs(direction) + 0.4 * min(1.0, features.get("volume_log", 0.0)))
        persistence = min(1.0, current_h / max(self.cfg.half_life_max, 1e-9))
        uncertainty = max(0.0, min(1.0, 1.0 - strength + 0.25 * perturb_mag))
        reversal = max(0.0, min(1.0, 0.5 * perturb_mag + 0.3 * max(-direction * self.previous_direction, 0.0)))

        return {
            "direction_state": direction,
            "magnitude_state": magnitude,
            "strength": strength,
            "persistence": persistence,
            "observation_half_life": current_h,
            "forward_half_life": forward_h,
            "reinforcement": reinforcement,
            "uncertainty": uncertainty,
            "reversal_tendency": reversal,
            "perturbation_state": perturb_mag,
        }

    def step(self, obs: NormalizedObservation, model_time: float) -> tuple[DynamicModelOutput, ForwardModelOutput, dict[str, dict[str, float]]]:
        features, d, raw_features = self._build_features(obs, model_time=model_time)

        perturb = self.detector.detect(
            entity_id=obs.entity_id,
            timestamp=model_time,
            displacement=d["delta_price"],
            velocity=d["velocity"],
            acceleration=d["acceleration"],
            relative_volume=d["rv"],
            volume_density=d["v_density"],
            spread_change=d["spread_change"],
        )

        reinforcement = reinforcement_score(self.previous_direction, np.sign(d["delta_price"]), perturb.magnitude)
        h_obs = self.obs_half_life.update(
            perturbation_magnitude=perturb.magnitude,
            reinforcement=reinforcement,
            enabled=self.cfg.adaptive_half_life,
            perturbation_responsive=self.cfg.perturbation_responsive_half_life,
        )
        h_fwd = self.fwd_half_life.update(
            perturbation_magnitude=0.5 * perturb.magnitude,
            reinforcement=max(0.0, reinforcement),
            enabled=self.cfg.adaptive_half_life,
            perturbation_responsive=self.cfg.perturbation_responsive_half_life,
        )
        tr = TemporalRelevanceModel(observation_half_life_seconds=h_obs, forward_half_life_seconds=h_fwd)

        coh = directional_coherence(d["delta_price"], d["dvol"])
        em0 = effective_mass_m0(d["vlog"])
        em1 = effective_mass_m1(d["rv"], d["v_density"], coh)
        effective_mass = 0.5 * em0 + 0.5 * em1

        uncertainty_seed = max(0.0, min(1.0, 0.6 - 0.25 * abs(coh) + 0.3 * perturb.magnitude))
        adaptive_signal = self.signal_estimator.build(
            entity_id=obs.entity_id,
            timestamp=model_time,
            half_life_seconds=h_obs,
            reinforcement=reinforcement,
            uncertainty=uncertainty_seed,
            effective_mass=effective_mass,
            movement_abs=abs(d["delta_price"]),
            directional_coherence=coh,
        )

        # Ensure full feature vector contains exactly known keys.
        padded = {k: float(features.get(k, 0.0)) for k in self.base_feature_names}
        if self.frozen_basis_enabled:
            basis = evaluate_frozen_basis(self.feature_names, padded)
            self._assert_frozen_basis(stage="step")
        else:
            if self.cfg.include_volume_interactions:
                padded = add_allowed_interactions(padded, self.cfg.interaction_allowlist)
            basis = polynomial_basis(padded, self.cfg.polynomial_order, interaction_max_order=self.cfg.interaction_max_order)
        x = np.array([basis.get(name, 0.0) for name in self.feature_names], dtype=float)

        targets = self._targets(padded, perturb.magnitude, reinforcement, h_obs, h_fwd)
        preds = self.mimo.predict(x)
        self.learning_active = True if not self.cfg.use_conditioning else (not self.scaling_registry.warmup_state())
        if self.learning_active:
            detail = self.mimo.update_detailed(x, targets)
            update_log = {
                out: {
                    "old_l1": d["old_l1"],
                    "new_l1": d["new_l1"],
                    "delta_l1": d["delta_l1"],
                    "error": d["error"],
                    "drift": d["drift"],
                    "grad_abs_max": d["grad_abs_max"],
                    "learning_rate": d["learning_rate"],
                    "l2_regularization": d["l2_regularization"],
                    "parameter_bound_hit": d["parameter_bound_hit"],
                    "weights_pre": d["weights_pre"],
                    "weights_post": d["weights_post"],
                    "gradient": d["gradient"],
                }
                for out, d in detail.items()
            }
            self.parameter_bound_hit_count += sum(1 for out in detail.values() if out["parameter_bound_hit"])
        else:
            update_log = {
                out: {
                    "old_l1": float(np.abs(self.mimo._weights[out]).sum()),
                    "new_l1": float(np.abs(self.mimo._weights[out]).sum()),
                    "delta_l1": 0.0,
                    "error": float(targets.get(out, 0.0) - preds.get(out, 0.0)),
                    "drift": 0.0,
                    "grad_abs_max": 0.0,
                    "learning_rate": self.cfg.learning_rate,
                    "l2_regularization": self.cfg.l2_regularization,
                    "parameter_bound_hit": False,
                    "weights_pre": self.mimo._weights[out].copy(),
                    "weights_post": self.mimo._weights[out].copy(),
                    "gradient": np.zeros_like(self.mimo._weights[out]),
                }
                for out in self.mimo.outputs
            }

        output = {k: 0.5 * preds[k] + 0.5 * targets[k] for k in REQUIRED_OUTPUTS}
        output["strength"] = max(0.0, min(1.0, output["strength"]))
        output["uncertainty"] = max(0.0, min(1.0, output["uncertainty"]))
        output["magnitude_state"] = abs(output["magnitude_state"])
        output["direction_state"] = max(-1.0, min(1.0, output["direction_state"]))

        # Volume != strength guardrail.
        if d["rv"] > 2.0 and abs(d["delta_price"]) < 0.0005:
            output["strength"] = min(output["strength"], 0.65)

        rev = reversal_tendency(output["direction_state"], self.previous_direction, perturb.magnitude)
        output["reversal_tendency"] = rev

        obs_interval_start = max(0.0, model_time - self.cfg.observation_interval_seconds)
        fwd_interval_end = model_time + self.cfg.forward_interval_seconds

        volume_state = VolumeState(
            raw_volume=obs.volume,
            relative_volume=d["rv"],
            volume_log=d["vlog"],
            volume_density=d["v_density"],
            directional_volume=d["dvol"],
            volume_movement_interaction_abs=d["vm_abs"],
            volume_movement_interaction_signed=d["vm_signed"],
            volume_half_life_seconds=self.cfg.volume_half_life_seconds,
        )

        current_state = CurrentState(
            direction_state=output["direction_state"],
            magnitude_state=output["magnitude_state"],
            strength=output["strength"],
            persistence=output["persistence"],
            reinforcement=output["reinforcement"],
            uncertainty=output["uncertainty"],
            reversal_tendency=output["reversal_tendency"],
            perturbation_state=output["perturbation_state"],
        )

        dmo = DynamicModelOutput(
            entity_id=obs.entity_id,
            model_instance_id=self.cfg.model_instance_id,
            model_time=model_time,
            model_definition_version=self.cfg.model_definition_version,
            parameter_state_version=self.parameter_state_version,
            observation_interval_start=obs_interval_start,
            observation_interval_end=model_time,
            input_channel_snapshot={
                **{f"model_{k}": v for k, v in padded.items()},
                **{f"raw_{k}": float(raw_features[k]) for k in self.base_feature_names},
                **{f"basis_{k}": float(basis.get(k, 0.0)) for k in self.feature_names},
                "effective_mass": effective_mass,
                "temporal_weight_now": tr.observation_weight(0.0),
            },
            adaptive_signal_snapshot={
                "strength": adaptive_signal.strength,
                "half_life_seconds": adaptive_signal.half_life_seconds,
                "reinforcement": adaptive_signal.reinforcement,
                "uncertainty": adaptive_signal.uncertainty,
                "effective_mass": adaptive_signal.effective_mass,
                "density": adaptive_signal.density,
            },
            current_state=current_state,
            direction_state=current_state.direction_state,
            magnitude_state=current_state.magnitude_state,
            strength=current_state.strength,
            persistence=current_state.persistence,
            reinforcement=current_state.reinforcement,
            uncertainty=current_state.uncertainty,
            observation_half_life=output["observation_half_life"],
            forward_half_life=output["forward_half_life"],
            reversal_tendency=current_state.reversal_tendency,
            perturbation_state=current_state.perturbation_state,
            volume_state=volume_state,
            parameter_summary=self.mimo.summarize(),
            model_health={
                "data_valid": obs.data_valid,
                "point_in_time": obs.model_available_timestamp <= model_time,
                "perturbation_type": perturb.type.value,
                "perturbation_reasons": perturb.reason_codes,
                "conditioning_warmup": not self.learning_active,
                "conditioning_bound_hits": self.conditioning_bound_hit_count,
                "scaling_statistics_version": max((c.statistics_version for c in self.latest_conditioning_records), default=0),
                "active_feature_count": len(self.feature_names),
                "active_base_feature_count": len(self.base_feature_names),
            },
        )

        expected_decay = tr.forward_decay(self.cfg.forward_interval_seconds)
        direction_support = output["direction_state"]
        expected_magnitude = max(0.0, output["magnitude_state"] * (1.0 + 0.5 * output["strength"]))
        expected_persistence = output["persistence"]
        uncertainty = output["uncertainty"]

        favorable = expected_magnitude * max(0.0, direction_support) * (1.0 - uncertainty)
        adverse = expected_magnitude * max(0.0, -direction_support) * (0.6 + uncertainty)
        if direction_support >= 0:
            favorable = max(favorable, expected_magnitude * (1.0 - uncertainty) * 0.5)
            adverse = max(adverse, expected_magnitude * uncertainty * 0.4)

        fmo = ForwardModelOutput(
            entity_id=obs.entity_id,
            model_time=model_time,
            forward_interval_start=model_time,
            forward_interval_end=fwd_interval_end,
            directional_support=direction_support,
            expected_magnitude=expected_magnitude,
            expected_persistence=expected_persistence,
            forward_half_life=output["forward_half_life"],
            expected_decay=expected_decay,
            reversal_tendency=output["reversal_tendency"],
            uncertainty=uncertainty,
            favorable_excursion_estimate=favorable,
            adverse_excursion_estimate=adverse,
            confidence=max(0.0, min(1.0, 1.0 - uncertainty)),
            metadata={"dmotype": "forward_subset"},
        )

        self.sequence += 1
        self.parameter_state_version += 1
        self.previous_direction = output["direction_state"]
        self.previous_velocity = d["velocity"]
        self.previous_observation = obs
        self.previous_timestamp = obs.exchange_timestamp

        return dmo, fmo, update_log

    def parameter_state(self, model_time: float) -> ParameterState:
        return ParameterState(
            model_definition_version=self.cfg.model_definition_version,
            parameter_state_version=self.parameter_state_version,
            updated_at=model_time,
            parameters={k: [float(v)] for k, v in self.mimo.summarize().items()},
        )

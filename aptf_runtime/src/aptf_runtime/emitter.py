from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, replace
from statistics import median
from typing import Any

from aptf_d04.envelope.capturability_model import CapturabilityModelV0_2
from aptf_d04.models.envelope_context import EnvelopeContext
from d01.v02.model import D01V02Model
from d02.v02.builder import build_return_shape

from .context import CONTEXT_LENGTH, RollingContext
from .models import EmitterDecision, EmitterState, ImmutableEmission
from .observation import Observation


DIRECTION_SIGN = {"UPWARD": 1, "DOWNWARD": -1, "FLAT": 0}


def _historical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class AdaptiveEmitter:
    def __init__(self, entity_id: str, rule_fingerprint: str, code_fingerprint: str) -> None:
        if not entity_id or not rule_fingerprint or not code_fingerprint:
            raise ValueError("entity_id and frozen fingerprints are required")
        self.entity_id = entity_id
        self.rule_fingerprint = rule_fingerprint
        self.code_fingerprint = code_fingerprint
        self.d01 = D01V02Model(entity_id=entity_id)
        self.capturability = CapturabilityModelV0_2()
        self.context = RollingContext()
        self.state = EmitterState()
        self._last_source_time: float | None = None
        self.initialization: list[ImmutableEmission] = []
        self.emissions: list[ImmutableEmission] = []
        self.adaptation_audit: list[dict[str, Any]] = []
        self.feedback_audit: list[dict[str, Any]] = []

    @staticmethod
    def _adaptive_properties(
        context: tuple[dict[str, Any], ...], current_c: float
    ) -> dict[str, Any]:
        c_values = [item["C"] for item in context]
        signs = [DIRECTION_SIGN[item["path_direction"]] for item in context]
        return {
            "prior_15_median_C": median(c_values),
            "prior_15_min_C": min(c_values),
            "prior_15_max_C": max(c_values),
            "prior_15_range_C": max(c_values) - min(c_values),
            "prior_C": c_values[-1],
            "delta_C": current_c - c_values[-1],
            "up_count": sum(sign > 0 for sign in signs),
            "down_count": sum(sign < 0 for sign in signs),
            "flat_count": sum(sign == 0 for sign in signs),
            "direction_balance": sum(signs),
        }

    @staticmethod
    def _decide(
        path_direction: str,
        hard_eligibility: int,
        capturability: float,
        adaptive: dict[str, Any],
    ) -> tuple[EmitterDecision, str]:
        quality_eligible = (
            hard_eligibility == 1
            and capturability >= adaptive["prior_15_median_C"]
        )
        if (
            path_direction == "UPWARD"
            and quality_eligible
            and adaptive["up_count"] >= adaptive["down_count"]
        ):
            return (
                EmitterDecision.BUY,
                "UPWARD_AND_PRIOR_DIRECTION_AGREEMENT_AND_C_GE_PRIOR_MEDIAN",
            )
        if (
            path_direction == "DOWNWARD"
            and quality_eligible
            and adaptive["down_count"] >= adaptive["up_count"]
        ):
            return (
                EmitterDecision.SELL,
                "DOWNWARD_AND_PRIOR_DIRECTION_AGREEMENT_AND_C_GE_PRIOR_MEDIAN",
            )
        return (
            EmitterDecision.HOLD,
            "AFFIRM_POSITION_STATE_TRANSITION_PREDICATE_NOT_SATISFIED",
        )

    def process(self, observation: Observation) -> ImmutableEmission:
        if observation.entity_id != self.entity_id:
            raise ValueError("observation entity does not match emitter instance")
        lifecycle_start = time.perf_counter_ns()
        stage: dict[str, int] = {}
        delta_t = (
            None
            if self._last_source_time is None
            else observation.event_time - self._last_source_time
        )
        if delta_t is not None and delta_t <= 0:
            raise ValueError("source time must increase")

        state_before = {
            "completed_count": self.state.completed_count,
            "position_state": self.state.legacy_internal_controller_state,
            "previous_decision": (
                None
                if self.state.previous_decision is None
                else self.state.previous_decision.value
            ),
            "d01_state_hash": _historical_sha256(asdict(self.d01.state)),
            "context_ids": list(self.context.observation_ids),
        }
        started = time.perf_counter_ns()
        dmo, fmo = self.d01.step(observation.to_d01())
        stage["D01"] = time.perf_counter_ns() - started
        started = time.perf_counter_ns()
        shape = build_return_shape(dmo, fmo)
        stage["D02"] = time.perf_counter_ns() - started
        started = time.perf_counter_ns()
        capture = self.capturability.evaluate(
            shape,
            EnvelopeContext.production(evaluation_time=observation.event_time),
        )
        stage["FOUR_FACTOR"] = time.perf_counter_ns() - started
        vector = {
            "H": capture.hard_eligibility,
            "Q_G": capture.geometry_quality,
            "Q_S": capture.structural_quality,
            "Q_R": capture.risk_quality,
            "C": capture.capturability_score,
        }
        observation_id = _historical_sha256(
            {
                "physical_row": observation.physical_row,
                "source_row_number": observation.source_row_number,
                "timestamp": observation.event_timestamp_utc,
                "ohlcv": {
                    "open": observation.open,
                    "high": observation.high,
                    "low": observation.low,
                    "close": observation.close,
                    "volume": observation.volume,
                },
            }
        )
        completed_record = {
            "observation_index": self.state.completed_count + 1,
            "observation_id": observation_id,
            "physical_row": observation.physical_row,
            "source_timestamp": observation.event_timestamp_utc,
            "source": {
                "open": float(observation.open),
                "high": float(observation.high),
                "low": float(observation.low),
                "close": float(observation.close),
                "volume": float(observation.volume),
            },
            "delta_t_seconds": delta_t,
            "path_direction": shape.path_direction.value,
            "terminal_displacement": shape.terminal_displacement,
            "state_velocity": dmo.state_velocity,
            "state_acceleration": dmo.state_acceleration,
            "strength": shape.strength,
            "coherence": shape.coherence,
            "persistence": shape.persistence,
            "uncertainty": shape.uncertainty,
            "reversal_propensity": shape.reversal_propensity,
            **vector,
        }

        context_snapshot = self.context.snapshot()
        if self.state.completed_count < CONTEXT_LENGTH:
            status = "INITIALIZING"
            decision = None
            rule_path = "INITIALIZATION_NON_ACTIONABLE"
            adaptive: dict[str, Any] = {}
        else:
            if len(context_snapshot) != CONTEXT_LENGTH:
                raise RuntimeError("actionable context length is not 15")
            status = "ACTIONABLE"
            started = time.perf_counter_ns()
            adaptive = self._adaptive_properties(context_snapshot, vector["C"])
            decision, rule_path = self._decide(
                shape.path_direction.value,
                vector["H"],
                vector["C"],
                adaptive,
            )
            stage["ADAPTIVE_DECISION"] = time.perf_counter_ns() - started

        old_internal_state = self.state.legacy_internal_controller_state
        old_decision = self.state.previous_decision
        if decision is EmitterDecision.BUY:
            next_internal_state = "LONG"
        elif decision is EmitterDecision.SELL:
            next_internal_state = "SHORT"
        else:
            next_internal_state = old_internal_state

        lifecycle_end = time.perf_counter_ns()
        emission_core = {
            "observation_index": self.state.completed_count + 1,
            "observation_id": observation_id,
            "physical_row": observation.physical_row,
            "observation_timestamp": observation.event_timestamp_utc,
            "prior_context_ids": [item["observation_id"] for item in context_snapshot],
            "context_start_timestamp": (
                context_snapshot[0]["source_timestamp"] if context_snapshot else None
            ),
            "context_end_timestamp": (
                context_snapshot[-1]["source_timestamp"] if context_snapshot else None
            ),
            "source_delta_t_seconds": delta_t,
            "status": status,
            "state_before": state_before,
            "mathematics": {
                "dmo": dmo.to_dict(),
                "fmo": fmo.to_dict(),
                "return_shape": shape.to_dict(),
                **vector,
            },
            "adaptive_properties": adaptive,
            "position_state_before": old_internal_state,
            "position_decision": None if decision is None else decision.value,
            "decision_rule_path": rule_path,
            "feedback_generated": (
                [] if decision is None else ["prior_decision", "position_state"]
            ),
            "state_after": {
                "completed_count": self.state.completed_count + 1,
                "position_state": next_internal_state,
                "previous_decision": (
                    old_decision.value if decision is None and old_decision else None
                )
                if decision is None
                else decision.value,
            },
            "lifecycle_start_ns": lifecycle_start,
            "lifecycle_end_ns": lifecycle_end,
            "direct_lifecycle_ns": lifecycle_end - lifecycle_start,
            "component_lifecycle_ns": stage,
            "source_fingerprint": observation_id,
            "rule_fingerprint": self.rule_fingerprint,
            "code_fingerprint": self.code_fingerprint,
            "future_access_count": 0,
        }
        emission_id = _historical_sha256(emission_core)
        emission_payload = {"emission_id": emission_id, **emission_core}

        prior_adaptive = (
            self._adaptive_properties(context_snapshot, context_snapshot[-1]["C"])
            if len(context_snapshot) == CONTEXT_LENGTH
            else None
        )
        self.context.append_completed(completed_record)
        new_context = self.context.snapshot()
        if len(new_context) == CONTEXT_LENGTH:
            new_adaptive = self._adaptive_properties(new_context, new_context[-1]["C"])
            for name, new_value in new_adaptive.items():
                old_value = None if prior_adaptive is None else prior_adaptive[name]
                if old_value != new_value:
                    self.adaptation_audit.append(
                        {
                            "property": name,
                            "old_value": old_value,
                            "new_value": new_value,
                            "causal_observation_id": observation_id,
                            "rolling_context_ids": list(self.context.observation_ids),
                            "equation": "defined rolling-15 operator",
                            "timestamp": observation.event_timestamp_utc,
                            "effective_observation": self.state.completed_count + 2,
                        }
                    )
        if decision is not None:
            self.feedback_audit.extend(
                [
                    {
                        "source_emission_id": emission_id,
                        "feedback_property": "position_decision",
                        "target_state_property": "previous_decision",
                        "old_value": None if old_decision is None else old_decision.value,
                        "new_value": decision.value,
                        "equation": "previous_decision_(n+1)=decision_n",
                        "timestamp": observation.event_timestamp_utc,
                        "effective_observation": self.state.completed_count + 2,
                    },
                    {
                        "source_emission_id": emission_id,
                        "feedback_property": "position_transition",
                        "target_state_property": "position_state",
                        "old_value": old_internal_state,
                        "new_value": next_internal_state,
                        "equation": "BUY->LONG; SELL->SHORT; HOLD->preserve",
                        "timestamp": observation.event_timestamp_utc,
                        "effective_observation": self.state.completed_count + 2,
                    },
                ]
            )
        self.state = replace(
            self.state,
            completed_count=self.state.completed_count + 1,
            previous_decision=decision if decision is not None else old_decision,
            legacy_internal_controller_state=next_internal_state,
        )
        self._last_source_time = observation.event_time
        immutable = ImmutableEmission.from_dict(emission_payload)
        if decision is None:
            self.initialization.append(immutable)
        else:
            self.emissions.append(immutable)
        return immutable

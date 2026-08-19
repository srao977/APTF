from __future__ import annotations

import hashlib
import json
from enum import Enum
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aptf_d04.models.envelope_state import EnvelopeEvaluation


class InvalidD03InputError(ValueError):
    """Raised when the D03 causal input fails schema or semantic validation."""


class PositionState(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class PendingTargetState(str, Enum):
    NONE = "NONE"
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class TransitionIntent(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    REVERSE = "REVERSE"
    RETARGET = "RETARGET"
    BLOCKED = "BLOCKED"


class DecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    context_time: float
    entity_id: str
    actual_position_state: PositionState
    position_candidate_id: str | None
    position_source_return_shape_model_time: float | None
    pending_target_state: PendingTargetState
    pending_decision_id: str | None
    execution_available: bool
    system_enabled: bool
    trading_enabled: bool
    emergency_flatten: bool
    control_state_valid: bool

    @model_validator(mode="after")
    def validate_context(self) -> "DecisionContext":
        if not self.entity_id or not self.entity_id.strip():
            raise InvalidD03InputError("entity_id must be non-empty")
        if not (self.context_time == self.context_time and self.context_time != float("inf") and self.context_time != float("-inf")):
            raise InvalidD03InputError("context_time must be finite")
        if self.actual_position_state not in {"FLAT", "LONG", "SHORT"}:
            raise InvalidD03InputError("actual_position_state must be one of FLAT, LONG, SHORT")
        if self.pending_target_state not in {"NONE", "FLAT", "LONG", "SHORT"}:
            raise InvalidD03InputError("pending_target_state must be one of NONE, FLAT, LONG, SHORT")
        if self.actual_position_state == "FLAT":
            if self.position_candidate_id is not None:
                raise InvalidD03InputError("FLAT actual_position_state requires null position_candidate_id")
            if self.position_source_return_shape_model_time is not None:
                raise InvalidD03InputError("FLAT actual_position_state requires null position_source_return_shape_model_time")
        else:
            if not self.position_candidate_id:
                raise InvalidD03InputError("LONG/SHORT actual_position_state requires position_candidate_id")
            if self.position_source_return_shape_model_time is None or not (self.position_source_return_shape_model_time == self.position_source_return_shape_model_time and self.position_source_return_shape_model_time not in (float("inf"), float("-inf"))):
                raise InvalidD03InputError("LONG/SHORT actual_position_state requires finite position_source_return_shape_model_time")
        if (self.pending_target_state == "NONE") != (self.pending_decision_id is None):
            raise InvalidD03InputError("pending_target_state and pending_decision_id must be consistent")
        return self


class D03Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    d04_evaluation: EnvelopeEvaluation
    decision_context: DecisionContext

    @model_validator(mode="after")
    def validate_input(self) -> "D03Input":
        if self.d04_evaluation.entity_id != self.decision_context.entity_id:
            raise InvalidD03InputError("entity_id mismatch between D04 evaluation and DecisionContext")
        if self.decision_context.context_time < self.d04_evaluation.evaluation_time:
            raise InvalidD03InputError("context_time cannot precede D04 evaluation_time")
        return self


class DecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)

    decision_id: str
    decision_time: float
    entity_id: str
    d03_model_version: str
    decision_rule_version: str
    schema_version: str
    source_d04_fingerprint: str
    input_fingerprint: str
    source_d04_evaluation_time: float
    source_d04_return_shape_model_time: float
    source_d04_envelope_state: str
    source_d04_safety_state: str
    candidate_id: str | None
    candidate_source_return_shape_model_time: float | None
    prior_position_state: PositionState
    desired_position_state: PositionState
    transition_intent: TransitionIntent
    action_authorized: bool
    decision_rule_id: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...] = Field(default_factory=tuple)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=_default_json)


def _default_json(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "value") and not isinstance(value, (str, int, float, bool, type(None))):
        return value.value
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _sha256_hex(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _exact_float_string(value: float) -> str:
    return format(float(value), ".17g")


def _candidate_lineage_for(target_rule: str, evaluation: EnvelopeEvaluation) -> tuple[str | None, float | None]:
    candidate = evaluation.candidate_envelope
    if target_rule in {"R36", "R40", "R41"} and candidate is not None:
        return candidate.candidate_id, candidate.source_return_shape_model_time
    return None, None


def _resolve_target_rule(context: DecisionContext, evaluation: EnvelopeEvaluation) -> tuple[str, str, str | None, tuple[str | None, float | None], str | None]:
    if context.emergency_flatten:
        return "R10", "FLAT", "EMERGENCY_FLATTEN", (None, None), None
    if not context.system_enabled:
        return "R20", context.actual_position_state.value, "SYSTEM_DISABLED", (None, None), None
    if not context.trading_enabled:
        return "R21", context.actual_position_state.value, "TRADING_DISABLED", (None, None), None
    if evaluation.safety_state == "SAFETY_CLOSED" or evaluation.stale or not evaluation.projection_valid:
        support = evaluation.safety_reason.value if evaluation.safety_reason is not None else "SHAPE_STALE"
        return "R30", "FLAT", "D04_SAFETY_CLOSED", (None, None), support
    if evaluation.new_envelope_state == "CLOSED":
        return "R31", "FLAT", "ENVELOPE_CLOSED", (None, None), None
    if evaluation.new_envelope_state == "OPENING":
        return "R32", "FLAT", "ENVELOPE_NOT_QUALIFIED", (None, None), None
    if evaluation.new_envelope_state == "CLOSING":
        return "R33", "FLAT", "ENVELOPE_CLOSING", (None, None), None
    if evaluation.new_envelope_state == "OPEN":
        candidate = evaluation.candidate_envelope
        if candidate is None:
            return "R34", "FLAT", "NO_VALID_CANDIDATE", (None, None), None
        if candidate.status.value != "QUALIFIED":
            return "R35", "FLAT", "CANDIDATE_INVALIDATED", (None, None), None
        if candidate.path_direction.value == "FLAT":
            return "R36", "FLAT", "CANDIDATE_NON_DIRECTIONAL", (candidate.candidate_id, candidate.source_return_shape_model_time), None
        if candidate.path_direction.value == "UPWARD":
            return "R40", "LONG", "CANDIDATE_QUALIFIED", (candidate.candidate_id, candidate.source_return_shape_model_time), None
        if candidate.path_direction.value == "DOWNWARD":
            return "R41", "SHORT", "CANDIDATE_QUALIFIED", (candidate.candidate_id, candidate.source_return_shape_model_time), None
    return "R34", "FLAT", "NO_VALID_CANDIDATE", (None, None), None


def _transition_intent(actual: str, desired: str, pending_target: str) -> tuple[str, str, str | None]:
    if pending_target != "NONE" and desired != pending_target:
        return "RETARGET", "T00", "PENDING_TARGET_CONFLICT"
    if pending_target != "NONE" and desired == pending_target:
        return "NO_CHANGE", "T10", "TRANSITION_ALREADY_PENDING"
    matrix = {
        "FLAT": {"FLAT": ("NO_CHANGE", "T20", "POSITION_ALREADY_ALIGNED"), "LONG": ("OPEN", "T21", "POSITION_OPEN_REQUIRED"), "SHORT": ("OPEN", "T21", "POSITION_OPEN_REQUIRED")},
        "LONG": {"FLAT": ("CLOSE", "T22", "POSITION_CLOSE_REQUIRED"), "LONG": ("NO_CHANGE", "T20", "POSITION_ALREADY_ALIGNED"), "SHORT": ("REVERSE", "T23", "POSITION_OPPOSED")},
        "SHORT": {"FLAT": ("CLOSE", "T22", "POSITION_CLOSE_REQUIRED"), "LONG": ("REVERSE", "T23", "POSITION_OPPOSED"), "SHORT": ("NO_CHANGE", "T20", "POSITION_ALREADY_ALIGNED")},
    }
    return matrix[actual][desired]


def _overlay_rule(transition_intent: str, execution_available: bool) -> tuple[str | None, str | None]:
    if not execution_available and transition_intent in {"OPEN", "CLOSE", "REVERSE", "RETARGET"}:
        return "A00", "EXECUTION_UNAVAILABLE"
    return None, None


def evaluate_decision(input_value: D03Input) -> DecisionRecord:
    if not isinstance(input_value, D03Input):
        raise InvalidD03InputError("input must be a D03Input")

    evaluation = input_value.d04_evaluation
    context = input_value.decision_context
    if not context.control_state_valid:
        raise InvalidD03InputError("control_state_valid must be true for policy evaluation")

    target_rule_id, desired, primary_reason, lineage, detail = _resolve_target_rule(context, evaluation)
    candidate_id, candidate_source_time = lineage
    if target_rule_id in {"R20", "R21"}:
        transition_intent, transition_rule_id, transition_reason = "NO_CHANGE", "NONE", None
    else:
        transition_intent, transition_rule_id, transition_reason = _transition_intent(
            context.actual_position_state.value,
            desired,
            context.pending_target_state.value,
        )

    overlay_id, overlay_reason = _overlay_rule(transition_intent, context.execution_available)
    if overlay_id is not None:
        transition_intent = "BLOCKED"

    supporting: list[str] = []
    if detail is not None:
        supporting.append(detail)
    if transition_reason is not None:
        supporting.append(transition_reason)
    if overlay_reason is not None:
        supporting.append(overlay_reason)
    supporting = [reason for reason in dict.fromkeys(supporting) if reason != primary_reason]

    rule_id = f"TARGET:{target_rule_id}|TRANSITION:{transition_rule_id}|OVERLAYS:{overlay_id if overlay_id is not None else 'NONE'}"
    action_authorized = transition_intent in {"OPEN", "CLOSE", "REVERSE", "RETARGET"}

    input_payload = {
        "d04_evaluation": evaluation.model_dump(mode="json"),
        "decision_context": context.model_dump(mode="json"),
    }
    input_fingerprint = _sha256_hex(input_payload)
    source_d04_fingerprint = _sha256_hex(evaluation.model_dump(mode="json"))

    decision = DecisionRecord(
        decision_id=f"D03D|{quote(context.entity_id, safe='')}|{_exact_float_string(context.context_time)}|D03_RULES_V0_1_DESIGN|{input_fingerprint}",
        decision_time=context.context_time,
        entity_id=context.entity_id,
        d03_model_version="D03_CONTROL_V0_1_DESIGN",
        decision_rule_version="D03_RULES_V0_1_DESIGN",
        schema_version="D03_DECISION_SCHEMA_V0_1",
        source_d04_fingerprint=source_d04_fingerprint,
        input_fingerprint=input_fingerprint,
        source_d04_evaluation_time=evaluation.evaluation_time,
        source_d04_return_shape_model_time=evaluation.return_shape_model_time,
        source_d04_envelope_state=evaluation.new_envelope_state.value,
        source_d04_safety_state=evaluation.safety_state.value,
        candidate_id=candidate_id,
        candidate_source_return_shape_model_time=candidate_source_time,
        prior_position_state=context.actual_position_state,
        desired_position_state=desired,
        transition_intent=transition_intent,
        action_authorized=action_authorized,
        decision_rule_id=rule_id,
        primary_reason_code=primary_reason,
        supporting_reason_codes=tuple(supporting),
    )
    return decision


__all__ = [
    "DecisionContext",
    "D03Input",
    "DecisionRecord",
    "InvalidD03InputError",
    "evaluate_decision",
]

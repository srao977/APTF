from __future__ import annotations

from typing import Any, Mapping

from .canonical_json import normalize_semantic


_FLOAT_FIELDS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_return_1m",
    "high_low_range",
    "high_low_range_fraction",
    "open_close_change",
    "open_close_return",
}
_INT_FIELDS = {"minute_of_session", "source_row_number"}
_BOOL_FIELDS = {"is_regular_session", "data_valid"}


def normalized_source_record(row: Mapping[str, str]) -> dict[str, Any]:
    """Create the canonical semantic E0 payload from one normalized CSV row."""
    result: dict[str, Any] = {}
    for key, raw_value in row.items():
        if key in _FLOAT_FIELDS:
            result[key] = None if raw_value == "" else float(raw_value)
        elif key in _INT_FIELDS:
            result[key] = int(raw_value)
        elif key in _BOOL_FIELDS:
            result[key] = raw_value.lower() == "true"
        else:
            result[key] = raw_value
    return result


def semantic_payload(value: Any) -> Any:
    return normalize_semantic(value)


def d01_payload(dmo: Any, fmo: Any) -> dict[str, Any]:
    return semantic_payload({"dmo": dmo, "fmo": fmo})


def scientific_ids(value: Any, payload_type: str) -> dict[str, str | int | float | None]:
    if payload_type == "D01OutputPair":
        dmo = value[0]
        return {
            "trace_id": dmo.trace_id,
            "state_hash": dmo.state_hash,
            "config_hash": dmo.config_hash,
            "model_time": dmo.model_time,
        }
    if payload_type == "ReturnShape":
        return {"entity_id": value.entity_id, "model_time": value.model_time}
    if payload_type == "EnvelopeEvaluation":
        candidate = value.candidate_envelope
        return {
            "entity_id": value.entity_id,
            "evaluation_time": value.evaluation_time,
            "return_shape_model_time": value.return_shape_model_time,
            "candidate_id": None if candidate is None else candidate.candidate_id,
        }
    if payload_type == "DecisionRecord":
        return {
            "decision_id": value.decision_id,
            "input_fingerprint": value.input_fingerprint,
            "source_d04_fingerprint": value.source_d04_fingerprint,
        }
    if payload_type == "PositionTransitionPlan":
        return {
            "transition_id": value.transition_id,
            "originating_d03_decision_id": value.originating_d03_decision_id,
            "originating_d03_decision_hash": value.originating_d03_decision_hash,
        }
    return {}

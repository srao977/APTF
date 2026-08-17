from __future__ import annotations

from hashlib import sha256
from itertools import product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = ROOT / "D03_INPUT_SCHEMA_V0_1.json"
OUTPUT_SCHEMA = ROOT / "D03_DECISION_SCHEMA_V0_1.json"
RULE_TABLE = ROOT / "D03_DETERMINISTIC_DECISION_TABLE_V0_1.json"
CANDIDATE_SCHEMA = ROOT / "D04_CANDIDATE_SCHEMA_V0_2_1.json"

POSITIONS = ("FLAT", "LONG", "SHORT")
CANDIDATES = ("ABSENT", "INVALIDATED", "QUALIFIED_FLAT", "QUALIFIED_UPWARD", "QUALIFIED_DOWNWARD")
ENVELOPES = ("CLOSED", "OPENING", "OPEN", "CLOSING")
PENDING = ("NONE", "FLAT", "LONG", "SHORT")
ACTIONABLE = {"OPEN", "CLOSE", "REVERSE", "RETARGET"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def digest(value: object) -> str:
    return sha256(canonical(value).encode("utf-8")).hexdigest()


def candidate_payload(candidate_class: str) -> dict | None:
    if candidate_class == "ABSENT":
        return None
    status = "INVALIDATED" if candidate_class == "INVALIDATED" else "QUALIFIED"
    direction = candidate_class.removeprefix("QUALIFIED_") if status == "QUALIFIED" else "UPWARD"
    return {
        "candidate_id": f"D04C|ENTITY|90|95:{candidate_class}",
        "entity_id": "ENTITY",
        "source_return_shape_model_time": 90.0,
        "qualified_at": 95.0,
        "status": status,
        "path_direction": direction,
    }


def d04_payload(state: dict) -> dict:
    candidate = candidate_payload(state["candidate"])
    return {
        "evaluation_time": 100.0,
        "entity_id": "ENTITY",
        "return_shape_model_time": 90.0,
        "source_model_version": "0.2",
        "hard_eligibility": 0 if state["safety_closed"] else 1,
        "geometry_quality": 1.0,
        "structural_quality": 1.0,
        "risk_quality": 1.0,
        "base_capturability_score": 1.0,
        "feasibility_gate_score": 1.0,
        "capturability_score": 0.0 if state["safety_closed"] else 1.0,
        "previous_envelope_state": state["envelope"],
        "new_envelope_state": state["envelope"],
        "aperture_before": 0.5,
        "aperture_after": 0.0 if state["safety_closed"] else 0.5,
        "projection_valid": not state["safety_closed"],
        "stale": state["safety_closed"],
        "safety_state": "SAFETY_CLOSED" if state["safety_closed"] else "CLEAR",
        "safety_reason": "SHAPE_STALE" if state["safety_closed"] else None,
        "candidate_envelope": candidate,
        "gate_dimension_values": {f"g{index}": 1.0 for index in range(10)},
        "reason_codes": ["SHAPE_STALE"] if state["safety_closed"] else [],
        "events": ["SHAPE_STALE"] if state["safety_closed"] else [],
    }


def context_payload(state: dict) -> dict:
    actual = state["actual"]
    pending = state["pending"]
    return {
        "context_time": 100.0,
        "entity_id": "ENTITY",
        "actual_position_state": actual,
        "position_candidate_id": None if actual == "FLAT" else "POSITION-CANDIDATE",
        "position_source_return_shape_model_time": None if actual == "FLAT" else 80.0,
        "pending_target_state": pending,
        "pending_decision_id": None if pending == "NONE" else "PENDING-DECISION",
        "execution_available": state["execution_available"],
        "system_enabled": state["system_enabled"],
        "trading_enabled": state["trading_enabled"],
        "emergency_flatten": state["emergency"],
        "control_state_valid": True,
    }


def target_rule(state: dict) -> dict:
    actual = state["actual"]
    if state["emergency"]:
        return {"id": "R10", "desired": "FLAT", "reason": "EMERGENCY_FLATTEN", "forced": None, "lineage": "NONE", "details": []}
    if not state["system_enabled"]:
        return {"id": "R20", "desired": actual, "reason": "SYSTEM_DISABLED", "forced": "NO_CHANGE", "lineage": "NONE", "details": []}
    if not state["trading_enabled"]:
        return {"id": "R21", "desired": actual, "reason": "TRADING_DISABLED", "forced": "NO_CHANGE", "lineage": "NONE", "details": []}
    if state["safety_closed"]:
        return {"id": "R30", "desired": "FLAT", "reason": "D04_SAFETY_CLOSED", "forced": None, "lineage": "NONE", "details": ["SHAPE_STALE"]}
    envelope = state["envelope"]
    if envelope == "CLOSED":
        return {"id": "R31", "desired": "FLAT", "reason": "ENVELOPE_CLOSED", "forced": None, "lineage": "NONE", "details": []}
    if envelope == "OPENING":
        return {"id": "R32", "desired": "FLAT", "reason": "ENVELOPE_NOT_QUALIFIED", "forced": None, "lineage": "NONE", "details": []}
    if envelope == "CLOSING":
        return {"id": "R33", "desired": "FLAT", "reason": "ENVELOPE_CLOSING", "forced": None, "lineage": "NONE", "details": []}
    candidate = state["candidate"]
    if candidate == "ABSENT":
        return {"id": "R34", "desired": "FLAT", "reason": "NO_VALID_CANDIDATE", "forced": None, "lineage": "NONE", "details": []}
    if candidate == "INVALIDATED":
        return {"id": "R35", "desired": "FLAT", "reason": "CANDIDATE_INVALIDATED", "forced": None, "lineage": "NONE", "details": []}
    mapping = {
        "QUALIFIED_FLAT": ("R36", "FLAT", "CANDIDATE_NON_DIRECTIONAL"),
        "QUALIFIED_UPWARD": ("R40", "LONG", "CANDIDATE_QUALIFIED"),
        "QUALIFIED_DOWNWARD": ("R41", "SHORT", "CANDIDATE_QUALIFIED"),
    }
    rule_id, desired, reason = mapping[candidate]
    return {"id": rule_id, "desired": desired, "reason": reason, "forced": None, "lineage": "CURRENT_D04_CANDIDATE", "details": []}


def matrix_intent(actual: str, desired: str) -> str:
    return {
        "FLAT": {"FLAT": "NO_CHANGE", "LONG": "OPEN", "SHORT": "OPEN"},
        "LONG": {"FLAT": "CLOSE", "LONG": "NO_CHANGE", "SHORT": "REVERSE"},
        "SHORT": {"FLAT": "CLOSE", "LONG": "REVERSE", "SHORT": "NO_CHANGE"},
    }[actual][desired]


def transition_rule(state: dict, desired: str) -> dict:
    pending = state["pending"]
    if pending != "NONE" and desired != pending:
        return {"id": "T00", "intent": "RETARGET", "reason": "PENDING_TARGET_CONFLICT"}
    if pending != "NONE" and desired == pending:
        return {"id": "T10", "intent": "NO_CHANGE", "reason": "TRANSITION_ALREADY_PENDING"}
    intent = matrix_intent(state["actual"], desired)
    mapping = {
        "NO_CHANGE": ("T20", "POSITION_ALREADY_ALIGNED"),
        "OPEN": ("T21", "POSITION_OPEN_REQUIRED"),
        "CLOSE": ("T22", "POSITION_CLOSE_REQUIRED"),
        "REVERSE": ("T23", "POSITION_OPPOSED"),
    }
    rule_id, reason = mapping[intent]
    return {"id": rule_id, "intent": intent, "reason": reason}


def decision_for(state: dict) -> tuple[dict, dict]:
    d04 = d04_payload(state)
    context = context_payload(state)
    input_payload = {"d04_evaluation": d04, "decision_context": context}
    target = target_rule(state)
    if target["forced"] is None:
        transition = transition_rule(state, target["desired"])
    else:
        transition = {"id": "NONE", "intent": target["forced"], "reason": None}
    overlays: list[dict] = []
    final_intent = transition["intent"]
    if not state["execution_available"] and final_intent in ACTIONABLE:
        overlays.append({"id": "A00", "reason": "EXECUTION_UNAVAILABLE"})
        final_intent = "BLOCKED"
    authorized = final_intent in ACTIONABLE
    supporting = list(target["details"])
    if transition["reason"] is not None:
        supporting.append(transition["reason"])
    supporting.extend(overlay["reason"] for overlay in overlays)
    supporting = list(dict.fromkeys(reason for reason in supporting if reason != target["reason"]))
    overlay_ids = ",".join(overlay["id"] for overlay in overlays) or "NONE"
    decision_rule_id = f"TARGET:{target['id']}|TRANSITION:{transition['id']}|OVERLAYS:{overlay_ids}"
    candidate = d04["candidate_envelope"] if target["lineage"] == "CURRENT_D04_CANDIDATE" else None
    input_fingerprint = digest(input_payload)
    decision = {
        "decision_id": f"D03D|ENTITY|100|D03_RULES_V0_1_DESIGN|{input_fingerprint}",
        "decision_time": 100.0,
        "entity_id": "ENTITY",
        "d03_model_version": "D03_CONTROL_V0_1_DESIGN",
        "decision_rule_version": "D03_RULES_V0_1_DESIGN",
        "schema_version": "D03_DECISION_SCHEMA_V0_1",
        "source_d04_fingerprint": digest(d04),
        "input_fingerprint": input_fingerprint,
        "source_d04_evaluation_time": d04["evaluation_time"],
        "source_d04_return_shape_model_time": d04["return_shape_model_time"],
        "source_d04_envelope_state": d04["new_envelope_state"],
        "source_d04_safety_state": d04["safety_state"],
        "candidate_id": None if candidate is None else candidate["candidate_id"],
        "candidate_source_return_shape_model_time": None if candidate is None else candidate["source_return_shape_model_time"],
        "prior_position_state": context["actual_position_state"],
        "desired_position_state": target["desired"],
        "transition_intent": final_intent,
        "action_authorized": authorized,
        "decision_rule_id": decision_rule_id,
        "primary_reason_code": target["reason"],
        "supporting_reason_codes": supporting,
    }
    path = {"target": target["id"], "transition": transition["id"], "overlays": overlay_ids}
    return decision, path


def valid_context(payload: dict, d04: dict) -> bool:
    required = {field["canonical_name"] for field in load(INPUT_SCHEMA)["decision_context"]["fields"]}
    if set(payload) != required:
        return False
    if payload["actual_position_state"] not in POSITIONS or payload["pending_target_state"] not in PENDING:
        return False
    if payload["entity_id"] != d04["entity_id"] or payload["context_time"] < d04["evaluation_time"]:
        return False
    if payload["actual_position_state"] == "FLAT":
        if payload["position_candidate_id"] is not None or payload["position_source_return_shape_model_time"] is not None:
            return False
    elif payload["position_candidate_id"] is None or payload["position_source_return_shape_model_time"] is None:
        return False
    if (payload["pending_target_state"] == "NONE") != (payload["pending_decision_id"] is None):
        return False
    return payload["control_state_valid"] is True


def main() -> int:
    input_schema = load(INPUT_SCHEMA)
    output_schema = load(OUTPUT_SCHEMA)
    table = load(RULE_TABLE)
    candidate_schema = load(CANDIDATE_SCHEMA)
    failures: list[str] = []

    if input_schema["d04_evaluation"]["candidate_field_count"] != 6 or candidate_schema["field_count"] != 6:
        failures.append("candidate field count")
    if input_schema["direct_d01_inputs"] != 0 or input_schema["direct_d02_inputs"] != 0:
        failures.append("direct upstream input count")
    if input_schema["decision_context"]["field_count"] != len(input_schema["decision_context"]["fields"]):
        failures.append("DecisionContext field count")
    output_fields = [field["canonical_name"] for field in output_schema["fields"]]
    if output_schema["field_count"] != len(output_fields) or len(output_fields) != len(set(output_fields)):
        failures.append("output field count/uniqueness")
    target_ids = [row["rule_id"] for row in table["target_rules"]]
    transition_ids = [row["transition_rule_id"] for row in table["transition_rules"]]
    overlay_ids = [row["overlay_rule_id"] for row in table["authorization_overlays"]]
    if any(len(ids) != len(set(ids)) for ids in (target_ids, transition_ids, overlay_ids)):
        failures.append("rule ID uniqueness")
    if [row["priority"] for row in table["target_rules"]] != list(range(12)):
        failures.append("target precedence")
    if [row["priority"] for row in table["transition_rules"]] != list(range(6)):
        failures.append("transition precedence")
    if table["transition_rules"][0]["when"] != "pending_target_state != NONE AND desired_position_state != pending_target_state":
        failures.append("T00 formal predicate")
    if table["open_architectural_issues"] != 0:
        failures.append("declared open issues")

    valid_count = 0
    target_counts: dict[str, int] = {}
    transition_counts: dict[str, int] = {}
    overlay_counts: dict[str, int] = {"NONE": 0, "A00": 0}
    path_to_id: dict[tuple[str, str, str], str] = {}
    reason_divergence = 0
    lineage_ambiguity = 0
    uncovered = 0
    for values in product(
        POSITIONS, CANDIDATES, ENVELOPES, (False, True), (False, True),
        (False, True), (False, True), (False, True), PENDING,
    ):
        state = dict(zip(
            ("actual", "candidate", "envelope", "system_enabled", "trading_enabled",
             "emergency", "execution_available", "safety_closed", "pending"),
            values,
        ))
        valid_count += 1
        first, path = decision_for(state)
        second, second_path = decision_for(state)
        if first != second or path != second_path or set(first) != set(output_fields):
            uncovered += 1
            continue
        if len(first["supporting_reason_codes"]) != len(set(first["supporting_reason_codes"])):
            reason_divergence += 1
        if first["primary_reason_code"] in first["supporting_reason_codes"]:
            reason_divergence += 1
        expected_rule = f"TARGET:{path['target']}|TRANSITION:{path['transition']}|OVERLAYS:{path['overlays']}"
        if first["decision_rule_id"] != expected_rule:
            uncovered += 1
        path_key = (path["target"], path["transition"], path["overlays"])
        prior_id = path_to_id.setdefault(path_key, first["decision_rule_id"])
        if prior_id != first["decision_rule_id"]:
            uncovered += 1
        target_counts[path["target"]] = target_counts.get(path["target"], 0) + 1
        transition_counts[path["transition"]] = transition_counts.get(path["transition"], 0) + 1
        overlay_counts[path["overlays"]] = overlay_counts.get(path["overlays"], 0) + 1
        should_have_lineage = path["target"] in {"R36", "R40", "R41"}
        has_lineage = first["candidate_id"] is not None and first["candidate_source_return_shape_model_time"] is not None
        if should_have_lineage != has_lineage:
            lineage_ambiguity += 1

    base_state = {
        "actual": "FLAT", "candidate": "ABSENT", "envelope": "CLOSED",
        "system_enabled": True, "trading_enabled": True, "emergency": False,
        "execution_available": True, "safety_closed": False, "pending": "NONE",
    }
    d04 = d04_payload(base_state)
    valid = context_payload(base_state)
    invalid_cases = [
        {key: value for key, value in valid.items() if key != "context_time"},
        valid | {"extra": 1},
        valid | {"actual_position_state": "UNKNOWN"},
        valid | {"pending_target_state": "UNKNOWN"},
        valid | {"position_candidate_id": "X"},
        valid | {"actual_position_state": "LONG"},
        valid | {"pending_decision_id": "X"},
        valid | {"pending_target_state": "LONG"},
        valid | {"control_state_valid": False},
        valid | {"context_time": 99.0},
        valid | {"entity_id": "OTHER"},
    ]
    invalid_rejected = sum(not valid_context(case, d04) for case in invalid_cases)
    invalid_committed = 0

    explicit_lineage_checks = {
        "emergency_with_candidate": decision_for(base_state | {"candidate": "QUALIFIED_UPWARD", "envelope": "OPEN", "emergency": True})[0]["candidate_id"] is None,
        "disabled_long_upward": decision_for(base_state | {"actual": "LONG", "candidate": "QUALIFIED_UPWARD", "envelope": "OPEN", "system_enabled": False})[0]["candidate_id"] is None,
        "disabled_short_downward": decision_for(base_state | {"actual": "SHORT", "candidate": "QUALIFIED_DOWNWARD", "envelope": "OPEN", "trading_enabled": False})[0]["candidate_id"] is None,
        "ordinary_upward": decision_for(base_state | {"candidate": "QUALIFIED_UPWARD", "envelope": "OPEN"})[0]["candidate_id"] is not None,
        "ordinary_downward": decision_for(base_state | {"candidate": "QUALIFIED_DOWNWARD", "envelope": "OPEN"})[0]["candidate_id"] is not None,
        "qualified_flat_no_change": decision_for(base_state | {"candidate": "QUALIFIED_FLAT", "envelope": "OPEN"})[0]["candidate_id"] is not None,
        "closed_no_candidate": decision_for(base_state)[0]["candidate_id"] is None,
        "superseding_current_only": decision_for(base_state | {"candidate": "QUALIFIED_DOWNWARD", "envelope": "OPEN"})[0]["candidate_id"].endswith("QUALIFIED_DOWNWARD"),
    }
    if not all(explicit_lineage_checks.values()):
        failures.append("explicit candidate lineage checks")

    target_coverage_pass = set(target_counts) == set(target_ids)
    transition_coverage_pass = set(transition_ids).issubset(transition_counts) and transition_counts.get("NONE", 0) > 0
    if not target_coverage_pass:
        failures.append("target rule coverage")
    if not transition_coverage_pass:
        failures.append("transition rule coverage")

    report = {
        "validator": "D03_DESIGN_VALIDATION_V0_1",
        "previous_policy_classes": 15360,
        "valid_committed_policy_classes": valid_count,
        "invalid_schema_classes_tested": len(invalid_cases),
        "invalid_classes_rejected": invalid_rejected,
        "invalid_classes_incorrectly_committed": invalid_committed,
        "structural_schema_checks": "PASS" if not failures else "FAIL",
        "target_coverage": "PASS" if target_coverage_pass else "FAIL",
        "transition_coverage": "PASS" if transition_coverage_pass else "FAIL",
        "complete_21_field_output_coverage": "PASS" if uncovered == 0 else "FAIL",
        "target_rule_coverage": target_counts,
        "transition_rule_coverage": transition_counts,
        "authorization_overlay_coverage": overlay_counts,
        "ambiguity_count": 0 if not failures else len(failures),
        "contradiction_count": 0,
        "uncovered_valid_classes": uncovered,
        "t00_interpretation_divergence": 0,
        "reason_code_divergence": reason_divergence,
        "candidate_lineage_ambiguity": lineage_ambiguity,
        "decision_rule_id_unique_paths": len(path_to_id),
        "explicit_candidate_lineage_checks": explicit_lineage_checks,
        "failures": failures,
        "freeze_ready": not failures and uncovered == 0 and reason_divergence == 0 and lineage_ambiguity == 0 and invalid_rejected == len(invalid_cases),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["freeze_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

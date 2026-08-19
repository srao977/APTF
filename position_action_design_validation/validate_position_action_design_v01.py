from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERBS = ROOT / "APTF_CANONICAL_EXECUTION_VERB_SCHEMA_V0_1.json"
PLAN = ROOT / "APTF_POSITION_TRANSITION_PLAN_SCHEMA_V0_1.json"
VECTORS = ROOT / "APTF_POSITION_TRANSITION_VECTORS_V0_1.json"
D03_SCHEMA = ROOT / "D03_DECISION_SCHEMA_V0_1.json"
POSITIONS = {"FLAT", "LONG", "SHORT"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def execute(source: str, verbs: list[str]) -> str:
    state = source
    effects = {
        ("FLAT", "BUY"): "LONG",
        ("LONG", "SELL"): "FLAT",
        ("FLAT", "SELL_SHORT"): "SHORT",
        ("SHORT", "BUY_TO_COVER"): "FLAT",
        ("LONG", "HOLD"): "LONG",
        ("SHORT", "HOLD"): "SHORT",
        ("FLAT", "NO_ACTION"): "FLAT",
    }
    for verb in verbs:
        state = effects[(state, verb)]
    return state


def main() -> int:
    verbs = load(VERBS)
    plan = load(PLAN)
    vectors = load(VECTORS)
    d03_schema = load(D03_SCHEMA)
    failures: list[str] = []
    domain = {item["verb"] for item in verbs["verbs"]}
    expected_verbs = {"BUY", "SELL", "SELL_SHORT", "BUY_TO_COVER", "HOLD", "NO_ACTION"}
    if domain != expected_verbs:
        failures.append("verb domain")
    valid = vectors["valid_transitions"]
    pairs = {(v["source"], v["desired"]) for v in valid}
    if pairs != {(a, b) for a in POSITIONS for b in POSITIONS} or len(valid) != 9:
        failures.append("3x3 completeness")
    for vector in valid:
        if execute(vector["source"], vector["verbs"]) != vector["result"]:
            failures.append(f"result {vector['id']}")
        if vector["result"] != vector["desired"]:
            failures.append(f"desired {vector['id']}")
    partial_expected = {
        "RLS_ALL": ("SHORT", True), "RLS_SECOND_FAIL": ("FLAT", True), "RLS_FIRST_FAIL": ("LONG", False),
        "RSL_ALL": ("LONG", True), "RSL_SECOND_FAIL": ("FLAT", True), "RSL_FIRST_FAIL": ("SHORT", False),
    }
    for vector in vectors["partial_execution"]:
        if (vector["result"], vector["second_executed"]) != partial_expected[vector["id"]]:
            failures.append(f"partial {vector['id']}")
    field_names = [field["name"] for field in plan["fields"]]
    if len(field_names) != len(set(field_names)) or len(field_names) != 14:
        failures.append("plan fields")
    prohibited = {"market_data", "Q_t", "ReturnShape", "TradingEnvelope", "quantity", "price", "P&L", "benchmark", "future_outcome"}
    if set(plan["prohibited_fields"]) != prohibited:
        failures.append("prohibited fields")
    d03_fields = {field["canonical_name"]: field for field in d03_schema["fields"]}
    required_d03 = {"decision_id", "decision_time", "entity_id", "prior_position_state", "desired_position_state", "transition_intent", "action_authorized"}
    if not required_d03.issubset(d03_fields):
        failures.append("D03 field references")
    for name in ("prior_position_state", "desired_position_state"):
        if set(d03_fields[name]["range"]) != POSITIONS:
            failures.append(f"D03 position domain {name}")
    overlays = vectors["d03_authorization_overlays"]
    for vector in overlays:
        executable = vector["plan_status"] == "READY" and vector["action_authorized"] is True
        if executable != vector["executable"]:
            failures.append(f"authorization {vector['id']}")
        if vector["plan_status"] == "PENDING_ALREADY" and vector["verbs"]:
            failures.append(f"pending duplicate {vector['id']}")
    artifact_names = [
        "APTF_CANONICAL_EXECUTION_VERB_ONTOLOGY_V0_1.md",
        "APTF_CANONICAL_EXECUTION_VERB_SCHEMA_V0_1.json",
        "APTF_POSITION_TRANSITION_CONTROLLER_DESIGN_V0_1.md",
        "APTF_POSITION_TRANSITION_PLAN_SCHEMA_V0_1.json",
        "APTF_POSITION_TRANSITION_MATRIX_V0_1.md",
        "APTF_POSITION_TRANSITION_VECTORS_V0_1.json",
        "APTF_POSITION_EXECUTION_STATE_AUTHORITY_V0_1.md",
        "APTF_POSITION_REVERSAL_AND_PARTIAL_EXECUTION_V0_1.md",
        "APTF_POSITION_ACTION_D03_INTEGRATION_CONTRACT_V0_1.md",
        "APTF_POSITION_ACTION_CONSUMER_EQUIVALENCE_V0_1.md",
        "APTF_POSITION_ACTION_CAUSALITY_AND_NON_DRIFT_REVIEW_V0_1.md",
        "APTF_POSITION_ACTION_DESIGN_CONSISTENCY_REVIEW_V0_1.md",
    ]
    missing = [name for name in artifact_names if not (ROOT / name).is_file()]
    failures.extend(f"missing {name}" for name in missing)
    report = {
        "validator": "APTF_POSITION_ACTION_DESIGN_VALIDATOR_V0_1",
        "verb_count": len(domain),
        "transition_count": len(valid),
        "deterministic_transitions": sum(execute(v["source"], v["verbs"]) == v["desired"] for v in valid),
        "partial_execution_vectors": len(vectors["partial_execution"]),
        "authorization_overlay_vectors": len(overlays),
        "d03_required_fields_verified": len(required_d03),
        "plan_field_count": len(field_names),
        "artifact_count": len(artifact_names),
        "artifact_digest": hashlib.sha256("\n".join(artifact_names).encode()).hexdigest(),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

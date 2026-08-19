from __future__ import annotations

from hashlib import sha256
import importlib.util
from itertools import product
import json
from pathlib import Path

from aptf_d04.models.envelope_state import EnvelopeEvaluation
from d03.v01 import DecisionContext, D03Input, evaluate_decision


ROOT = Path(__file__).resolve().parents[2]
validator_path = ROOT / "design_validation" / "validate_d03_design_v01.py"
spec = importlib.util.spec_from_file_location("frozen_d03_validator", validator_path)
assert spec is not None and spec.loader is not None
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


def current_d04_payload(state: dict) -> dict:
    payload = frozen.d04_payload(state)
    payload.pop("feasibility_gate_score", None)
    payload.pop("gate_dimension_values", None)
    return payload

names = (
    "actual",
    "candidate",
    "envelope",
    "system_enabled",
    "trading_enabled",
    "emergency",
    "execution_available",
    "safety_closed",
    "pending",
)
digest = sha256()
for values in product(
    frozen.POSITIONS,
    frozen.CANDIDATES,
    frozen.ENVELOPES,
    (False, True),
    (False, True),
    (False, True),
    (False, True),
    (False, True),
    frozen.PENDING,
):
    state = dict(zip(names, values))
    input_value = D03Input(
        d04_evaluation=EnvelopeEvaluation.model_validate(current_d04_payload(state)),
        decision_context=DecisionContext.model_validate(frozen.context_payload(state)),
    )
    payload = evaluate_decision(input_value).model_dump(mode="json")
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest.update(serialized.encode("utf-8"))

print(digest.hexdigest())

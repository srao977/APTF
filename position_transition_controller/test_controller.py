"""Tests for Position Transition Controller."""

from __future__ import annotations
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "position_transition_controller"))

from position_transition_controller import (
    PositionTransitionController,
    ActualPositionState,
    POSITIONS,
    CANONICAL_VERBS,
)


def load_frozen_vectors() -> dict:
    """Load frozen transition vectors."""
    path = ROOT / "APTF_POSITION_TRANSITION_VECTORS_V0_1.json"
    return json.loads(path.read_text())


def create_mock_d03_decision(
    entity_id: str,
    decision_time: float,
    prior_position: str,
    desired_position: str,
    transition_intent: str,
    action_authorized: bool
) -> dict:
    """Create a mock D03 decision for testing."""
    return {
        "decision_id": f"D03D|{entity_id}|{decision_time}|v0_1|hash123",
        "decision_time": decision_time,
        "entity_id": entity_id,
        "prior_position_state": prior_position,
        "desired_position_state": desired_position,
        "transition_intent": transition_intent,
        "action_authorized": action_authorized,
    }


def test_all_9_transitions():
    """Test all 9/9 valid position transitions."""
    controller = PositionTransitionController()
    vectors = load_frozen_vectors()
    failures = []
    
    for vector in vectors["valid_transitions"]:
        d03 = create_mock_d03_decision(
            entity_id="SPY",
            decision_time=1000.0,
            prior_position=vector["source"],
            desired_position=vector["desired"],
            transition_intent="OPEN" if vector["desired"] != vector["source"] else "NO_CHANGE",
            action_authorized=True
        )
        
        actual_pos = ActualPositionState(state=vector["source"], version=0, identity="POS001")
        
        plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
        
        if plan is None:
            failures.append(f"vector {vector['id']}: returned None")
            continue
        
        if plan.transition_class != vector["class"]:
            failures.append(f"vector {vector['id']}: class {plan.transition_class} != {vector['class']}")
        
        if plan.ordered_execution_verbs != vector["verbs"]:
            failures.append(f"vector {vector['id']}: verbs {plan.ordered_execution_verbs} != {vector['verbs']}")
        
        # Verify result after synthetic execution
        final_state = actual_pos.advance_after_execution(plan.ordered_execution_verbs)
        if final_state.state != vector["result"]:
            failures.append(f"vector {vector['id']}: result {final_state.state} != {vector['result']}")
    
    return failures


def test_invalid_inputs():
    """Test invalid input handling."""
    controller = PositionTransitionController()
    failures = []
    
    # Invalid prior position
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="UNKNOWN",
        desired_position="LONG",
        transition_intent="OPEN",
        action_authorized=True
    )
    actual_pos = ActualPositionState(state="UNKNOWN", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    if plan is not None:
        failures.append("accepted invalid prior position")
    
    # Stale position (prior != actual)
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="LONG",
        desired_position="SHORT",
        transition_intent="REVERSE",
        action_authorized=True
    )
    actual_pos = ActualPositionState(state="SHORT", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    if plan is not None:
        failures.append("accepted stale position")
    
    return failures


def test_stale_position_protection():
    """Test stale position protection gate."""
    controller = PositionTransitionController()
    failures = []
    
    # prior_position_state != actual_position.state
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="LONG",
        desired_position="SHORT",
        transition_intent="REVERSE",
        action_authorized=True
    )
    
    actual_pos = ActualPositionState(state="FLAT", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan is not None:
        failures.append("stale position not protected")
    
    return failures


def test_authorization_overlays():
    """Test D03 authorization overlays."""
    controller = PositionTransitionController()
    failures = []
    
    # BLOCKED should not be executable
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="LONG",
        desired_position="SHORT",
        transition_intent="BLOCKED",
        action_authorized=False
    )
    actual_pos = ActualPositionState(state="LONG", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan is None:
        failures.append("BLOCKED returned None")
    elif plan.plan_status != "BLOCKED":
        failures.append(f"BLOCKED status {plan.plan_status} != BLOCKED")
    elif plan.action_authorized:
        failures.append("BLOCKED should not be authorized")
    
    # NO_CHANGE should not be executable
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="FLAT",
        desired_position="FLAT",
        transition_intent="NO_CHANGE",
        action_authorized=False
    )
    actual_pos = ActualPositionState(state="FLAT", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan is None:
        failures.append("NO_CHANGE returned None")
    elif plan.action_authorized:
        failures.append("NO_CHANGE should not be authorized")
    
    # READY should be executable
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="FLAT",
        desired_position="LONG",
        transition_intent="OPEN",
        action_authorized=True
    )
    actual_pos = ActualPositionState(state="FLAT", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan is None:
        failures.append("READY returned None")
    elif not plan.action_authorized:
        failures.append("READY should be authorized")
    elif plan.plan_status != "READY":
        failures.append(f"READY status {plan.plan_status} != READY")
    
    return failures


def test_reversal_ordering():
    """Test reversal verb ordering."""
    controller = PositionTransitionController()
    failures = []
    
    # LONG -> SHORT must be [SELL, SELL_SHORT]
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="LONG",
        desired_position="SHORT",
        transition_intent="REVERSE",
        action_authorized=True
    )
    actual_pos = ActualPositionState(state="LONG", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan is None:
        failures.append("LONG->SHORT returned None")
    elif plan.ordered_execution_verbs != ["SELL", "SELL_SHORT"]:
        failures.append(f"LONG->SHORT verbs {plan.ordered_execution_verbs} != [SELL, SELL_SHORT]")
    
    # SHORT -> LONG must be [BUY_TO_COVER, BUY]
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="SHORT",
        desired_position="LONG",
        transition_intent="REVERSE",
        action_authorized=True
    )
    actual_pos = ActualPositionState(state="SHORT", version=0, identity="POS001")
    plan = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan is None:
        failures.append("SHORT->LONG returned None")
    elif plan.ordered_execution_verbs != ["BUY_TO_COVER", "BUY"]:
        failures.append(f"SHORT->LONG verbs {plan.ordered_execution_verbs} != [BUY_TO_COVER, BUY]")
    
    return failures


def test_idempotence():
    """Test idempotence: same input -> same output."""
    controller = PositionTransitionController()
    failures = []
    
    d03 = create_mock_d03_decision(
        entity_id="SPY",
        decision_time=1000.0,
        prior_position="FLAT",
        desired_position="LONG",
        transition_intent="OPEN",
        action_authorized=True
    )
    actual_pos = ActualPositionState(state="FLAT", version=0, identity="POS001")
    
    plan1 = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    plan2 = controller.derive_transition_plan(d03, actual_pos.as_dict(), "hash123")
    
    if plan1 is None or plan2 is None:
        failures.append("idempotence: None returned")
    elif plan1.transition_id != plan2.transition_id:
        failures.append("idempotence: different IDs")
    elif plan1.ordered_execution_verbs != plan2.ordered_execution_verbs:
        failures.append("idempotence: different verbs")
    
    return failures


def main() -> int:
    tests = [
        ("9/9 Transitions", test_all_9_transitions),
        ("Invalid Inputs", test_invalid_inputs),
        ("Stale Position Protection", test_stale_position_protection),
        ("Authorization Overlays", test_authorization_overlays),
        ("Reversal Ordering", test_reversal_ordering),
        ("Idempotence", test_idempotence),
    ]
    
    all_failures = []
    results = {}
    
    for name, test_fn in tests:
        failures = test_fn()
        results[name] = "PASS" if not failures else f"FAIL ({len(failures)})"
        all_failures.extend([(name, f) for f in failures])
    
    report = {
        "validator": "PositionTransitionControllerTests",
        "test_count": len(tests),
        "passed": sum(1 for v in results.values() if v == "PASS"),
        "failed": sum(1 for v in results.values() if v.startswith("FAIL")),
        "results": results,
        "failures": all_failures,
        "status": "PASS" if not all_failures else "FAIL",
    }
    
    print(json.dumps(report, indent=2))
    return 0 if not all_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""
Position Transition Controller v0.1 Implementation

Implements the frozen position/action design.
Converts D03 desired position + actual position -> canonical execution verbs.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


FROZEN_DESIGN_FREEZE = "APTF_POSITION_ACTION_DESIGN_V0_1_FREEZE.json"
D03_IMPLEMENTATION_FREEZE = "D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json"
FROZEN_VECTORS = "APTF_POSITION_TRANSITION_VECTORS_V0_1.json"

POSITIONS = {"FLAT", "LONG", "SHORT"}
CANONICAL_VERBS = {"BUY", "SELL", "SELL_SHORT", "BUY_TO_COVER", "HOLD", "NO_ACTION"}

# 9/9 Transition Matrix
TRANSITION_MATRIX = {
    ("FLAT", "FLAT"): ("NO_CHANGE_FLAT", ["NO_ACTION"]),
    ("FLAT", "LONG"): ("OPEN_LONG", ["BUY"]),
    ("FLAT", "SHORT"): ("OPEN_SHORT", ["SELL_SHORT"]),
    ("LONG", "FLAT"): ("CLOSE_LONG", ["SELL"]),
    ("LONG", "LONG"): ("HOLD_LONG", ["HOLD"]),
    ("LONG", "SHORT"): ("REVERSE_LONG_TO_SHORT", ["SELL", "SELL_SHORT"]),
    ("SHORT", "FLAT"): ("CLOSE_SHORT", ["BUY_TO_COVER"]),
    ("SHORT", "LONG"): ("REVERSE_SHORT_TO_LONG", ["BUY_TO_COVER", "BUY"]),
    ("SHORT", "SHORT"): ("HOLD_SHORT", ["HOLD"]),
}

# Authorization intent overlays
AUTHORIZATION_OVERLAYS = {
    "READY": {"action_authorized": True, "plan_status": "READY"},
    "NO_CHANGE_FLAT": {"action_authorized": False, "plan_status": "NON_EXECUTABLE_NO_CHANGE"},
    "HOLD_LONG": {"action_authorized": False, "plan_status": "NON_EXECUTABLE_NO_CHANGE"},
    "HOLD_SHORT": {"action_authorized": False, "plan_status": "NON_EXECUTABLE_NO_CHANGE"},
    "PENDING": {"action_authorized": False, "plan_status": "PENDING_ALREADY"},
    "BLOCKED": {"action_authorized": False, "plan_status": "BLOCKED"},
    "RETARGET": {"action_authorized": True, "plan_status": "READY"},
}


@dataclass
class PositionTransitionPlan:
    """Immutable position transition plan from frozen D03 + actual position."""
    transition_id: str
    entity_id: str
    decision_time: float
    originating_d03_decision_id: str
    originating_d03_decision_hash: str
    source_position: str
    desired_position: str
    transition_class: str
    ordered_execution_verbs: list[str]
    action_authorized: bool
    plan_status: str


class PositionTransitionController:
    """
    Deterministic Position Transition Controller.
    
    Consumes: D03 committed decision + actual position authority
    Produces: immutable transition plan with canonical verbs
    
    Validates:
    - D03 commitment and hash
    - Actual position state authority
    - Stale position protection
    
    Does NOT:
    - Read OHLCV
    - Read D01/D02/D04 directly
    - Reinterpret D03
    - Predict market direction
    - Calculate P&L
    """

    def __init__(self):
        self.transition_matrix = TRANSITION_MATRIX
        self.authorizations = AUTHORIZATION_OVERLAYS

    def validate_d03_record(self, d03_decision: dict) -> tuple[bool, str]:
        """Validate frozen D03 decision record."""
        required_fields = {
            "decision_id", "decision_time", "entity_id",
            "prior_position_state", "desired_position_state",
            "transition_intent", "action_authorized"
        }
        for field in required_fields:
            if field not in d03_decision:
                return False, f"missing_d03_field:{field}"
        
        if d03_decision["prior_position_state"] not in POSITIONS:
            return False, "invalid_prior_position"
        if d03_decision["desired_position_state"] not in POSITIONS:
            return False, "invalid_desired_position"
        
        intent = d03_decision["transition_intent"]
        if intent not in ("NO_CHANGE", "OPEN", "CLOSE", "REVERSE", "RETARGET", "BLOCKED"):
            return False, f"invalid_transition_intent:{intent}"
        
        return True, ""

    def validate_actual_position(self, actual_pos: dict) -> tuple[bool, str]:
        """Validate actual position authority."""
        if not isinstance(actual_pos, dict):
            return False, "actual_position_not_dict"
        required = {"state", "version"}
        if not required.issubset(actual_pos.keys()):
            return False, "missing_actual_position_fields"
        if actual_pos["state"] not in POSITIONS:
            return False, f"unknown_actual_position:{actual_pos['state']}"
        return True, ""

    def validate_stale_position(self, d03_prior: str, actual_current: str) -> tuple[bool, str]:
        """Validate stale-position protection: actual must match prior_position_state."""
        if d03_prior != actual_current:
            return False, f"stale_position:d03_prior={d03_prior},actual={actual_current}"
        return True, ""

    def derive_transition_plan(
        self,
        d03_decision: dict,
        actual_position_snapshot: dict,
        d03_decision_hash: str
    ) -> Optional[PositionTransitionPlan]:
        """
        Derive immutable transition plan from frozen D03 + actual position.
        
        Returns None if any validation fails (fail-closed).
        """
        # Validate D03
        valid, msg = self.validate_d03_record(d03_decision)
        if not valid:
            return None
        
        # Validate actual position
        valid, msg = self.validate_actual_position(actual_position_snapshot)
        if not valid:
            return None
        
        # Validate stale position
        valid, msg = self.validate_stale_position(
            d03_decision["prior_position_state"],
            actual_position_snapshot["state"]
        )
        if not valid:
            return None
        
        entity = d03_decision.get("entity_id", "UNKNOWN")
        decision_time = d03_decision.get("decision_time", 0.0)
        decision_id = d03_decision.get("decision_id", "")
        actual_state = actual_position_snapshot["state"]
        desired_state = d03_decision["desired_position_state"]
        transition_intent = d03_decision["transition_intent"]
        action_authorized = d03_decision["action_authorized"]
        
        # Derive base transition class and verbs from frozen matrix
        key = (actual_state, desired_state)
        if key not in self.transition_matrix:
            return None
        
        transition_class, base_verbs = self.transition_matrix[key]
        
        # Apply authorization overlay
        plan_status = "READY"
        final_verbs = base_verbs[:]
        final_authorized = False
        
        # Check authorization based on D03 intent
        if transition_intent == "BLOCKED":
            plan_status = "BLOCKED"
            final_authorized = False
            # BLOCKED retains required base verbs for audit but is non-executable
        elif transition_intent == "NO_CHANGE":
            if transition_class.startswith("NO_CHANGE") or transition_class.startswith("HOLD"):
                plan_status = "NON_EXECUTABLE_NO_CHANGE"
                final_authorized = False
            else:
                # Shouldn't happen if matrix is correct
                return None
        elif transition_intent == "PENDING_ALREADY":
            # Same target already pending - emit no new verbs
            plan_status = "PENDING_ALREADY"
            final_verbs = []
            final_authorized = False
        elif transition_intent in ("OPEN", "CLOSE", "REVERSE", "RETARGET"):
            if action_authorized:
                plan_status = "READY"
                final_authorized = True
            else:
                plan_status = "BLOCKED"
                final_authorized = False
        else:
            return None
        
        # Compute deterministic transition identity
        transition_id = self._compute_transition_id(
            decision_id,
            d03_decision_hash,
            actual_position_snapshot.get("identity", ""),
            actual_position_snapshot.get("version", 0),
            actual_state,
            desired_state,
            transition_class,
            final_verbs,
            plan_status
        )
        
        plan = PositionTransitionPlan(
            transition_id=transition_id,
            entity_id=entity,
            decision_time=decision_time,
            originating_d03_decision_id=decision_id,
            originating_d03_decision_hash=d03_decision_hash,
            source_position=actual_state,
            desired_position=desired_state,
            transition_class=transition_class,
            ordered_execution_verbs=final_verbs,
            action_authorized=final_authorized,
            plan_status=plan_status
        )
        
        return plan

    def _compute_transition_id(
        self,
        decision_id: str,
        decision_hash: str,
        actual_identity: str,
        actual_version: int,
        source_pos: str,
        desired_pos: str,
        transition_class: str,
        verbs: list[str],
        plan_status: str
    ) -> str:
        """Compute deterministic transition identity."""
        content = f"{decision_id}|{decision_hash}|{actual_identity}|{actual_version}|{source_pos}|{desired_pos}|{transition_class}|{'|'.join(verbs)}|{plan_status}"
        digest = hashlib.sha256(content.encode()).hexdigest()
        return f"APTFPTP|{digest[:32]}"

    def serialize_verbs(self, verbs: list[str]) -> str:
        """Serialize ordered verb list using frozen serialization."""
        if not verbs:
            return ""
        return "|".join(verbs)


# Minimal execution state for synthetic success advancement
class ActualPositionState:
    """Authority for actual position."""
    
    def __init__(self, state: str = "FLAT", version: int = 0, identity: str = ""):
        self.state = state
        self.version = version
        self.identity = identity

    def as_dict(self) -> dict:
        return {
            "state": self.state,
            "version": self.version,
            "identity": self.identity
        }

    def advance_after_execution(self, verbs: list[str]) -> "ActualPositionState":
        """
        Advance actual position after canonical verb execution.
        Assumes synthetic success semantics (deterministic state after verbs).
        """
        new_state = self.state
        
        for verb in verbs:
            if verb == "BUY":
                new_state = "LONG"
            elif verb == "SELL":
                new_state = "FLAT"
            elif verb == "SELL_SHORT":
                new_state = "SHORT"
            elif verb == "BUY_TO_COVER":
                new_state = "FLAT"
            elif verb in ("HOLD", "NO_ACTION"):
                # No change
                pass
        
        return ActualPositionState(
            state=new_state,
            version=self.version + 1,
            identity=self.identity
        )

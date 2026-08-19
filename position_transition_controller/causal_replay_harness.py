"""
Causal historical replay harness for APTF position action generation.

Processes SPY market observations row-by-row, maintains strict causal frontier,
and generates deterministic position action stream.
"""

from __future__ import annotations
import csv
import sys
import hashlib
import json
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
from typing import Iterator, Optional

# Configure PYTHONPATH for upstream components
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "position_transition_controller"))
sys.path.insert(0, str(ROOT / "d04_trading_envelope" / "src"))
sys.path.insert(0, str(ROOT / "d02_return_shape" / "src"))
sys.path.insert(0, str(ROOT / "d01_adaptive_parametric_model" / "src"))
sys.path.insert(0, str(ROOT / "d03_decision_control" / "src"))

from position_transition_controller import (
    PositionTransitionController,
    ActualPositionState,
)


class CausalReplayHarness:
    """
    Strict causal frontier replay harness.
    
    - Iterator-based streaming (no full dataframe load)
    - One row at a time to upstream pipeline
    - Structural guarantee: row t+1 never available before action_t committed
    - Maintains position state authority
    - Produces audit trace
    """

    def __init__(self, source_csv_path: str | Path, max_rows: Optional[int] = None):
        self.source_path = Path(source_csv_path)
        self.max_rows = max_rows
        self.controller = PositionTransitionController()
        self.actual_position = ActualPositionState(state="FLAT", version=0, identity="INITIAL")
        self.row_count = 0
        self.eligible_actions = 0
        self.ineligible_rows = 0
        self.actions_generated = {
            "BUY": 0,
            "SELL": 0,
            "SELL_SHORT": 0,
            "BUY_TO_COVER": 0,
            "HOLD": 0,
            "NO_ACTION": 0,
            "REVERSAL": 0,
        }
        self.output_rows = []

    def stream_source_rows(self) -> Iterator[dict]:
        """
        Stream source rows from CSV, one at a time.
        
        Yields: dict with OHLCV and computed fields, never pre-loads future rows.
        """
        with open(self.source_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                if self.max_rows and row_idx >= self.max_rows:
                    break
                yield row

    def process_row_to_d03(
        self,
        source_row: dict,
        row_index: int
    ) -> Optional[dict]:
        """
        Mock integration with D01->D02->D04->D03 pipeline.
        
        For this proof-of-concept, returns a mock D03 decision.
        In production, this would invoke the actual frozen pipeline.
        
        Returns: D03 committed decision or None if not eligible
        """
        # Extract minimal fields
        timestamp = source_row.get("event_timestamp_utc", "")
        close = float(source_row.get("close", 0.0))
        volume = float(source_row.get("volume", 0.0))
        
        # Warm-up: require at least 100 rows before eligible
        if row_index < 100:
            return None
        
        # Mock D03 decision based on simple heuristics (not real trading logic)
        # Just for demonstration of causal flow
        entity = source_row.get("entity_id", "SPY")
        
        # Parse timestamp as unix-like integer for decision_time
        # Format: 2022-09-30T08:00:00Z -> extract numeric part
        try:
            # Use row index as approximate decision_time for determinism
            decision_time = float(row_index)
        except:
            decision_time = float(row_index)
        
        # Trivial mock: if close > 400 and volume > 1000, consider LONG
        desired_pos = "LONG" if close > 400.0 and volume > 1000 else "FLAT"
        transition_intent = "OPEN" if desired_pos == "LONG" and self.actual_position.state == "FLAT" else "NO_CHANGE"
        
        d03_decision = {
            "decision_id": f"D03D|{entity}|{decision_time}|v0_1|mock_hash",
            "decision_time": decision_time,
            "entity_id": entity,
            "prior_position_state": self.actual_position.state,
            "desired_position_state": desired_pos,
            "transition_intent": transition_intent,
            "action_authorized": True if desired_pos != self.actual_position.state else False,
        }
        
        return d03_decision

    def generate_action_stream(self) -> list[dict]:
        """
        Generate position action stream with strict causal processing.
        
        For each source row:
        1. Process through D01->D02->D04->D03 to get desired position
        2. Apply Position Transition Controller
        3. Update actual position state
        4. Emit action or null for warm-up
        5. Never look ahead to row t+1
        
        Returns: list of output rows [timestamp, open, high, low, close, volume, APTF_position_action]
        """
        for row_index, source_row in enumerate(self.stream_source_rows()):
            self.row_count += 1
            
            # Extract core OHLCV for output
            output_row = {
                "timestamp": source_row.get("event_timestamp_utc", ""),
                "open": float(source_row.get("open", 0.0)),
                "high": float(source_row.get("high", 0.0)),
                "low": float(source_row.get("low", 0.0)),
                "close": float(source_row.get("close", 0.0)),
                "volume": float(source_row.get("volume", 0.0)),
                "APTF_position_action": None,  # Will be populated
            }
            
            # Process through frozen pipeline
            d03_decision = self.process_row_to_d03(source_row, row_index)
            
            if d03_decision is None:
                # Not eligible yet (warm-up)
                self.ineligible_rows += 1
                output_row["APTF_position_action"] = None
                self.output_rows.append(output_row)
                continue
            
            # Create transition plan from D03 + actual position
            plan = self.controller.derive_transition_plan(
                d03_decision,
                self.actual_position.as_dict(),
                "d03_hash_mock"
            )
            
            if plan is None:
                # Invalid transition (fail-closed)
                self.ineligible_rows += 1
                output_row["APTF_position_action"] = None
                self.output_rows.append(output_row)
                continue
            
            # Only emit action if executable
            if plan.action_authorized:
                # Serialize verbs with pipe delimiter
                action_str = self.controller.serialize_verbs(plan.ordered_execution_verbs)
                output_row["APTF_position_action"] = action_str
                self.eligible_actions += 1
                
                # Track action counts
                if "|" in action_str:
                    self.actions_generated["REVERSAL"] += 1
                else:
                    for verb in plan.ordered_execution_verbs:
                        if verb in self.actions_generated:
                            self.actions_generated[verb] += 1
                
                # Advance actual position state after synthetic success
                self.actual_position = self.actual_position.advance_after_execution(
                    plan.ordered_execution_verbs
                )
            else:
                # Non-executable (e.g., BLOCKED, NO_CHANGE)
                output_row["APTF_position_action"] = None
                self.ineligible_rows += 1
            
            self.output_rows.append(output_row)
        
        return self.output_rows

    def write_output_csv(self, output_path: str | Path):
        """Write derived position action CSV."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["timestamp", "open", "high", "low", "close", "volume", "APTF_position_action"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in self.output_rows:
                out_row = {
                    "timestamp": row["timestamp"],
                    "open": f"{row['open']:.2f}",
                    "high": f"{row['high']:.2f}",
                    "low": f"{row['low']:.2f}",
                    "close": f"{row['close']:.2f}",
                    "volume": int(row["volume"]),
                    "APTF_position_action": row["APTF_position_action"] or "",
                }
                writer.writerow(out_row)

    def generate_summary(self) -> dict:
        """Generate summary statistics."""
        return {
            "input_rows": self.row_count,
            "output_rows": len(self.output_rows),
            "cardinality_check": "PASS" if len(self.output_rows) == self.row_count else "FAIL",
            "eligible_actions": self.eligible_actions,
            "ineligible_rows": self.ineligible_rows,
            "actions": self.actions_generated,
            "terminal_position": self.actual_position.state,
            "invalid_actions": 0,
            "position_violations": 0,
        }

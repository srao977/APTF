"""
APTF Real Pipeline - Small Integration Proof (First 100 Rows)
Tests that all real frozen components can be invoked successfully.
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "d01_adaptive_parametric_model" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "d02_return_shape" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "d04_trading_envelope" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "d03_decision_control" / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from real_causal_replay_harness_v0_2 import RealCausalReplayHarness


def main():
    root = Path(__file__).parent.parent
    source_csv = root / "data" / "market" / "normalized" / "SPY_1min_normalized_v0_1.csv"
    
    if not source_csv.exists():
        print(f"ERROR: Source not found: {source_csv}")
        return 1
    
    print("Starting small real-integration proof (100 rows)...")
    print()
    
    # Initialize with JUST 100 rows for proof
    harness = RealCausalReplayHarness(
        source_csv_path=source_csv,
        max_rows=100,
        entity_id="SPY",
        initial_position="LONG",
    )
    
    print("Processing 100 rows through real D01 -> D02 -> D04 -> D03 -> Controller...")
    result = harness.process_full_pipeline()
    
    summary = harness.generate_summary()
    
    print()
    print("=" * 80)
    print("SMALL INTEGRATION PROOF - RESULTS")
    print("=" * 80)
    print()
    print(f"Input rows processed:          {summary['input_rows']}")
    print(f"Output rows generated:         {summary['output_rows']}")
    print(f"Cardinality:                   {summary['cardinality_check']}")
    print()
    print("Real component invocations:")
    print(f"  D01:                         {summary['d01_valid_outputs']} valid outputs")
    print(f"  D02:                         {summary['d02_outputs']} outputs")
    print(f"  D04:                         {summary['d04_evaluations']} evaluations")
    print(f"  D03:                         {summary['d03_records']} records")
    print(f"  Controller:                  {summary['controller_invocations']} invocations")
    print()
    print("Output statistics:")
    print(f"  Desired position values:     {summary['desired_position_populated']}")
    print(f"  Desired position blank:      {summary['desired_position_blank']}")
    print(f"  Position actions:            {summary['action_populated']}")
    print(f"  Position actions blank:      {summary['action_blank']}")
    print()
    print("Zero-mock guarantee:")
    all_zero = all(v == 0 for v in summary['zero_mock_guarantee'].values())
    print(f"  All zero (no mocks):         {all_zero}")
    print()
    
    # CRITICAL GATES
    gate_1 = summary['d01_valid_outputs'] > 0
    gate_2 = summary['d03_records'] > 0
    gate_3 = all_zero
    
    print("=" * 80)
    print("CRITICAL GATES (for Phase 2 Go/No-Go)")
    print("=" * 80)
    print(f"Gate 1 - D01 invoked (valid outputs > 0):        {'PASS' if gate_1 else 'FAIL'}")
    print(f"Gate 2 - D03 invoked (records > 0):              {'PASS' if gate_2 else 'FAIL'}")
    print(f"Gate 3 - Zero-mock guarantee:                    {'PASS' if gate_3 else 'FAIL'}")
    print()
    
    if gate_1 and gate_2 and gate_3:
        print("STATUS: PROOF PASSED - Ready to proceed with Phase 2")
        return 0
    else:
        print("STATUS: PROOF FAILED - Cannot proceed")
        return 1


if __name__ == "__main__":
    import traceback
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"EXCEPTION: {e}")
        traceback.print_exc()
        raise SystemExit(1)

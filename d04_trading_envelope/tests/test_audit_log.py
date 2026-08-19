import json
from pathlib import Path

from aptf_d04.cli.main import run_single


ROOT = Path(__file__).resolve().parents[1]


def test_audit_log_json_and_monotonic_sequence() -> None:
    summary = run_single(ROOT, "02_shape_becomes_capturable", speed=0.0, verbose=False)
    path = Path(summary["audit_file"])
    assert path.exists()

    sequence = []
    first = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if first is None:
                first = row
            sequence.append(row["sequence_number"])

    assert sequence == sorted(sequence)
    assert len(sequence) > 0
    assert first is not None
    assert "base_capturability_score" in first
    assert "feasibility_gate_score" not in first
    assert "gate_dimension_values" not in first
    assert "capturability_score" in first

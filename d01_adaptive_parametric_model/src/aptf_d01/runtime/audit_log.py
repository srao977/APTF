from __future__ import annotations

from pathlib import Path
import json


class AuditLogger:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sequence = 0
        self.files = {
            "observations": output_dir / "observations.jsonl",
            "perturbations": output_dir / "perturbations.jsonl",
            "signals": output_dir / "signals.jsonl",
            "parameter_updates": output_dir / "parameter_updates.jsonl",
            "dmo": output_dir / "dmo.jsonl",
            "fmo": output_dir / "fmo.jsonl",
            "fmo_captures": output_dir / "fmo_captures.jsonl",
            "realized_outcomes": output_dir / "realized_outcomes.jsonl",
            "experiments": output_dir / "experiments.jsonl",
        }

    def write(self, stream: str, payload: dict) -> None:
        self.sequence += 1
        row = {
            "sequence_number": self.sequence,
            **payload,
        }
        path = self.files[stream]
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")

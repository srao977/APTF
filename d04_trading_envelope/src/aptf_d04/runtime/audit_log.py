from __future__ import annotations

import json
import time
from pathlib import Path

from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.envelope_state import EnvelopeEvaluation
from aptf_d04.models.return_shape import ReturnShape


class AuditLogger:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.sequence_number = 0

    def write(
        self,
        scenario_time: float,
        return_shape: ReturnShape,
        context: EnvelopeContext,
        evaluation: EnvelopeEvaluation,
    ) -> None:
        self.sequence_number += 1

        payload = {
            "sequence_number": self.sequence_number,
            "wall_clock_timestamp": time.time(),
            "scenario_time": scenario_time,
            "candidate_id": return_shape.candidate_id,
            "return_shape_id": return_shape.return_shape_id,
            "return_shape_version": return_shape.version,
            "return_shape": return_shape.model_dump(),
            "envelope_context": context.model_dump(),
            "shape_component": evaluation.shape_component,
            "envelope_component": evaluation.envelope_component,
            "lifetime_component": evaluation.lifetime_component,
            "base_capturability_score": evaluation.base_capturability_score,
            "feasibility_gate_score": evaluation.feasibility_gate_score,
            "capturability_score": evaluation.capturability_score,
            "gate_dimension_values": evaluation.gate_dimension_values,
            "previous_aperture": evaluation.previous_aperture,
            "new_aperture": evaluation.aperture,
            "previous_state": evaluation.previous_state.value,
            "new_state": evaluation.new_state.value,
            "position_open": evaluation.position_open,
            "entry_eligible": evaluation.entry_eligible,
            "continuation_signal": evaluation.continuation_signal.value,
            "events_emitted": [e.value for e in evaluation.events_emitted],
            "reason_codes": evaluation.reason_codes,
        }
        with self.output_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True) + "\n")

from __future__ import annotations

import json
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
            "scenario_time": scenario_time,
            "candidate_id": evaluation.candidate_envelope.candidate_id if evaluation.candidate_envelope else None,
            "return_shape_identity": [return_shape.entity_id, return_shape.model_time],
            "return_shape": return_shape.to_dict(),
            "envelope_context": context.model_dump(),
            "geometry_quality": evaluation.geometry_quality,
            "structural_quality": evaluation.structural_quality,
            "risk_quality": evaluation.risk_quality,
            "base_capturability_score": evaluation.base_capturability_score,
            "capturability_score": evaluation.capturability_score,
            "previous_aperture": evaluation.aperture_before,
            "new_aperture": evaluation.aperture_after,
            "previous_state": evaluation.previous_envelope_state.value,
            "new_state": evaluation.new_envelope_state.value,
            "events_emitted": [e.value for e in evaluation.events],
            "reason_codes": evaluation.reason_codes,
        }
        with self.output_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True) + "\n")

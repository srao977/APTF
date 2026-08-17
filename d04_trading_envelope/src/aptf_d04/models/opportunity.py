from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from d02.v02.models import PathDirection

from .enums import CandidateStatus


class CandidateEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    entity_id: str
    source_return_shape_model_time: float
    qualified_at: float
    status: CandidateStatus
    path_direction: PathDirection


OpportunityEvent = CandidateEnvelope

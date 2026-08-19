from __future__ import annotations

from urllib.parse import quote

from aptf_d04.envelope.aperture_model import ApertureModel
from aptf_d04.envelope.capturability_model import CapturabilityModel, InvalidReturnShapeError
from aptf_d04.envelope.hysteresis import HysteresisController
from aptf_d04.envelope.lifecycle import map_transition_event
from aptf_d04.models.capturability import CapturabilityResult
from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.envelope_state import EnvelopeEvaluation
from aptf_d04.models.enums import CandidateStatus, EnvelopeState, EventType, SafetyReason, SafetyState
from aptf_d04.models.opportunity import CandidateEnvelope
from d02.v02.models import ReturnShape

def candidate_identity(entity_id: str, source_model_time: float, qualified_at: float) -> str:
    encoded = quote(entity_id, safe="-._~", encoding="utf-8", errors="strict")
    return f"D04C|{encoded}|{format(source_model_time, '.17g')}|{format(qualified_at, '.17g')}"


class TradingEnvelope:
    def __init__(
        self,
        capturability_model: CapturabilityModel,
        aperture_model: ApertureModel,
        hysteresis: HysteresisController,
    ) -> None:
        self.capturability_model = capturability_model
        self.aperture_model = aperture_model
        self.hysteresis = hysteresis
        self.current_state = EnvelopeState.CLOSED
        self.current_aperture = 0.0
        self.current_entity_id: str | None = None
        self.current_model_time: float | None = None
        self.current_candidate: CandidateEnvelope | None = None

    def _invalidate_candidate(self) -> CandidateEnvelope | None:
        if self.current_candidate is None:
            return None
        invalidated = self.current_candidate.model_copy(update={"status": CandidateStatus.INVALIDATED})
        self.current_candidate = None
        return invalidated

    def _safety_reason(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
        invalid_return_shape: bool,
    ) -> SafetyReason | None:
        if invalid_return_shape:
            return SafetyReason.INVALID_RETURNSHAPE
        if context.evaluation_time > return_shape.model_time + return_shape.projection_interval:
            return SafetyReason.SHAPE_STALE
        if context.market_eligible is False:
            return SafetyReason.MARKET_INELIGIBLE
        return None

    def process(self, return_shape: ReturnShape, context: EnvelopeContext) -> EnvelopeEvaluation:
        previous_state = self.current_state
        previous_aperture = self.current_aperture
        events: list[EventType] = []
        reasons: list[str] = []
        candidate_for_output: CandidateEnvelope | None = None

        if self.current_entity_id is not None and return_shape.entity_id != self.current_entity_id:
            raise ValueError("TradingEnvelope instance is bound to one entity")
        is_new_shape = self.current_model_time is None or return_shape.model_time > self.current_model_time
        is_context_reevaluation = self.current_model_time is not None and return_shape.model_time == self.current_model_time
        if self.current_model_time is not None and return_shape.model_time < self.current_model_time:
            raise ValueError("ReturnShape model_time cannot move backward")

        if is_new_shape:
            if self.current_model_time is not None:
                events.append(EventType.SHAPE_SUPERSEDED)
                invalidated = self._invalidate_candidate()
                if invalidated is not None:
                    candidate_for_output = invalidated
                    events.append(EventType.CANDIDATE_INVALIDATED)
            self.current_entity_id = return_shape.entity_id
            self.current_model_time = return_shape.model_time
            events.append(EventType.RETURN_SHAPE_ACCEPTED)
        elif is_context_reevaluation:
            events.append(EventType.CONTEXT_REEVALUATED)

        invalid_return_shape = False
        try:
            capture = self.capturability_model.evaluate(return_shape, context)
        except InvalidReturnShapeError:
            invalid_return_shape = True
            capture = CapturabilityResult(
                hard_eligibility=0,
                geometry_quality=0.0,
                structural_quality=0.0,
                risk_quality=0.0,
                base_capturability_score=0.0,
                capturability_score=0.0,
                reason_codes=["INVALID_RETURNSHAPE"],
            )
        reasons.extend(capture.reason_codes)
        events.append(EventType.CAPTURABILITY_EVALUATED)
        safety_reason = self._safety_reason(return_shape, context, invalid_return_shape)

        if safety_reason is not None:
            self.current_state = EnvelopeState.CLOSED
            self.current_aperture = 0.0
            self.hysteresis.reset()
            invalidated = self._invalidate_candidate()
            if invalidated is not None:
                candidate_for_output = invalidated
                events.append(EventType.CANDIDATE_INVALIDATED)
            events.append(EventType[safety_reason.value])
            if previous_state != EnvelopeState.CLOSED:
                events.append(EventType.ENVELOPE_CLOSED)
        else:
            self.current_state, hysteresis_reasons = self.hysteresis.next_state(
                current_state=self.current_state,
                capturability_score=capture.capturability_score,
            )
            reasons.extend(hysteresis_reasons)
            self.current_aperture = self.aperture_model.update(
                capture.capturability_score,
                self.current_state,
                self.current_aperture,
            )
            transition = map_transition_event(previous_state, self.current_state)
            if transition:
                events.append(EventType[transition])
            if self.current_state == EnvelopeState.OPEN and self.current_candidate is None:
                self.current_candidate = CandidateEnvelope(
                    candidate_id=candidate_identity(return_shape.entity_id, return_shape.model_time, context.evaluation_time),
                    entity_id=return_shape.entity_id,
                    source_return_shape_model_time=return_shape.model_time,
                    qualified_at=context.evaluation_time,
                    status=CandidateStatus.QUALIFIED,
                    path_direction=return_shape.path_direction,
                )
                events.append(EventType.CANDIDATE_QUALIFIED)
            candidate_for_output = self.current_candidate

        events.append(EventType.APERTURE_UPDATED)
        projection_valid = context.evaluation_time <= return_shape.model_time + return_shape.projection_interval
        return EnvelopeEvaluation(
            evaluation_time=context.evaluation_time,
            entity_id=return_shape.entity_id,
            return_shape_model_time=return_shape.model_time,
            source_model_version=return_shape.source_model_version,
            hard_eligibility=capture.hard_eligibility,
            geometry_quality=capture.geometry_quality,
            structural_quality=capture.structural_quality,
            risk_quality=capture.risk_quality,
            base_capturability_score=capture.base_capturability_score,
            capturability_score=capture.capturability_score,
            previous_envelope_state=previous_state,
            new_envelope_state=self.current_state,
            aperture_before=previous_aperture,
            aperture_after=self.current_aperture,
            projection_valid=projection_valid,
            stale=not projection_valid,
            safety_state=SafetyState.CLEAR if safety_reason is None else SafetyState.SAFETY_CLOSED,
            safety_reason=safety_reason,
            candidate_envelope=candidate_for_output,
            reason_codes=sorted(set(reasons)),
            events=events,
        )

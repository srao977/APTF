from __future__ import annotations

from dataclasses import dataclass

from aptf_d04.envelope.aperture_model import ApertureModel
from aptf_d04.envelope.capturability_model import CapturabilityModel
from aptf_d04.envelope.hysteresis import HysteresisController
from aptf_d04.envelope.lifecycle import continuation_signal_for_state, map_transition_event
from aptf_d04.models.capturability import CapturabilityResult
from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.envelope_state import EnvelopeEvaluation, EnvelopeTransitionEvent
from aptf_d04.models.enums import ContinuationSignal, EnvelopeState, EventType
from aptf_d04.models.opportunity import OpportunityEvent
from aptf_d04.models.return_shape import ReturnShape


@dataclass
class SafetyConfig:
    critical_data_integrity_threshold: float
    auto_open_position_on_qualified_opportunity: bool


class TradingEnvelope:
    def __init__(
        self,
        capturability_model: CapturabilityModel,
        aperture_model: ApertureModel,
        hysteresis: HysteresisController,
        safety_config: SafetyConfig,
    ) -> None:
        self.capturability_model = capturability_model
        self.aperture_model = aperture_model
        self.hysteresis = hysteresis
        self.safety_config = safety_config

        self.current_state = EnvelopeState.CLOSED
        self.current_aperture = 0.0
        self.position_open = False
        self.last_shape_id: str | None = None
        self.last_shape_version: int = 0

    def _safety_override_reason(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
    ) -> str | None:
        if not context.market_eligible:
            return "MARKET_INELIGIBLE"
        if context.data_integrity <= self.safety_config.critical_data_integrity_threshold:
            return "DATA_INVALID"
        if not return_shape.active or return_shape.expected_lifetime_seconds <= 0:
            return "SHAPE_EXPIRED"
        return None

    def _forced_closed_result(self, reason: str) -> CapturabilityResult:
        return CapturabilityResult(
            shape_component=0.0,
            envelope_component=0.0,
            lifetime_component=0.0,
            base_capturability_score=0.0,
            feasibility_gate_score=0.0,
            capturability_score=0.0,
            gate_dimension_values={},
            reason_codes=[reason],
        )

    def process(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
    ) -> EnvelopeEvaluation:
        previous_state = self.current_state
        previous_aperture = self.current_aperture

        if self.last_shape_id is not None and self.last_shape_id == return_shape.return_shape_id:
            if return_shape.version <= self.last_shape_version:
                raise ValueError("ReturnShape version must increase for same return_shape_id")
        self.last_shape_id = return_shape.return_shape_id
        self.last_shape_version = return_shape.version

        reason_codes: list[str] = []
        events_emitted: list[EventType] = [
            EventType.RETURN_SHAPE_UPDATED,
            EventType.ENVELOPE_CONTEXT_UPDATED,
        ]

        safety_reason = self._safety_override_reason(return_shape, context)
        if safety_reason:
            capture = self._forced_closed_result(safety_reason)
            reason_codes.extend(capture.reason_codes)
            self.current_state = EnvelopeState.CLOSED
            self.hysteresis.reset()
            self.current_aperture = self.aperture_model.update(0.0, self.current_state, self.current_aperture)
            events_emitted.extend([EventType.CAPTURABILITY_EVALUATED, EventType.APERTURE_UPDATED, EventType[safety_reason]])
        else:
            capture = self.capturability_model.evaluate(return_shape, context)
            reason_codes.extend(capture.reason_codes)
            events_emitted.extend([EventType.CAPTURABILITY_EVALUATED])

            self.current_state, hysteresis_reasons = self.hysteresis.next_state(
                current_state=self.current_state,
                capturability_score=capture.capturability_score,
            )
            reason_codes.extend(hysteresis_reasons)

            self.current_aperture = self.aperture_model.update(
                capturability_score=capture.capturability_score,
                current_state=self.current_state,
                prior_aperture=self.current_aperture,
            )
            events_emitted.append(EventType.APERTURE_UPDATED)

        transition_name = map_transition_event(previous_state, self.current_state)
        transition_event = None
        if transition_name:
            t_event_type = EventType[transition_name]
            transition_event = EnvelopeTransitionEvent(
                event_type=t_event_type,
                timestamp=return_shape.timestamp,
            )
            events_emitted.append(t_event_type)

        entry_eligible = (
            self.current_state == EnvelopeState.OPEN
            and return_shape.active
            and context.market_eligible
        )

        opportunity_event = None
        should_emit_opportunity = (
            entry_eligible
            and previous_state != EnvelopeState.OPEN
            and not self.position_open
        )
        if should_emit_opportunity:
            events_emitted.append(EventType.QUALIFIED_OPPORTUNITY)
            opportunity_event = OpportunityEvent(
                event_type=EventType.QUALIFIED_OPPORTUNITY,
                candidate_id=return_shape.candidate_id,
                return_shape_id=return_shape.return_shape_id,
                timestamp=return_shape.timestamp,
                reason_codes=reason_codes.copy(),
            )
            if self.safety_config.auto_open_position_on_qualified_opportunity:
                self.position_open = True

        continuation_signal = continuation_signal_for_state(
            position_open=self.position_open,
            previous_state=previous_state,
            new_state=self.current_state,
        )

        if continuation_signal == ContinuationSignal.HOLD_ELIGIBLE:
            events_emitted.append(EventType.HOLD_ELIGIBLE)
        elif continuation_signal == ContinuationSignal.REDUCE_CANDIDATE:
            events_emitted.append(EventType.REDUCE_CANDIDATE)
        elif continuation_signal == ContinuationSignal.MODIFY_CANDIDATE:
            events_emitted.append(EventType.MODIFY_CANDIDATE)
        elif continuation_signal == ContinuationSignal.EXIT_CANDIDATE:
            events_emitted.append(EventType.EXIT_CANDIDATE)
            self.position_open = False

        return EnvelopeEvaluation(
            timestamp=return_shape.timestamp,
            return_shape_id=return_shape.return_shape_id,
            candidate_id=return_shape.candidate_id,
            return_shape_version=return_shape.version,
            previous_state=previous_state,
            new_state=self.current_state,
            shape_quality=return_shape.shape_quality,
            shape_component=capture.shape_component,
            envelope_component=capture.envelope_component,
            lifetime_component=capture.lifetime_component,
            base_capturability_score=capture.base_capturability_score,
            feasibility_gate_score=capture.feasibility_gate_score,
            capturability_score=capture.capturability_score,
            gate_dimension_values=capture.gate_dimension_values,
            previous_aperture=previous_aperture,
            aperture=self.current_aperture,
            position_open=self.position_open,
            entry_eligible=entry_eligible,
            continuation_signal=continuation_signal,
            reason_codes=sorted(set(reason_codes)),
            events_emitted=events_emitted,
            state_transition_event=transition_event,
            opportunity_event=opportunity_event,
        )

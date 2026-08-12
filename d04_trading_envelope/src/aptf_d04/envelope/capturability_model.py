from __future__ import annotations

from abc import ABC, abstractmethod

from aptf_d04.models.capturability import CapturabilityResult
from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.return_shape import ReturnShape


class CapturabilityModel(ABC):
    @abstractmethod
    def evaluate(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
    ) -> CapturabilityResult:
        raise NotImplementedError


class CapturabilityModelV0(CapturabilityModel):
    """Deterministic and transparent placeholder model for v0.1."""

    def __init__(
        self,
        shape_weights: dict[str, float],
        envelope_weights: dict[str, float],
        target_lifetime_seconds: float,
    ) -> None:
        self.shape_weights = shape_weights
        self.envelope_weights = envelope_weights
        self.target_lifetime_seconds = max(target_lifetime_seconds, 1.0)
        self._validate_weights(self.shape_weights)
        self._validate_weights(self.envelope_weights)

    @staticmethod
    def _shape_values(return_shape: ReturnShape) -> dict[str, float]:
        return {
            "shape_quality": return_shape.shape_quality,
            "forward_support": return_shape.forward_support,
            "magnitude_score": return_shape.magnitude_score,
            "persistence_score": return_shape.persistence_score,
            "inv_uncertainty": 1.0 - return_shape.uncertainty,
            "inv_reversal_risk": 1.0 - return_shape.reversal_risk,
            "inv_decay_score": 1.0 - return_shape.decay_score,
        }

    @staticmethod
    def _envelope_values(context: EnvelopeContext) -> dict[str, float]:
        return {
            "data_integrity": context.data_integrity,
            "clock_event_quality": context.clock_event_quality,
            "capital_available": context.capital_available,
            "portfolio_capacity": context.portfolio_capacity,
            "position_capacity": context.position_capacity,
            "liquidity_quality": context.liquidity_quality,
            "spread_quality": context.spread_quality,
            "latency_quality": context.latency_quality,
            "execution_feasibility": context.execution_feasibility,
            "risk_capacity": context.risk_capacity,
            "broker_health": context.broker_health,
        }

    def _common_reason_codes(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
        reason_codes: list[str],
    ) -> None:
        if return_shape.shape_quality < 0.5:
            reason_codes.append("SHAPE_QUALITY_LOW")
        if return_shape.forward_support < 0.5:
            reason_codes.append("FORWARD_SUPPORT_LOW")
        if return_shape.uncertainty > 0.5:
            reason_codes.append("UNCERTAINTY_HIGH")
        if return_shape.reversal_risk > 0.5:
            reason_codes.append("REVERSAL_RISK_HIGH")
        if return_shape.expected_lifetime_seconds < self.target_lifetime_seconds * 0.25:
            reason_codes.append("LIFETIME_SHORT")
        if context.data_integrity < 0.5:
            reason_codes.append("DATA_INTEGRITY_LOW")
        if context.capital_available < 0.4:
            reason_codes.append("CAPITAL_LOW")
        if context.portfolio_capacity < 0.4:
            reason_codes.append("PORTFOLIO_CAPACITY_LOW")
        if context.liquidity_quality < 0.5:
            reason_codes.append("LIQUIDITY_LOW")
        if context.spread_quality < 0.5:
            reason_codes.append("SPREAD_POOR")
        if context.latency_quality < 0.5:
            reason_codes.append("LATENCY_POOR")
        if context.execution_feasibility < 0.5:
            reason_codes.append("EXECUTION_FEASIBILITY_LOW")
        if context.risk_capacity < 0.4:
            reason_codes.append("RISK_CAPACITY_LOW")
        if context.broker_health < 0.5:
            reason_codes.append("BROKER_HEALTH_LOW")

    @staticmethod
    def _validate_weights(weights: dict[str, float]) -> None:
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0; got {total:.6f}")

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def evaluate(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
    ) -> CapturabilityResult:
        reason_codes: list[str] = []

        if not return_shape.active or return_shape.expected_lifetime_seconds <= 0:
            reason_codes.append("SHAPE_EXPIRED")
            return CapturabilityResult(
                shape_component=0.0,
                envelope_component=0.0,
                lifetime_component=0.0,
                base_capturability_score=0.0,
                feasibility_gate_score=0.0,
                capturability_score=0.0,
                gate_dimension_values={},
                reason_codes=reason_codes,
            )

        if not context.market_eligible:
            reason_codes.append("MARKET_INELIGIBLE")
            return CapturabilityResult(
                shape_component=0.0,
                envelope_component=0.0,
                lifetime_component=0.0,
                base_capturability_score=0.0,
                feasibility_gate_score=0.0,
                capturability_score=0.0,
                gate_dimension_values={},
                reason_codes=reason_codes,
            )

        shape_values = self._shape_values(return_shape)
        envelope_values = self._envelope_values(context)

        shape_component = self._clamp(
            sum(shape_values[name] * w for name, w in self.shape_weights.items())
        )
        envelope_component = self._clamp(
            sum(envelope_values[name] * w for name, w in self.envelope_weights.items())
        )
        lifetime_component = self._clamp(
            return_shape.expected_lifetime_seconds / self.target_lifetime_seconds
        )

        capturability_score = self._clamp(
            (0.5 * shape_component + 0.5 * envelope_component) * lifetime_component
        )

        self._common_reason_codes(return_shape, context, reason_codes)

        return CapturabilityResult(
            shape_component=shape_component,
            envelope_component=envelope_component,
            lifetime_component=lifetime_component,
            base_capturability_score=capturability_score,
            feasibility_gate_score=1.0,
            capturability_score=capturability_score,
            gate_dimension_values={},
            reason_codes=reason_codes,
        )


class CapturabilityModelV0_2(CapturabilityModelV0):
    """Experimental v0.2 model: base score multiplied by feasibility gate."""

    GATE_REASON_CODE_MAP = {
        "liquidity_quality": "GATE_LIQUIDITY_LOW",
        "spread_quality": "GATE_SPREAD_LOW",
        "latency_quality": "GATE_LATENCY_LOW",
        "execution_feasibility": "GATE_EXECUTION_LOW",
        "capital_available": "GATE_CAPITAL_LOW",
        "portfolio_capacity": "GATE_PORTFOLIO_LOW",
        "position_capacity": "GATE_POSITION_CAPACITY_LOW",
        "risk_capacity": "GATE_RISK_LOW",
        "broker_health": "GATE_BROKER_HEALTH_LOW",
        "data_integrity": "GATE_DATA_INTEGRITY_LOW",
    }

    def __init__(
        self,
        shape_weights: dict[str, float],
        envelope_weights: dict[str, float],
        target_lifetime_seconds: float,
        feasibility_gate_mode: str,
        feasibility_gate_dimensions: list[str],
        gate_warning_threshold: float,
    ) -> None:
        super().__init__(shape_weights, envelope_weights, target_lifetime_seconds)
        if feasibility_gate_mode != "minimum":
            raise ValueError("Only minimum feasibility gate mode is supported in V0_2")
        if not feasibility_gate_dimensions:
            raise ValueError("feasibility_gate_dimensions cannot be empty")
        self.feasibility_gate_mode = feasibility_gate_mode
        self.feasibility_gate_dimensions = feasibility_gate_dimensions
        self.gate_warning_threshold = self._clamp(gate_warning_threshold)

    def evaluate(
        self,
        return_shape: ReturnShape,
        context: EnvelopeContext,
    ) -> CapturabilityResult:
        reason_codes: list[str] = []

        if not return_shape.active or return_shape.expected_lifetime_seconds <= 0:
            reason_codes.append("SHAPE_EXPIRED")
            return CapturabilityResult(
                shape_component=0.0,
                envelope_component=0.0,
                lifetime_component=0.0,
                base_capturability_score=0.0,
                feasibility_gate_score=0.0,
                capturability_score=0.0,
                gate_dimension_values={},
                reason_codes=reason_codes,
            )

        if not context.market_eligible:
            reason_codes.append("MARKET_INELIGIBLE")
            return CapturabilityResult(
                shape_component=0.0,
                envelope_component=0.0,
                lifetime_component=0.0,
                base_capturability_score=0.0,
                feasibility_gate_score=0.0,
                capturability_score=0.0,
                gate_dimension_values={},
                reason_codes=reason_codes,
            )

        shape_values = self._shape_values(return_shape)
        envelope_values = self._envelope_values(context)

        shape_component = self._clamp(
            sum(shape_values[name] * w for name, w in self.shape_weights.items())
        )
        envelope_component = self._clamp(
            sum(envelope_values[name] * w for name, w in self.envelope_weights.items())
        )
        lifetime_component = self._clamp(
            return_shape.expected_lifetime_seconds / self.target_lifetime_seconds
        )

        base_score = self._clamp(
            (0.5 * shape_component + 0.5 * envelope_component) * lifetime_component
        )

        gate_values: dict[str, float] = {}
        for dim in self.feasibility_gate_dimensions:
            value = getattr(context, dim)
            gate_values[dim] = self._clamp(value)

        feasibility_gate_score = self._clamp(min(gate_values.values()))
        final_score = self._clamp(base_score * feasibility_gate_score)

        self._common_reason_codes(return_shape, context, reason_codes)
        if feasibility_gate_score < self.gate_warning_threshold:
            reason_codes.append("FEASIBILITY_GATE_LOW")
        for dim, value in gate_values.items():
            if value < self.gate_warning_threshold and dim in self.GATE_REASON_CODE_MAP:
                reason_codes.append(self.GATE_REASON_CODE_MAP[dim])

        return CapturabilityResult(
            shape_component=shape_component,
            envelope_component=envelope_component,
            lifetime_component=lifetime_component,
            base_capturability_score=base_score,
            feasibility_gate_score=feasibility_gate_score,
            capturability_score=final_score,
            gate_dimension_values=gate_values,
            reason_codes=reason_codes,
        )

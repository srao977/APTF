from __future__ import annotations

from abc import ABC, abstractmethod
import math

from aptf_d04.models.capturability import CapturabilityResult
from aptf_d04.models.envelope_context import EnvelopeContext
from d02.v02.models import PathDirection, ReturnShape


class InvalidReturnShapeError(ValueError):
    pass


class CapturabilityModel(ABC):
    @abstractmethod
    def evaluate(self, return_shape: ReturnShape, context: EnvelopeContext) -> CapturabilityResult:
        raise NotImplementedError


class CapturabilityModelV0_2(CapturabilityModel):
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
        feasibility_gate_dimensions: list[str],
        gate_warning_threshold: float,
        critical_data_integrity_threshold: float,
    ) -> None:
        if feasibility_gate_dimensions != list(self.GATE_REASON_CODE_MAP):
            raise ValueError("feasibility gate dimensions must match the frozen ten-field order")
        if not 0.0 <= gate_warning_threshold <= 1.0:
            raise ValueError("gate_warning_threshold must be in [0,1]")
        if not 0.0 <= critical_data_integrity_threshold <= 1.0:
            raise ValueError("critical_data_integrity_threshold must be in [0,1]")
        self.feasibility_gate_dimensions = tuple(feasibility_gate_dimensions)
        self.gate_warning_threshold = gate_warning_threshold
        self.critical_data_integrity_threshold = critical_data_integrity_threshold

    @staticmethod
    def validate_return_shape(return_shape: ReturnShape) -> None:
        terminal = return_shape.forward_samples[-1].level - return_shape.current_level
        maximum = max(
            abs(sample.level - return_shape.current_level)
            for sample in return_shape.forward_samples
        )
        if return_shape.terminal_displacement > 0.0:
            direction = PathDirection.UPWARD
        elif return_shape.terminal_displacement < 0.0:
            direction = PathDirection.DOWNWARD
        else:
            direction = PathDirection.FLAT
        if (
            abs(return_shape.terminal_displacement) > return_shape.maximum_absolute_displacement
            or return_shape.terminal_displacement != terminal
            or return_shape.maximum_absolute_displacement != maximum
            or return_shape.path_direction != direction
        ):
            raise InvalidReturnShapeError("INVALID_RETURNSHAPE")

    @staticmethod
    def geometry_quality(return_shape: ReturnShape) -> float:
        maximum = return_shape.maximum_absolute_displacement
        if maximum == 0.0:
            return 0.0
        return abs(return_shape.terminal_displacement) / maximum

    @staticmethod
    def structural_quality(return_shape: ReturnShape) -> float:
        return (return_shape.strength * return_shape.coherence * return_shape.persistence) ** (1.0 / 3.0)

    @staticmethod
    def risk_quality(return_shape: ReturnShape) -> float:
        return math.sqrt((1.0 - return_shape.uncertainty) * (1.0 - return_shape.reversal_propensity))

    def evaluate(self, return_shape: ReturnShape, context: EnvelopeContext) -> CapturabilityResult:
        self.validate_return_shape(return_shape)
        geometry = self.geometry_quality(return_shape)
        structural = self.structural_quality(return_shape)
        risk = self.risk_quality(return_shape)
        base = geometry * structural * risk
        gate_values = {name: getattr(context, name) for name in self.feasibility_gate_dimensions}
        gate = min(gate_values.values())
        projection_valid = context.evaluation_time <= return_shape.model_time + return_shape.projection_interval
        hard_eligibility = int(
            projection_valid
            and context.market_eligible
            and context.data_integrity > self.critical_data_integrity_threshold
        )
        final = hard_eligibility * base * gate

        reasons: list[str] = []
        if return_shape.maximum_absolute_displacement == 0.0:
            reasons.append("ZERO_GEOMETRY")
        if return_shape.uncertainty > 0.5:
            reasons.append("UNCERTAINTY_HIGH")
        if return_shape.reversal_propensity > 0.5:
            reasons.append("REVERSAL_PROPENSITY_HIGH")
        if gate < self.gate_warning_threshold:
            reasons.append("FEASIBILITY_GATE_LOW")
        for name, value in gate_values.items():
            if value < self.gate_warning_threshold:
                reasons.append(self.GATE_REASON_CODE_MAP[name])
        if not projection_valid:
            reasons.append("SHAPE_STALE")
        if not context.market_eligible:
            reasons.append("MARKET_INELIGIBLE")
        if context.data_integrity <= self.critical_data_integrity_threshold:
            reasons.append("DATA_INVALID")

        return CapturabilityResult(
            hard_eligibility=hard_eligibility,
            geometry_quality=geometry,
            structural_quality=structural,
            risk_quality=risk,
            base_capturability_score=base,
            feasibility_gate_score=gate,
            capturability_score=final,
            gate_dimension_values=gate_values,
            reason_codes=sorted(set(reasons)),
        )


CapturabilityModelV0 = CapturabilityModelV0_2

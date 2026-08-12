import pytest
from pydantic import ValidationError

from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_d04.models.enums import Direction
from aptf_d04.models.return_shape import ReturnShape


def test_return_shape_validation() -> None:
    with pytest.raises(ValidationError):
        ReturnShape(
            return_shape_id="RS-1",
            candidate_id="C1",
            version=1,
            timestamp=0.0,
            direction=Direction.LONG,
            shape_quality=1.2,
            forward_support=0.5,
            uncertainty=0.2,
            expected_lifetime_seconds=10,
            candidate_rr=1.5,
            magnitude_score=0.5,
            persistence_score=0.5,
            decay_score=0.2,
            reversal_risk=0.2,
            active=True,
            metadata={},
        )


def test_envelope_context_validation() -> None:
    with pytest.raises(ValidationError):
        EnvelopeContext(
            timestamp=0.0,
            market_eligible=True,
            data_integrity=0.8,
            clock_event_quality=0.8,
            capital_available=0.8,
            portfolio_capacity=0.8,
            position_capacity=0.8,
            liquidity_quality=0.8,
            spread_quality=1.2,
            latency_quality=0.8,
            execution_feasibility=0.8,
            risk_capacity=0.8,
            broker_health=0.8,
            metadata={},
        )

from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator
from aptf_d04.models.envelope_context import EnvelopeContext
from d02.v02.models import ReturnShape


ROOT = Path(__file__).resolve().parents[1]


def test_return_shape_validation() -> None:
    observation = SyntheticGenerator(
        load_scenario(ROOT / "scenarios" / "02_shape_becomes_capturable.yaml")
    ).generate()[0]
    assert isinstance(observation.return_shape, ReturnShape)
    with pytest.raises(ValueError, match="strength must be in"):
        replace(observation.return_shape, strength=1.2)


def test_envelope_context_validation() -> None:
    with pytest.raises(ValidationError):
        EnvelopeContext(
            evaluation_time=0.0,
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
        )

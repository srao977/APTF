from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import math

import pytest

from d01.v02.outputs import FMOSample
from d02.v02 import PathDirection, build_return_shape
from helpers import make_dmo, make_fmo, sample


CANONICAL_FIELDS = (
    "model_time", "entity_id", "source_model_version", "current_level",
    "projection_interval", "forward_half_life", "forward_samples",
    "terminal_displacement", "maximum_absolute_displacement", "path_direction",
    "terminal_decay_factor", "strength", "coherence", "persistence",
    "uncertainty", "reversal_propensity", "state_support_ratio",
)


def test_exact_17_field_schema_and_immutability() -> None:
    result = build_return_shape(make_dmo(), make_fmo())
    assert tuple(field.name for field in fields(result)) == CANONICAL_FIELDS
    with pytest.raises(FrozenInstanceError):
        result.model_time = 101.0


@pytest.mark.parametrize(
    ("levels", "direction", "terminal"),
    [
        ((1.1, 1.2, 1.3), PathDirection.UPWARD, 0.3),
        ((0.9, 0.8, 0.7), PathDirection.DOWNWARD, -0.3),
        ((1.0, 1.0, 1.0), PathDirection.FLAT, 0.0),
    ],
)
def test_terminal_displacement_and_exact_direction(levels, direction, terminal) -> None:
    result = build_return_shape(make_dmo(), make_fmo(levels))
    assert result.terminal_displacement == pytest.approx(terminal)
    assert result.path_direction is direction


@pytest.mark.parametrize(
    ("levels", "expected"),
    [
        ((1.1, 1.2, 1.3), 0.3),
        ((0.9, 0.8, 0.7), 0.3),
        ((1.5, 0.75, 1.2), 0.5),
        ((1.0, 1.0, 1.0), 0.0),
        ((1.3, 1.2, 1.3), 0.3),
    ],
)
def test_maximum_absolute_displacement(levels, expected) -> None:
    result = build_return_shape(make_dmo(), make_fmo(levels))
    assert result.maximum_absolute_displacement == pytest.approx(expected)
    assert abs(result.terminal_displacement) <= result.maximum_absolute_displacement


def test_terminal_decay_factor() -> None:
    result = build_return_shape(make_dmo(forward_half_life=60.0), make_fmo())
    assert result.terminal_decay_factor == pytest.approx(2.0 ** (-30.0 / 60.0))
    assert 0.0 < result.terminal_decay_factor < 1.0


def test_identity_and_d01_state_are_copied_exactly() -> None:
    dmo = make_dmo(
        model_time=42.0, entity_id="ENTITY:X", state_level=-2.5, strength=0.11,
        coherence=0.22, persistence=0.33, uncertainty=0.44,
        reversal_propensity=0.55, state_support_ratio=12.5,
    )
    fmo = make_fmo(model_time=42.0, entity_id="ENTITY:X")
    result = build_return_shape(dmo, fmo)
    assert (result.model_time, result.entity_id, result.source_model_version) == (42.0, "ENTITY:X", "0.2")
    assert result.current_level == -2.5
    assert (result.strength, result.coherence, result.persistence) == (0.11, 0.22, 0.33)
    assert (result.uncertainty, result.reversal_propensity, result.state_support_ratio) == (0.44, 0.55, 12.5)


def test_full_fmo_is_copied_without_reordering_or_value_change() -> None:
    fmo = make_fmo()
    result = build_return_shape(make_dmo(), fmo)
    assert len(result.forward_samples) == len(fmo.samples)
    for source, output in zip(fmo.samples, result.forward_samples):
        assert output.tau == source.tau
        assert output.level == source.level
        assert output.velocity == source.velocity
        assert output.uncertainty == source.uncertainty
        assert output.strength == source.strength
        assert output.persistence == source.persistence
        assert output.reversal_propensity == source.reversal_propensity


@pytest.mark.parametrize(
    "dmo,fmo,error",
    [
        (make_dmo(), make_fmo(model_time=101.0), "model_time"),
        (make_dmo(), make_fmo(entity_id="OTHER"), "entity_id"),
        (make_dmo(model_version="0.1"), make_fmo(), "model_version"),
        (make_dmo(strength=math.nan), make_fmo(), "strength"),
        (make_dmo(state_support_ratio=-1.0), make_fmo(), "state_support_ratio"),
        (make_dmo(), make_fmo(samples=[]), "non-empty"),
        (make_dmo(), make_fmo(samples=[sample(10.0, 1.1), sample(10.0, 1.2)]), "strictly increasing"),
        (make_dmo(), make_fmo(samples=[sample(10.0, 1.1)], interval_length=20.0), "terminal"),
    ],
)
def test_invalid_input_fails_deterministically(dmo, fmo, error) -> None:
    with pytest.raises(ValueError, match=error):
        build_return_shape(dmo, fmo)


def test_serialization_is_stable_and_complete() -> None:
    first = build_return_shape(make_dmo(), make_fmo()).to_dict()
    second = build_return_shape(make_dmo(), make_fmo()).to_dict()
    assert first == second
    assert tuple(first) == CANONICAL_FIELDS
    assert first["path_direction"] == "UPWARD"
    assert isinstance(first["forward_samples"], list)
from pathlib import Path

import pytest

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml


def _build_v011_model() -> AdaptiveParametricModel:
    root = Path(__file__).resolve().parents[1]
    cfg_default = _load_yaml(root / "config" / "default_v0_1_1.yaml")
    exp_cfg = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]
    return AdaptiveParametricModel(_build_model_cfg(cfg_default, exp_cfg))


def test_isolated_reset_drops_derivative_continuity_state() -> None:
    root = Path(__file__).resolve().parents[1]
    model = _build_v011_model()

    s1 = SyntheticProvider(root / "synthetic" / "quiet_market.yaml").stream()[:3]
    for obs in s1:
        model.step(obs, obs.model_available_timestamp)

    model.reset_observation_continuity_state()
    s2_first = SyntheticProvider(root / "synthetic" / "volume_shock.yaml").stream()[0]
    dmo, _fmo, _ = model.step(s2_first, s2_first.model_available_timestamp)
    assert dmo.input_channel_snapshot.get("raw_price_velocity", 0.0) == 0.0
    assert dmo.input_channel_snapshot.get("raw_price_acceleration", 0.0) == 0.0


def test_dt_non_positive_raises_invalid_temporal_order() -> None:
    root = Path(__file__).resolve().parents[1]
    model = _build_v011_model()
    obs = SyntheticProvider(root / "synthetic" / "quiet_market.yaml").stream()[0]
    model.step(obs, obs.model_available_timestamp)
    bad = obs.model_copy(update={"event_id": "E-BAD", "source_sequence": obs.source_sequence + 1})
    with pytest.raises(ValueError, match="INVALID_TEMPORAL_ORDER"):
        model.step(bad, bad.model_available_timestamp)

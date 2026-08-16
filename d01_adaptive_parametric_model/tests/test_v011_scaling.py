from pathlib import Path

from aptf_d01.conditioning.feature_scaler import FeatureScalerConfig, RunningZScoreFeatureScaler
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.providers.synthetic_provider import SyntheticProvider


def test_scaler_uses_prior_state_then_updates() -> None:
    scaler = RunningZScoreFeatureScaler(
        FeatureScalerConfig(minimum_warmup_observations=1, epsilon=1e-6, lower_bound=-8.0, upper_bound=8.0)
    )
    c1 = scaler.transform_then_update("x", 10.0, "units", 1.0)
    # Warmup emits deterministic zero model value.
    assert c1.model_value == 0.0
    c2 = scaler.transform_then_update("x", 10.0, "units", 2.0)
    # Prior mean was exactly 10 after first update, so z should be 0.
    assert c2.model_value == 0.0


def test_scaler_bound_hit_logged() -> None:
    scaler = RunningZScoreFeatureScaler(
        FeatureScalerConfig(minimum_warmup_observations=0, epsilon=1e-6, lower_bound=-1.0, upper_bound=1.0)
    )
    c = scaler.transform_then_update("x", 1000.0, "units", 1.0)
    assert c.bound_hit is True
    assert c.model_value == 1.0


def test_model_preserves_raw_and_conditioned_views() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg_default = _load_yaml(root / "config" / "default_v0_1_1.yaml")
    exp_cfg = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]
    model = AdaptiveParametricModel(_build_model_cfg(cfg_default, exp_cfg))
    obs = SyntheticProvider(root / "synthetic" / "quiet_market.yaml").stream()[0]
    dmo, _fmo, _ = model.step(obs, obs.model_available_timestamp)
    assert any(k.startswith("raw_") for k in dmo.input_channel_snapshot)
    assert any(k.startswith("model_") for k in dmo.input_channel_snapshot)

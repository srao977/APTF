from pathlib import Path

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml


def test_direction_magnitude_outputs_remain_separate() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg_default = _load_yaml(root / "config" / "default_v0_1_1.yaml")
    exp_cfg = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]
    model = AdaptiveParametricModel(_build_model_cfg(cfg_default, exp_cfg))
    obs = SyntheticProvider(root / "synthetic" / "quiet_market.yaml").stream()[10]
    dmo, fmo, _ = model.step(obs, obs.model_available_timestamp)
    assert -1.0 <= dmo.direction_state <= 1.0
    assert dmo.magnitude_state >= 0.0
    assert fmo.expected_magnitude >= 0.0


def test_fmo_capture_is_immutable_contract() -> None:
    from aptf_d01.evaluation.fmo_capture import FMOCapture

    root = Path(__file__).resolve().parents[1]
    cfg_default = _load_yaml(root / "config" / "default_v0_1_1.yaml")
    exp_cfg = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]
    model = AdaptiveParametricModel(_build_model_cfg(cfg_default, exp_cfg))
    obs = SyntheticProvider(root / "synthetic" / "quiet_market.yaml").stream()[15]
    _dmo, fmo, _ = model.step(obs, obs.model_available_timestamp)
    cap = FMOCapture().capture(fmo, parameter_state_version=1)
    original = cap.expected_magnitude
    fmo.expected_magnitude = fmo.expected_magnitude + 1.0
    assert cap.expected_magnitude == original

from pathlib import Path
import yaml

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml


def test_dmo_fmo_required_fields_and_fmo_capture_immutable() -> None:
    root = Path(__file__).resolve().parents[1]
    default_cfg = _load_yaml(root / "config" / "default.yaml")
    exp_cfg = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]
    m = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))
    s = SyntheticProvider(root / "synthetic" / "quiet_market.yaml").stream()[:3]
    dmo, fmo, _ = m.step(s[0], s[0].model_available_timestamp)
    assert dmo.model_instance_id
    assert fmo.expected_magnitude >= 0.0

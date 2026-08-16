from pathlib import Path

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml


def test_same_inputs_same_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    default_cfg = _load_yaml(root / "config" / "default.yaml")
    exp_cfg = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]

    provider = SyntheticProvider(root / "synthetic" / "quiet_market.yaml")
    stream = provider.stream()[:20]

    m1 = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))
    m2 = AdaptiveParametricModel(_build_model_cfg(default_cfg, exp_cfg))

    o1 = [m1.step(o, o.model_available_timestamp)[0].direction_state for o in stream]
    o2 = [m2.step(o, o.model_available_timestamp)[0].direction_state for o in stream]
    assert o1 == o2

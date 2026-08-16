import numpy as np

from aptf_d01.parametric.multi_output_model import MultiOutputConfig, MultiOutputModel


def test_mimo_emits_required_channels() -> None:
    model = MultiOutputModel(["a", "b"], ["bias", "x"], MultiOutputConfig(0.01, 0.0, 1.0))
    x = np.array([1.0, 0.5])
    y = model.predict(x)
    assert set(y.keys()) == {"a", "b"}

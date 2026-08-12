from aptf_d04.envelope.aperture_model import ApertureModelV0
from aptf_d04.models.enums import EnvelopeState


def test_aperture_range() -> None:
    model = ApertureModelV0(alpha=0.5)
    prior = 0.0
    for score in [0.0, 0.2, 0.5, 0.9, 1.0]:
        prior = model.update(score, EnvelopeState.CLOSED, prior)
        assert 0.0 <= prior <= 1.0

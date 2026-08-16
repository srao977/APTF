import math

from aptf_d01.volume.relative_volume import RelativeVolumeEstimator
from aptf_d01.volume.volume_density import volume_density
from aptf_d01.volume.volume_direction import directional_volume
from aptf_d01.volume.volume_movement import volume_movement_abs, volume_movement_signed


def test_relative_log_volume_density_direction_interactions() -> None:
    rv = RelativeVolumeEstimator(method="rolling_mean", window=3)
    rv.update(1.0, 100.0)
    rel, vlog = rv.update(2.0, 200.0)
    assert rel > 0.0
    assert abs(vlog - math.log1p(rel)) < 1e-12

    rho = volume_density(300.0, 3.0)
    assert abs(rho - 100.0) < 1e-9
    assert directional_volume(0.1, 0.7) > 0
    assert directional_volume(-0.1, 0.7) < 0
    assert volume_movement_abs(2.0, -0.1) == 0.2
    assert volume_movement_signed(2.0, -0.1) == -0.2

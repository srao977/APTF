from __future__ import annotations


def effective_mass_m0(volume_log: float) -> float:
    return max(0.0, volume_log)


def effective_mass_m1(relative_volume: float, volume_density: float, directional_coherence: float) -> float:
    density_component = min(1.0, volume_density / 5000.0)
    return max(0.0, 0.5 * relative_volume + 0.35 * density_component + 0.15 * abs(directional_coherence))

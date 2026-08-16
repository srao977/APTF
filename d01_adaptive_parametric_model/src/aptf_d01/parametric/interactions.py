from __future__ import annotations


def add_allowed_interactions(features: dict[str, float], allowlist: list[str], require_parent_presence: bool = False) -> dict[str, float]:
    out = dict(features)

    def get(name: str) -> float:
        return float(features.get(name, 0.0))

    def available(*parents: str) -> bool:
        if not require_parent_presence:
            return True
        return all(p in features for p in parents)

    if "volume_log_x_price_displacement" in allowlist and available("volume_log", "price_displacement"):
        out["volume_log_x_price_displacement"] = get("volume_log") * get("price_displacement")
    if "relative_volume_x_price_velocity" in allowlist and available("relative_volume", "price_velocity"):
        out["relative_volume_x_price_velocity"] = get("relative_volume") * get("price_velocity")
    if "volume_density_x_price_displacement" in allowlist and available("volume_density", "price_displacement"):
        out["volume_density_x_price_displacement"] = get("volume_density") * get("price_displacement")
    if "price_velocity_x_acceleration" in allowlist and available("price_velocity", "price_acceleration"):
        out["price_velocity_x_acceleration"] = get("price_velocity") * get("price_acceleration")
    return out

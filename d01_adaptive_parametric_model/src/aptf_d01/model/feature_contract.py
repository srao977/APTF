from __future__ import annotations

from dataclasses import dataclass

from aptf_d01.providers.observation_capabilities import ObservationCapabilities


@dataclass(frozen=True)
class BaseFeatureSpec:
    name: str
    requires: tuple[str, ...]
    feature_type: str


@dataclass(frozen=True)
class FeatureAdmissibilityDecision:
    feature_name: str
    active: bool
    reason: str
    requires: tuple[str, ...]
    feature_type: str


@dataclass(frozen=True)
class ActiveChannelMap:
    provider: str
    entity: str
    available_observations: tuple[str, ...]
    unavailable_observations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "entity": self.entity,
            "available_observations": list(self.available_observations),
            "unavailable_observations": list(self.unavailable_observations),
        }


BASE_FEATURE_SPECS: tuple[BaseFeatureSpec, ...] = (
    BaseFeatureSpec("price_displacement", ("close",), "price"),
    BaseFeatureSpec("price_velocity", ("close",), "price"),
    BaseFeatureSpec("price_acceleration", ("close",), "price"),
    BaseFeatureSpec("spread", ("bid", "ask"), "quote"),
    BaseFeatureSpec("spread_change", ("bid", "ask"), "quote"),
    BaseFeatureSpec("relative_volume", ("volume",), "volume"),
    BaseFeatureSpec("volume_log", ("volume",), "volume"),
    BaseFeatureSpec("volume_density", ("volume",), "volume"),
    BaseFeatureSpec("directional_volume", ("volume", "close"), "volume"),
    BaseFeatureSpec("volume_movement_abs", ("volume", "close"), "volume"),
    BaseFeatureSpec("volume_movement_signed", ("volume", "close"), "volume"),
)


def build_active_channel_map(capabilities: ObservationCapabilities) -> ActiveChannelMap:
    available: list[str] = []
    unavailable: list[str] = []

    mapping = {
        "open": capabilities.has_open,
        "high": capabilities.has_high,
        "low": capabilities.has_low,
        "close": capabilities.has_close,
        "price": capabilities.has_price,
        "volume": capabilities.has_volume,
        "trade_size": capabilities.has_trade_size,
        "bid": capabilities.has_bid,
        "ask": capabilities.has_ask,
        "bid_size": capabilities.has_bid_size,
        "ask_size": capabilities.has_ask_size,
        "quote_spread": capabilities.has_quote_spread,
        "order_book": capabilities.has_order_book,
    }
    for key, flag in mapping.items():
        if flag:
            available.append(key)
        else:
            unavailable.append(key)

    return ActiveChannelMap(
        provider=capabilities.provider,
        entity=capabilities.entity,
        available_observations=tuple(sorted(available)),
        unavailable_observations=tuple(sorted(unavailable)),
    )


def derive_admissible_base_features(
    capabilities: ObservationCapabilities,
    include_volume: bool,
) -> tuple[list[str], list[FeatureAdmissibilityDecision]]:
    channel_map = build_active_channel_map(capabilities)
    available = set(channel_map.available_observations)

    active: list[str] = []
    decisions: list[FeatureAdmissibilityDecision] = []
    for spec in BASE_FEATURE_SPECS:
        if spec.feature_type == "volume" and not include_volume:
            decisions.append(
                FeatureAdmissibilityDecision(
                    feature_name=spec.name,
                    active=False,
                    reason="INCLUDE_VOLUME_DISABLED",
                    requires=spec.requires,
                    feature_type=spec.feature_type,
                )
            )
            continue

        missing = [r for r in spec.requires if r not in available]
        if missing:
            decisions.append(
                FeatureAdmissibilityDecision(
                    feature_name=spec.name,
                    active=False,
                    reason=f"MISSING_REQUIRED_CHANNELS:{','.join(sorted(missing))}",
                    requires=spec.requires,
                    feature_type=spec.feature_type,
                )
            )
            continue

        active.append(spec.name)
        decisions.append(
            FeatureAdmissibilityDecision(
                feature_name=spec.name,
                active=True,
                reason="ACTIVE",
                requires=spec.requires,
                feature_type=spec.feature_type,
            )
        )

    return active, decisions
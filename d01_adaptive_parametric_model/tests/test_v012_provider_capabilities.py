from __future__ import annotations

from aptf_d01.providers.observation_capabilities import ObservationCapabilities, firstrate_ohlcv_capabilities
from aptf_d01.model.feature_contract import build_active_channel_map


def test_firstrate_profile_ohlcv_only() -> None:
    caps = firstrate_ohlcv_capabilities("SPY")
    m = build_active_channel_map(caps)
    assert "close" in m.available_observations
    assert "volume" in m.available_observations
    assert "bid" in m.unavailable_observations
    assert "ask" in m.unavailable_observations
    assert "trade_size" in m.unavailable_observations


def test_provider_neutral_mapping_roundtrip() -> None:
    caps = ObservationCapabilities(provider="X", entity="Y", has_bid=False, has_ask=False)
    d = caps.to_dict()
    assert d["provider"] == "X"
    assert d["entity"] == "Y"
    assert d["has_bid"] is False
    assert d["has_ask"] is False

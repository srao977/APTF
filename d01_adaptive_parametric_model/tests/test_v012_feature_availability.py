from __future__ import annotations

from pathlib import Path

from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.models.normalized_observation import NormalizedObservation
from aptf_d01.providers.observation_capabilities import ObservationCapabilities
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml


def _cfg_with_caps(caps: ObservationCapabilities, include_volume: bool = True):
    root = Path(__file__).resolve().parents[1]
    default_cfg = _load_yaml(root / "config" / "default_v0_1_1.yaml")
    default_cfg["observation_capabilities"] = caps.to_dict()
    exp_cfg = {
        "id": "TEST",
        "variant": "A",
        "polynomial_order": 2,
        "include_volume": include_volume,
        "include_volume_interactions": True,
        "adaptive_half_life": True,
        "perturbation_responsive_half_life": True,
    }
    return _build_model_cfg(default_cfg, exp_cfg)


def _obs(i: int, bid=None, ask=None):
    t = float(i + 1)
    return NormalizedObservation(
        entity_id="SPY",
        event_id=f"EV-{i}",
        source_id="unit",
        source_sequence=i,
        exchange_timestamp=t,
        receive_timestamp=t,
        model_available_timestamp=t,
        price=100.0 + i,
        trade_size=None,
        volume=1000.0 + i,
        bid=bid,
        ask=ask,
        bid_size=None,
        ask_size=None,
        contextual={},
        channel_availability={},
        metadata={},
        data_valid=True,
    )


def test_case_a_ohlcv_only_quote_features_absent() -> None:
    caps = ObservationCapabilities(
        provider="FirstRateData",
        entity="SPY",
        has_bid=False,
        has_ask=False,
        has_bid_size=False,
        has_ask_size=False,
        has_trade_size=False,
    )
    model = AdaptiveParametricModel(_cfg_with_caps(caps))

    assert "spread" not in model.base_feature_names
    assert "spread_change" not in model.base_feature_names
    assert "relative_volume" in model.base_feature_names
    assert not any("spread" in f for f in model.feature_names)
    assert model.inactive_base_feature_reasons["spread"].startswith("MISSING_REQUIRED_CHANNELS")


def test_case_b_with_bid_ask_spread_available_no_quote_imbalance_feature() -> None:
    caps = ObservationCapabilities(
        provider="Synthetic",
        entity="SPY",
        has_bid=True,
        has_ask=True,
        has_bid_size=False,
        has_ask_size=False,
        has_trade_size=False,
    )
    model = AdaptiveParametricModel(_cfg_with_caps(caps))

    assert "spread" in model.base_feature_names
    assert "spread_change" in model.base_feature_names
    assert "quote_imbalance" not in model.base_feature_names


def test_case_c_with_sizes_still_deterministic_lineage() -> None:
    caps = ObservationCapabilities(
        provider="Synthetic",
        entity="SPY",
        has_bid=True,
        has_ask=True,
        has_bid_size=True,
        has_ask_size=True,
        has_trade_size=False,
    )
    m1 = AdaptiveParametricModel(_cfg_with_caps(caps))
    m2 = AdaptiveParametricModel(_cfg_with_caps(caps))
    assert m1.base_feature_names == m2.base_feature_names
    assert m1.feature_names == m2.feature_names
    assert m1.get_feature_manifest()["feature_lineage"] == m2.get_feature_manifest()["feature_lineage"]


def test_case_d_full_source_and_intercept_policy() -> None:
    caps = ObservationCapabilities(provider="Synthetic", entity="SPY")
    model = AdaptiveParametricModel(_cfg_with_caps(caps))

    assert model.feature_names.count("bias") == 1
    assert model.intercept_collision_count == 0
    assert "volume_log" in model.base_feature_names


def test_unavailable_not_zero_no_raw_spread_snapshot_key() -> None:
    caps = ObservationCapabilities(
        provider="FirstRateData",
        entity="SPY",
        has_bid=False,
        has_ask=False,
        has_bid_size=False,
        has_ask_size=False,
        has_trade_size=False,
    )
    model = AdaptiveParametricModel(_cfg_with_caps(caps))

    model.step(_obs(0), 1.0)
    dmo, _fmo, _upd = model.step(_obs(1), 2.0)

    assert "raw_spread" not in dmo.input_channel_snapshot
    assert "model_spread" not in dmo.input_channel_snapshot


def test_polynomial_and_interactions_from_active_features_only() -> None:
    caps = ObservationCapabilities(
        provider="FirstRateData",
        entity="SPY",
        has_bid=False,
        has_ask=False,
        has_bid_size=False,
        has_ask_size=False,
        has_trade_size=False,
    )
    model = AdaptiveParametricModel(_cfg_with_caps(caps))

    active = set(model.base_feature_names)
    for name in model.feature_names:
        if name == "bias":
            continue
        base = name.split("^")[0]
        parts = base.split("_x_")
        assert all((p in active) or (f"price_{p}" in active) for p in parts)

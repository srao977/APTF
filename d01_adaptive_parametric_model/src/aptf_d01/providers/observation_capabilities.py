from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservationCapabilities:
    provider: str = "UNKNOWN"
    entity: str = "UNKNOWN"

    has_price: bool = True
    has_open: bool = True
    has_high: bool = True
    has_low: bool = True
    has_close: bool = True
    has_volume: bool = True

    has_bid: bool = True
    has_ask: bool = True
    has_bid_size: bool = True
    has_ask_size: bool = True
    has_trade_size: bool = True

    has_quote_spread: bool = False
    has_order_book: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "entity": self.entity,
            "has_price": self.has_price,
            "has_open": self.has_open,
            "has_high": self.has_high,
            "has_low": self.has_low,
            "has_close": self.has_close,
            "has_volume": self.has_volume,
            "has_bid": self.has_bid,
            "has_ask": self.has_ask,
            "has_bid_size": self.has_bid_size,
            "has_ask_size": self.has_ask_size,
            "has_trade_size": self.has_trade_size,
            "has_quote_spread": self.has_quote_spread,
            "has_order_book": self.has_order_book,
        }


def from_mapping(mapping: dict[str, object] | None) -> ObservationCapabilities | None:
    if mapping is None:
        return None
    return ObservationCapabilities(
        provider=str(mapping.get("provider", "UNKNOWN")),
        entity=str(mapping.get("entity", "UNKNOWN")),
        has_price=bool(mapping.get("has_price", True)),
        has_open=bool(mapping.get("has_open", True)),
        has_high=bool(mapping.get("has_high", True)),
        has_low=bool(mapping.get("has_low", True)),
        has_close=bool(mapping.get("has_close", True)),
        has_volume=bool(mapping.get("has_volume", True)),
        has_bid=bool(mapping.get("has_bid", True)),
        has_ask=bool(mapping.get("has_ask", True)),
        has_bid_size=bool(mapping.get("has_bid_size", True)),
        has_ask_size=bool(mapping.get("has_ask_size", True)),
        has_trade_size=bool(mapping.get("has_trade_size", True)),
        has_quote_spread=bool(mapping.get("has_quote_spread", False)),
        has_order_book=bool(mapping.get("has_order_book", False)),
    )


def firstrate_ohlcv_capabilities(entity: str = "SPY") -> ObservationCapabilities:
    return ObservationCapabilities(
        provider="FirstRateData",
        entity=entity,
        has_price=True,
        has_open=True,
        has_high=True,
        has_low=True,
        has_close=True,
        has_volume=True,
        has_bid=False,
        has_ask=False,
        has_bid_size=False,
        has_ask_size=False,
        has_trade_size=False,
        has_quote_spread=False,
        has_order_book=False,
    )

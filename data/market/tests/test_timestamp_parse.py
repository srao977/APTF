from datetime import datetime

from data.market.prepare_spy_firstratedata import parse_source_timestamp


def test_parse_timestamp_standard_format() -> None:
    dt = parse_source_timestamp("2022-09-30 04:00:00")
    assert isinstance(dt, datetime)
    assert dt.year == 2022
    assert dt.month == 9
    assert dt.day == 30
    assert dt.hour == 4
    assert dt.minute == 0


def test_parse_timestamp_invalid_returns_none() -> None:
    assert parse_source_timestamp("not-a-time") is None

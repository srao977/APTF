from datetime import UTC

from data.market.prepare_spy_firstratedata import NY_TZ


def test_timezone_conversion_dst_aware() -> None:
    local_dt = __import__("datetime").datetime(2022, 11, 7, 9, 30, 0, tzinfo=NY_TZ)
    utc_dt = local_dt.astimezone(UTC)
    assert utc_dt.hour in (13, 14)


def test_timezone_conversion_has_tzinfo() -> None:
    local_dt = __import__("datetime").datetime(2023, 3, 1, 10, 0, 0, tzinfo=NY_TZ)
    assert local_dt.tzinfo is not None

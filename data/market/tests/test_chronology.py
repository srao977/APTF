from data.market.prepare_spy_firstratedata import detect_chronology


def test_detect_chronology_ascending() -> None:
    ts = ["2023-01-01 09:30:00", "2023-01-01 09:31:00", "2023-01-01 09:32:00"]
    assert detect_chronology(ts) == "ASCENDING"


def test_detect_chronology_mixed() -> None:
    ts = ["2023-01-01 09:31:00", "2023-01-01 09:30:00", "2023-01-01 09:32:00"]
    assert detect_chronology(ts) == "MIXED"
